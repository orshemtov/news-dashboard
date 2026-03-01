import hashlib
import re
from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import async_session_factory
from app.ingestors import RawArticle, TelegramIngestor
from app.ingestors.base import BaseIngestor
from app.models import Article, Source
from app.services.embedding import EmbeddingService
from app.services.events import NewArticlesEvent, article_to_sse_dict

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
# Telegram cursor helpers
# ------------------------------------------------------------------

_TG_EXTERNAL_ID_RE = re.compile(r"^tg-[^-]+-(\d+)$")


async def _get_max_telegram_msg_id(db: AsyncSession, source: Source) -> int:
    """Return the highest Telegram message ID already ingested for *source*.

    The external_id for Telegram articles follows the pattern
    ``tg-{channel}-{msg_id}``. We extract the numeric suffix and return
    the maximum, or 0 if no articles exist yet.
    """
    result = await db.execute(
        select(Article.external_id)
        .where(Article.source_id == source.id)
        .where(Article.source_type == "telegram")
        .order_by(Article.published_at.desc())
        .limit(1)
    )
    latest_ext_id = result.scalar_one_or_none()
    if latest_ext_id is None:
        return 0

    m = _TG_EXTERNAL_ID_RE.match(latest_ext_id)
    return int(m.group(1)) if m else 0


# ------------------------------------------------------------------
# Ingestor factory
# ------------------------------------------------------------------


async def _build_ingestor(source: Source, db: AsyncSession) -> BaseIngestor:
    """Instantiate the correct ingestor for *source*."""
    config: dict = source.config or {}

    if source.source_type == "telegram":
        from app.services.telegram_client import get_telegram_client

        client = await get_telegram_client()

        # Find the highest Telegram message ID we already have for this source
        # so we only fetch newer messages.
        min_id = await _get_max_telegram_msg_id(db, source)

        return TelegramIngestor(
            source_name=source.name,
            config=config,
            client=client,
            min_id=min_id,
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
        media_attachments=raw.media_attachments,
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
) -> tuple[int, NewArticlesEvent | None]:
    """Ingest articles from a single *source*.

    Returns a ``(new_count, pending_event)`` tuple.  The caller is
    responsible for publishing *pending_event* via the event bus **after**
    the database transaction has been committed so that SSE clients never
    receive phantom articles.

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

    ingestor = await _build_ingestor(source, db)

    try:
        raw_articles = await ingestor.fetch()
    except Exception as exc:
        logger.exception("Ingestion failed for source {}", source.name)
        source.error_message = str(exc)
        source.last_polled_at = datetime.now(tz=UTC)
        await db.flush()
        return 0, None

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

            # Semantic dedup: check each new article against existing articles
            from app.services.dedup import DedupService

            dedup_svc = DedupService(db)
            dedup_count = 0
            for article in new_articles:
                if article.embedding is None:
                    continue
                similar = await dedup_svc.check_semantic_duplicate(article.embedding)
                if similar is not None:
                    article.is_duplicate = True
                    article.dedup_cluster_id = await dedup_svc.find_or_create_cluster(similar)
                    dedup_count += 1
            if dedup_count:
                logger.info(
                    "Source {}: marked {} articles as semantic duplicates",
                    source.name,
                    dedup_count,
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

    # Build the SSE event but do NOT publish yet – the caller must
    # publish after the DB transaction commits.
    pending_event: NewArticlesEvent | None = None
    if new_articles:
        pending_event = NewArticlesEvent(
            source_name=source.name,
            count=new_count,
            articles=[article_to_sse_dict(a) for a in new_articles],
        )

    return new_count, pending_event


async def ingest_all_sources() -> tuple[dict[str, int], list[NewArticlesEvent]]:
    """Fetch all enabled sources and ingest each one.

    Each source is ingested in its **own** database transaction so that a
    failure in one source does not poison the others.

    Only sources whose ``poll_interval_seconds`` has elapsed since
    ``last_polled_at`` are included. This respects per-source polling
    frequency instead of blindly polling everything on every cycle.

    Returns ``(summary, pending_events)`` where *summary* maps source
    names to new-article counts and *pending_events* should be published
    **after** the database transactions have committed.
    """
    now = datetime.now(tz=UTC)

    # Read the list of sources in a short-lived read-only session.
    async with async_session_factory() as db:
        result = await db.execute(select(Source).where(Source.enabled.is_(True)))
        sources = list(result.scalars().all())

        if not sources:
            logger.info("No enabled sources found — nothing to ingest.")
            return {}, []

        # Filter to sources that are due for a poll.  Capture lightweight
        # identifiers so we can open independent sessions below.
        due_sources: list[tuple[str, str]] = []  # (source_id_hex, source_name)
        for source in sources:
            if source.last_polled_at is None:
                due_sources.append((str(source.id), source.name))
                continue
            elapsed = (now - source.last_polled_at).total_seconds()
            if elapsed >= source.poll_interval_seconds:
                due_sources.append((str(source.id), source.name))
            else:
                logger.debug(
                    "Source {}: skipping, polled {:.0f}s ago (interval={}s)",
                    source.name,
                    elapsed,
                    source.poll_interval_seconds,
                )

    if not due_sources:
        logger.debug("No sources due for polling this cycle.")
        return {}, []

    summary: dict[str, int] = {}
    pending_events: list[NewArticlesEvent] = []

    for source_id, source_name in due_sources:
        try:
            async with async_session_factory() as db, db.begin():
                source = await db.get(Source, source_id)
                if source is None:
                    logger.warning("Source {} disappeared, skipping", source_name)
                    continue
                count, event = await ingest_source(source, db)
            # Transaction committed — safe to collect the event.
            summary[source_name] = count
            if event is not None:
                pending_events.append(event)
        except Exception:
            logger.exception("Unexpected error ingesting source {}", source_name)
            summary[source_name] = 0

    return summary, pending_events
