import uuid

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.article import Article


class DedupService:
    """Two-tier deduplication: exact hash match + semantic similarity."""

    def __init__(self, db: AsyncSession, settings: Settings | None = None) -> None:
        self.db = db
        self._settings = settings or get_settings()

    # ------------------------------------------------------------------
    # Exact dedup
    # ------------------------------------------------------------------

    async def check_exact_duplicate(self, dedup_hash: str) -> Article | None:
        """Return an existing article with the same content hash, or None."""
        stmt = select(Article).where(Article.dedup_hash == dedup_hash).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Semantic dedup
    # ------------------------------------------------------------------

    async def check_semantic_duplicate(self, embedding: list[float]) -> Article | None:
        """Find a semantically similar article using pgvector cosine distance.

        Searches articles published within the configured dedup window and
        returns the first match whose cosine similarity exceeds the threshold.
        """
        threshold = self._settings.dedup_similarity_threshold
        window_hours = self._settings.dedup_window_hours

        query = text("""
            SELECT id
            FROM articles
            WHERE is_duplicate = false
              AND embedding IS NOT NULL
              AND published_at > now() - make_interval(hours => :window_hours)
              AND 1 - (embedding <=> cast(:target_embedding AS vector)) > :threshold
            ORDER BY embedding <=> cast(:target_embedding AS vector)
            LIMIT 1
        """)

        result = await self.db.execute(
            query,
            {
                "target_embedding": str(embedding),
                "threshold": threshold,
                "window_hours": window_hours,
            },
        )
        row = result.first()
        if row is None:
            return None

        # Load the full Article ORM object
        return await self.db.get(Article, row.id)

    # ------------------------------------------------------------------
    # Clustering
    # ------------------------------------------------------------------

    async def find_or_create_cluster(self, similar_article: Article) -> uuid.UUID:
        """Get the cluster ID from a similar article, or create a new one.

        If the similar article already belongs to a cluster, reuse that ID.
        Otherwise assign a new UUID as the cluster ID for both articles.
        """
        if similar_article.dedup_cluster_id is not None:
            return similar_article.dedup_cluster_id

        cluster_id = uuid.uuid4()
        similar_article.dedup_cluster_id = cluster_id
        self.db.add(similar_article)
        await self.db.flush()
        logger.info(
            "Created new dedup cluster {} from article {}",
            cluster_id,
            similar_article.id,
        )
        return cluster_id
