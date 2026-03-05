from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.services.llm import LLMService


class ThemeService:
    """Service for identifying and summarizing trending themes/clusters."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._llm = LLMService()

    def _clean_snippet(self, text: str) -> str:
        """Normalize noisy telegram content before theme summarization."""
        cleaned = text.replace("\n", " ")
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:420]

    def _fallback_theme_summary(self, snippets: list[str], title: str | None) -> str:
        """Create a concise fallback summary when LLM is unavailable."""
        base = title or (snippets[0] if snippets else "Trending event")
        base = self._clean_snippet(base)
        if len(base) > 180:
            base = base[:177] + "..."
        return base

    async def get_trending_themes(
        self,
        window_minutes: int = 180,
        limit: int = 10,
        min_sources: int = 2,
    ) -> list[dict]:
        """
        Identify top clusters from the last X minutes and generate catchy themes.
        """
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

            # Prefer LLM event summary for themes (not raw content)
            llm_theme = await self._llm.summarize_theme(snippets)
            if llm_theme:
                display_theme = self._clean_snippet(llm_theme)
            elif lead.summary:
                display_theme = self._clean_snippet(lead.summary)
            elif lead.title:
                display_theme = self._clean_snippet(lead.title)
            else:
                display_theme = self._fallback_theme_summary(snippets, lead.title)

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
        return [
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
