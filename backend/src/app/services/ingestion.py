import hashlib
from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.ingestors import RawArticle, TelegramIngestor
from app.ingestors.base import BaseIngestor
from app.models import Article, Source
from app.services.embedding import EmbeddingService

# ------------------------------------------------------------------
# Module-level embedding service (lazy singleton)
# ------------------------------------------------------------------
_embedding_service: EmbeddingService | None = None


def _get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


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


async def _build_ingestor(source: Source) -> BaseIngestor:
    """Instantiate the correct ingestor for *source*."""
    config: dict = source.config or {}

    if source.source_type == "telegram":
        from app.services.telegram_client import get_telegram_client

        client = await get_telegram_client()
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


async def ingest_source(
    source: Source,
    db: AsyncSession,
    *,
    backfill_hours: int | None = None,
    generate_embeddings: bool = True,
) -> int:
    """Ingest articles from a single *source*. Returns the number of new
    articles stored.

    Parameters
    ----------
    backfill_hours:
        If set, articles older than this many hours are discarded.
        Defaults to the ``initial_backfill_hours`` setting.
    generate_embeddings:
        Whether to generate vector embeddings for each article.
    """
    settings = get_settings()
    if backfill_hours is None:
        backfill_hours = settings.initial_backfill_hours

    ingestor = await _build_ingestor(source)

    try:
        raw_articles = await ingestor.fetch()
    except Exception as exc:
        logger.exception("Ingestion failed for source {}", source.name)
        source.error_message = str(exc)
        source.last_polled_at = datetime.now(tz=UTC)
        await db.flush()
        return 0

    # Filter by backfill window
    cutoff = datetime.now(tz=UTC) - timedelta(hours=backfill_hours)
    filtered: list[RawArticle] = []
    for raw in raw_articles:
        pub = raw.published_at
        # Make naive datetimes UTC-aware for comparison
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=UTC)
        if pub >= cutoff:
            filtered.append(raw)

    if len(filtered) < len(raw_articles):
        logger.info(
            "Source {}: filtered {} -> {} articles (backfill window: {}h)",
            source.name,
            len(raw_articles),
            len(filtered),
            backfill_hours,
        )

    new_count = 0
    new_articles: list[Article] = []
    for raw in filtered:
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
        new_articles.append(article)
        new_count += 1

    # Generate embeddings in batch for new articles
    if generate_embeddings and new_articles:
        try:
            emb_service = _get_embedding_service()
            texts = [f"{a.title or ''}\n{a.content[:1000]}" for a in new_articles]
            embeddings = await emb_service.embed_batch(texts)
            for article, emb in zip(new_articles, embeddings, strict=True):
                article.embedding = emb
            logger.info(
                "Source {}: generated {} embeddings",
                source.name,
                len(embeddings),
            )
        except Exception:
            logger.warning(
                "Source {}: embedding generation failed, articles stored without embeddings",
                source.name,
            )

    # Update source bookkeeping
    source.last_polled_at = datetime.now(tz=UTC)
    source.article_count = (source.article_count or 0) + new_count
    source.error_message = None
    await db.flush()

    logger.info(
        "Source {}: stored {} new articles ({} fetched, {} after backfill filter)",
        source.name,
        new_count,
        len(raw_articles),
        len(filtered),
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
