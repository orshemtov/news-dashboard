from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.services.events import BurstEvent, article_to_sse_dict


class BurstDetector:
    """
    Detects 'breaking news bursts' by monitoring semantic clusters.
    A burst is defined as 3+ different sources reporting on the same event
    (same cluster_id) within a 5-minute window.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def check_for_burst(self, cluster_id: UUID) -> BurstEvent | None:
        """
        Check if the given cluster_id has reached the 'burst' threshold.
        Returns a BurstEvent if a new burst is detected, otherwise None.
        """
        # 1. Count unique sources in this cluster within the last 5 minutes
        query = text("""
            SELECT 
                COUNT(DISTINCT source_id) as source_count,
                ARRAY_AGG(DISTINCT source_name) as source_names
            FROM articles
            WHERE dedup_cluster_id = :cluster_id
              AND published_at > now() - interval '5 minutes'
        """)

        result = await self.db.execute(query, {"cluster_id": cluster_id})
        row = result.fetchone()

        if not row or row.source_count < 3:
            return None

        # 2. Get the lead article for this cluster
        stmt = (
            select(Article)
            .where(Article.dedup_cluster_id == cluster_id)
            .order_by(Article.is_duplicate.asc(), Article.published_at.desc())
            .limit(1)
        )
        lead_result = await self.db.execute(stmt)
        lead_article = lead_result.scalar_one_or_none()

        if not lead_article:
            return None

        logger.info(
            "BURST DETECTED: Cluster {} reached {} sources: {}",
            cluster_id,
            row.source_count,
            row.source_names,
        )

        return BurstEvent(
            cluster_id=str(cluster_id),
            lead_article=article_to_sse_dict(lead_article),
            sources=list(row.source_names),
            count=int(row.source_count),
        )
