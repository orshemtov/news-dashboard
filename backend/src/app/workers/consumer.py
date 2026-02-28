import asyncio
import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from loguru import logger

from app.config import get_settings
from app.db.session import async_session_factory
from app.models.article import Article
from app.services.dedup import DedupService
from app.services.embedding import EmbeddingService

TOPIC_RAW = "raw-articles"
TOPIC_ENRICHED = "enriched-articles"


# ------------------------------------------------------------------
# Processing helpers
# ------------------------------------------------------------------


def _compute_dedup_hash(data: dict[str, Any]) -> str:
    """Create a deterministic hash of the article content for exact dedup."""
    payload = (
        f"{data.get('source_type', '')}:{data.get('external_id', '')}:{data.get('content', '')}"
    )
    return hashlib.sha256(payload.encode()).hexdigest()


async def process_raw_article(message_data: dict[str, Any]) -> dict[str, Any] | None:
    """Process a raw article: hash, embed, dedup, and enrich.

    Returns the enriched message dict ready for the next topic, or None if
    the article is a duplicate that should be silently skipped.
    """
    settings = get_settings()
    embedding_service = EmbeddingService(settings)

    # Compute hash
    dedup_hash = _compute_dedup_hash(message_data)
    message_data["dedup_hash"] = dedup_hash

    # Generate embedding from title + content
    embed_text = f"{message_data.get('title', '')} {message_data.get('content', '')}"
    embedding = await embedding_service.embed(embed_text)
    message_data["embedding"] = embedding

    # Deduplication
    async with async_session_factory() as session:
        dedup = DedupService(session, settings)

        # Exact check
        existing = await dedup.check_exact_duplicate(dedup_hash)
        if existing is not None:
            logger.info(
                "Exact duplicate found for {}:{} — skipping",
                message_data.get("source_type"),
                message_data.get("external_id"),
            )
            return None

        # Semantic check
        similar = await dedup.check_semantic_duplicate(embedding)
        if similar is not None:
            cluster_id = await dedup.find_or_create_cluster(similar)
            message_data["is_duplicate"] = True
            message_data["dedup_cluster_id"] = str(cluster_id)
            logger.info("Semantic duplicate detected — cluster {}", cluster_id)
        else:
            message_data["is_duplicate"] = False
            message_data["dedup_cluster_id"] = None

        await session.commit()

    return message_data


async def store_article(message_data: dict[str, Any]) -> None:
    """Persist an enriched article to the database."""
    published_at = message_data.get("published_at")
    if isinstance(published_at, str):
        published_at = datetime.fromisoformat(published_at)
    if published_at is None:
        published_at = datetime.now(UTC)

    article = Article(
        external_id=message_data["external_id"],
        source_id=message_data.get("source_id"),
        source_type=message_data["source_type"],
        source_name=message_data["source_name"],
        title=message_data.get("title"),
        content=message_data["content"],
        url=message_data.get("url"),
        author=message_data.get("author"),
        language=message_data.get("language"),
        published_at=published_at,
        raw_data=message_data.get("raw_data", {}),
        metadata_=message_data.get("metadata", {}),
        embedding=message_data.get("embedding"),
        dedup_hash=message_data["dedup_hash"],
        dedup_cluster_id=message_data.get("dedup_cluster_id"),
        is_duplicate=message_data.get("is_duplicate", False),
    )

    async with async_session_factory() as session:
        session.add(article)
        await session.commit()
        logger.info("Stored article {} ({})", article.id, article.title)


# ------------------------------------------------------------------
# Main consumer loop
# ------------------------------------------------------------------


async def run_consumer() -> None:
    """Start the Kafka consumer loop.

    Reads from ``TOPIC_RAW``, processes each article (embed + dedup),
    publishes enriched results to ``TOPIC_ENRICHED``, and stores them.
    """
    settings = get_settings()

    consumer = AIOKafkaConsumer(
        TOPIC_RAW,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="news-dashboard-workers",
        value_deserializer=lambda m: json.loads(m.decode()),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, default=str).encode(),
    )

    await consumer.start()
    await producer.start()
    logger.info("Consumer started — listening on {}", TOPIC_RAW)

    try:
        async for message in consumer:
            try:
                if message.value is None:
                    continue
                enriched = await process_raw_article(message.value)
                if enriched is None:
                    continue

                # Publish to enriched topic
                await producer.send_and_wait(TOPIC_ENRICHED, value=enriched)

                # Persist to database
                await store_article(enriched)
            except Exception:
                logger.exception("Error processing message at offset {}", message.offset)
    finally:
        await consumer.stop()
        await producer.stop()
        logger.info("Consumer shut down")


if __name__ == "__main__":
    asyncio.run(run_consumer())
