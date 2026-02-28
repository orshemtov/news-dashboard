import hashlib
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.ingestors import RawArticle, RSSIngestor, TelegramIngestor
from app.ingestors.base import BaseIngestor
from app.models import Article, Source

# ------------------------------------------------------------------
# Dedup
# ------------------------------------------------------------------


def _compute_dedup_hash(content: str) -> str:
    """SHA-256 hash of normalised (lowercased, stripped) content."""
    normalized = content.lower().strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------
# Ingestor factory
# ------------------------------------------------------------------


def _build_ingestor(source: Source) -> BaseIngestor:
    """Instantiate the correct ingestor for *source*."""
    config: dict = source.config or {}

    if source.source_type == "rss":
        return RSSIngestor(source_name=source.name, config=config)

    if source.source_type == "telegram":
        from telethon import TelegramClient

        settings = get_settings()
        if not settings.telegram_api_id or not settings.telegram_api_hash:
            raise ValueError(
                "Telegram API credentials (telegram_api_id, telegram_api_hash) are not configured."
            )

        client = TelegramClient(
            settings.telegram_session_name,
            settings.telegram_api_id,
            settings.telegram_api_hash,
        )
        return TelegramIngestor(
            source_name=source.name,
            config=config,
            client=client,
        )

    raise ValueError(f"Unknown source type: {source.source_type!r}")


# ------------------------------------------------------------------
# Persistence helpers
# ------------------------------------------------------------------


async def _dedup_hash_exists(db: AsyncSession, dedup_hash: str) -> bool:
    result = await db.execute(select(Article.id).where(Article.dedup_hash == dedup_hash).limit(1))
    return result.scalar_one_or_none() is not None


def _raw_to_article(raw: RawArticle, source: Source, dedup_hash: str) -> Article:
    return Article(
        external_id=raw.external_id,
        source_id=source.id,
        source_type=raw.source_type,
        source_name=raw.source_name,
        title=raw.title,
        content=raw.content,
        url=raw.url,
        author=raw.author,
        language=raw.language,
        published_at=raw.published_at,
        raw_data=raw.raw_data,
        metadata_=raw.metadata,
        dedup_hash=dedup_hash,
    )


# ------------------------------------------------------------------
# Core pipeline
# ------------------------------------------------------------------


async def ingest_source(source: Source, db: AsyncSession) -> int:
    """Ingest articles from a single *source*. Returns the number of new
    articles stored."""
    ingestor = _build_ingestor(source)

    try:
        raw_articles = await ingestor.fetch()
    except Exception as exc:
        logger.exception("Ingestion failed for source {}", source.name)
        source.error_message = str(exc)
        source.last_polled_at = datetime.now(tz=UTC)
        await db.flush()
        return 0

    new_count = 0
    for raw in raw_articles:
        dedup_hash = _compute_dedup_hash(raw.content)

        if await _dedup_hash_exists(db, dedup_hash):
            logger.debug(
                "Duplicate skipped (hash={}) for source {}",
                dedup_hash[:12],
                source.name,
            )
            continue

        article = _raw_to_article(raw, source, dedup_hash)
        db.add(article)
        new_count += 1

    # Update source bookkeeping
    source.last_polled_at = datetime.now(tz=UTC)
    source.article_count = (source.article_count or 0) + new_count
    source.error_message = None
    await db.flush()

    logger.info(
        "Source {}: stored {} new articles ({} fetched, rest deduplicated)",
        source.name,
        new_count,
        len(raw_articles),
    )
    return new_count


async def ingest_all_sources(db: AsyncSession) -> dict[str, int]:
    """Fetch all enabled sources and ingest each one.

    Returns a mapping of ``source_name -> new_article_count``.
    """
    result = await db.execute(select(Source).where(Source.enabled.is_(True)))
    sources = list(result.scalars().all())

    if not sources:
        logger.info("No enabled sources found — nothing to ingest.")
        return {}

    summary: dict[str, int] = {}
    for source in sources:
        try:
            count = await ingest_source(source, db)
        except Exception:
            logger.exception("Unexpected error ingesting source {}", source.name)
            count = 0
        summary[source.name] = count

    return summary
