"""Backfill script to clean article content and detect language for existing articles.

Usage:
    uv run python backfill_content.py [--dry-run]

This script:
1. Cleans Telegram markdown/HTML formatting from all article content
2. Detects language (he/en) for articles with null language field
"""

import asyncio
import re
import sys
import unicodedata

from loguru import logger
from sqlalchemy import select, update

from app.config import get_settings
from app.db.session import async_session_factory
from app.models.article import Article

# ---------------------------------------------------------------------------
# Cleaning functions (same logic as telegram.py ingestor)
# ---------------------------------------------------------------------------


def _clean_telegram_content(text: str) -> str:
    """Strip Telegram markdown formatting and navigation cruft from content."""
    # Remove empty markdown links: [ ](url)
    text = re.sub(r"\[\s*\]\([^)]*\)", "", text)
    # Convert markdown links to just the text: [visible](url) -> visible
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    # Remove markdown bold: **text** -> text
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    # Remove markdown italic: __text__ -> text
    text = re.sub(r"__([^_]+)__", r"\1", text)
    # Remove single asterisk emphasis: *text* -> text
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    # Remove bare URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove common navigation emojis
    text = re.sub(r"[👈🏽👉🏽⬇️⬆️➡️⬅️🔗📢📌]+", "", text)
    # Remove Hebrew navigation prompts
    text = re.sub(r"לקריאה?\s+נוחה?\s+(במחשב|בנייד)", "", text)
    text = re.sub(r"הצטרפו\s+ל(ערוץ|קבוצה)", "", text)
    # Strip HTML tags (for articles that have HTML content)
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


_HEBREW_RE = re.compile(r"[\u0590-\u05FF]")


def _detect_language(text: str) -> str | None:
    """Simple heuristic language detection based on character ranges."""
    hebrew_count = len(_HEBREW_RE.findall(text))
    latin_count = sum(
        1 for ch in text if unicodedata.category(ch).startswith("L") and ord(ch) < 0x0590
    )
    total = hebrew_count + latin_count
    if total == 0:
        return None
    if hebrew_count / total > 0.3:
        return "he"
    if latin_count / total > 0.3:
        return "en"
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def backfill(dry_run: bool = False) -> None:
    logger.info("Starting backfill (dry_run={})", dry_run)

    async with async_session_factory() as session:
        result = await session.execute(select(Article))
        articles = result.scalars().all()

        cleaned_count = 0
        language_count = 0

        for article in articles:
            original_content = article.content
            cleaned = _clean_telegram_content(original_content)

            content_changed = cleaned != original_content
            needs_language = article.language is None

            if not content_changed and not needs_language:
                continue

            new_language = article.language
            if needs_language:
                new_language = _detect_language(cleaned)

            if dry_run:
                if content_changed:
                    logger.info(
                        "[DRY RUN] Would clean article {}: {} chars -> {} chars",
                        article.id,
                        len(original_content),
                        len(cleaned),
                    )
                    cleaned_count += 1
                if needs_language and new_language:
                    logger.info(
                        "[DRY RUN] Would set language={} for article {}",
                        new_language,
                        article.id,
                    )
                    language_count += 1
            else:
                updates: dict = {}
                if content_changed:
                    updates["content"] = cleaned
                    cleaned_count += 1
                if needs_language and new_language:
                    updates["language"] = new_language
                    language_count += 1

                if updates:
                    await session.execute(
                        update(Article).where(Article.id == article.id).values(**updates)
                    )

        if not dry_run:
            await session.commit()

        logger.info(
            "Backfill complete: {} articles cleaned, {} languages detected (of {} total)",
            cleaned_count,
            language_count,
            len(articles),
        )


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(backfill(dry_run))
