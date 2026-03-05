from __future__ import annotations

import re
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.services.llm import LLMService

# Module-level TTL cache for trending themes
_theme_cache: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL_SECONDS = 120  # 2 minutes


class ThemeService:
    """Service for identifying and summarizing trending themes/clusters."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._llm = LLMService()

    # Common Telegram noise phrases to strip (Hebrew + English)
    _NOISE_PATTERNS: list[re.Pattern[str]] = [
        re.compile(p, re.IGNORECASE)
        for p in [
            # Hebrew telegram promo / CTA
            r"לקריאת נוחה בנייד",
            r"לקריאה נוחה בנייד",
            r"לקריאת הכתבה המלאה",
            r"לכתבה המלאה",
            r"הצטרפו לערוץ",
            r"הצטרפו לקבוצה",
            r"הצטרפו אלינו",
            r"עקבו אחרינו",
            r"לפרטים נוספים",
            r"שתפו את הפוסט",
            r"📲\s*הצטרפו",
            r"👆\s*הצטרפו",
            r"⬆️\s*הצטרפו",
            r"🔴\s*",
            r"🚨\s*",
            r"⚡\s*",
            r"🔵\s*",
            r"📢\s*",
            r"🔔\s*",
            r"👇\s*",
            # English telegram promo / CTA
            r"join our channel",
            r"join our group",
            r"follow us on",
            r"subscribe to",
            r"click here",
            r"read more at",
            r"for easy reading",
            r"for comfortable reading",
            # Common telegram channel signatures
            r"@\w{4,}",  # @channel_name
            r"t\.me/\S+",  # t.me/channel links
        ]
    ]

    def _clean_snippet(self, text: str) -> str:
        """Normalize noisy telegram content before theme summarization."""
        cleaned = text.replace("\n", " ")
        # Remove URLs
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        # Remove telegram noise phrases
        for pattern in self._NOISE_PATTERNS:
            cleaned = pattern.sub("", cleaned)
        # Remove leftover emoji sequences (3+ consecutive emoji)
        cleaned = re.sub(
            r"[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0000FE00-\U0000FE0F\U0000200D]{3,}",
            " ",
            cleaned,
        )
        # Collapse whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:420]

    def _build_theme_display(self, lead: Article, snippets: list[str]) -> str:
        """Build a clean theme display string from the lead article.

        Priority: title > first sentence of content > cleaned snippet.
        No LLM involved — the local model is too weak for Hebrew text generation.
        """
        # 1. Title is usually the cleanest source
        if lead.title:
            cleaned = self._clean_snippet(lead.title)
            if len(cleaned) >= 20:
                return cleaned[:200]

        # 2. Use the lead article's existing summary (set during ingestion)
        if lead.summary:
            cleaned = self._clean_snippet(lead.summary)
            if len(cleaned) >= 20:
                return cleaned[:200]

        # 3. Extract first sentence from content
        if lead.content:
            cleaned = self._clean_snippet(lead.content)
            # Try to cut at first sentence boundary
            for sep in [".", "。", "。", "!", "?"]:
                idx = cleaned.find(sep)
                if 20 <= idx <= 200:
                    return cleaned[: idx + 1]
            # No good sentence boundary — just truncate
            if len(cleaned) > 200:
                # Try to break at a word boundary
                truncated = cleaned[:200]
                last_space = truncated.rfind(" ")
                if last_space > 100:
                    return truncated[:last_space] + "..."
                return truncated + "..."
            return cleaned

        # 4. Fallback to first available snippet
        if snippets:
            return snippets[0][:200]

        return "Trending event"

    async def get_trending_themes(
        self,
        window_minutes: int = 180,
        limit: int = 10,
        min_sources: int = 2,
    ) -> list[dict]:
        """
        Identify top clusters from the last X minutes and generate catchy themes.
        Results are cached for 2 minutes to avoid hammering the LLM.
        """
        cache_key = f"{window_minutes}:{limit}:{min_sources}"
        now_ts = time.monotonic()
        if cache_key in _theme_cache:
            cached_ts, cached_result = _theme_cache[cache_key]
            if now_ts - cached_ts < _CACHE_TTL_SECONDS:
                return cached_result

        cutoff = datetime.now(tz=UTC) - timedelta(minutes=window_minutes)
        pool_limit = max(limit * 3, 30)

        # 1. Find clusters with 2+ sources in the window
        # We group by cluster_id and count unique source_ids
        stmt = (
            select(
                Article.dedup_cluster_id,
                func.count(Article.id).label("article_count"),
                func.count(Article.source_id.distinct()).label("source_count"),
                func.max(Article.published_at).label("last_update"),
            )
            .where(Article.dedup_cluster_id.is_not(None))
            .where(Article.published_at >= cutoff)
            .group_by(Article.dedup_cluster_id)
            .having(func.count(Article.source_id.distinct()) >= min_sources)
            .order_by(
                func.count(Article.source_id.distinct()).desc(),
                func.count(Article.id).desc(),
                func.max(Article.published_at).desc(),
            )
            .limit(pool_limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        themes = []
        now = datetime.now(tz=UTC)
        for row in rows:
            # 2. Get the lead article for context
            lead_stmt = (
                select(Article)
                .where(Article.dedup_cluster_id == row.dedup_cluster_id)
                .where(Article.is_duplicate.is_(False))
                .limit(1)
            )
            lead_res = await self.db.execute(lead_stmt)
            lead = lead_res.scalar_one_or_none()

            if not lead:
                # Fallback to any article in cluster if no lead marked
                any_res = await self.db.execute(
                    select(Article)
                    .where(Article.dedup_cluster_id == row.dedup_cluster_id)
                    .limit(1)
                )
                lead = any_res.scalar_one_or_none()

            if not lead:
                continue

            snippets_result = await self.db.execute(
                select(Article.content)
                .where(Article.dedup_cluster_id == row.dedup_cluster_id)
                .order_by(Article.published_at.desc())
                .limit(4)
            )
            snippets = [self._clean_snippet(s) for s in snippets_result.scalars().all() if s]

            # Use cleaned lead content (no LLM text generation — too weak for Hebrew)
            display_theme = self._build_theme_display(lead, snippets)

            if len(display_theme) > 340:
                display_theme = display_theme[:337] + "..."

            minutes_ago = max(0, int((now - row.last_update).total_seconds() // 60))
            base_score = float(
                row.source_count * 120 + row.article_count * 8 + max(0, 180 - minutes_ago) * 0.3
            )

            themes.append(
                {
                    "id": str(row.dedup_cluster_id),
                    "theme": display_theme,
                    "article_count": row.article_count,
                    "source_count": row.source_count,
                    "last_update": row.last_update.isoformat(),
                    "lead_id": str(lead.id),
                    "minutes_ago": minutes_ago,
                    "base_score": base_score,
                }
            )

        llm_scores = await self._llm.rank_themes_by_importance(themes)
        for t in themes:
            llm_score = llm_scores.get(str(t["id"]))
            base = float(t["base_score"])
            if llm_score is None:
                t["importance_score"] = base
            else:
                # LLM score dominates, with recency/source base as tie-breaker signal
                t["importance_score"] = llm_score * 10.0 + base * 0.25

        ranked = sorted(
            themes,
            key=lambda t: (
                float(t["importance_score"]),
                float(t["base_score"]),
                t["last_update"],
            ),
            reverse=True,
        )

        trimmed = ranked[:limit]
        result = [
            {
                "id": t["id"],
                "theme": t["theme"],
                "article_count": t["article_count"],
                "source_count": t["source_count"],
                "last_update": t["last_update"],
                "lead_id": t["lead_id"],
            }
            for t in trimmed
        ]

        # Cache the result
        _theme_cache[cache_key] = (now_ts, result)
        return result
