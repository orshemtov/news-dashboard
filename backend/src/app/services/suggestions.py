"""Channel suggestion engine.

Computes an interest-profile embedding from the user's recent articles,
then ranks the curated channel catalog by cosine similarity to suggest
channels the user might want to add.
"""

from __future__ import annotations

import numpy as np
from loguru import logger
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.services.channel_catalog import CatalogChannel, CHANNEL_CATALOG, get_catalog_excluding
from app.services.embedding import EmbeddingService

# Module-level singleton so the transformer model is not reloaded on every request
_embedding_service: EmbeddingService | None = None


def _get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def _compute_interest_vector(
    db: AsyncSession,
    limit: int = 500,
) -> np.ndarray | None:
    """Compute a mean embedding from the user's most recent articles.

    Returns None if there are no articles with embeddings.
    """
    # Fetch the most recent article embeddings
    result = await db.execute(
        select(Article.embedding)
        .where(Article.embedding.isnot(None))
        .order_by(Article.published_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()

    if not rows:
        logger.debug("No article embeddings found for interest vector")
        return None

    vectors = np.array([list(row) for row in rows], dtype=np.float32)
    mean_vec = vectors.mean(axis=0)

    # Normalize to unit vector for cosine similarity
    norm = np.linalg.norm(mean_vec)
    if norm > 0:
        mean_vec = mean_vec / norm

    logger.debug(
        "Computed interest vector from {} article embeddings",
        len(rows),
    )
    return mean_vec


async def get_channel_suggestions(
    db: AsyncSession,
    top_k: int = 20,
) -> list[dict]:
    """Suggest channels from the catalog ranked by interest similarity.

    Steps:
    1. Get existing source usernames to exclude already-added channels.
    2. Compute a mean embedding (interest vector) from recent articles.
    3. Embed each catalog channel's description.
    4. Rank by cosine similarity to the interest vector.
    5. Return top-k suggestions.

    If no article embeddings exist, returns catalog channels in default
    order (still useful for cold-start / new users).
    """
    from app.models.source import Source

    # 1. Get existing source usernames
    result = await db.execute(select(Source.config))
    configs = result.scalars().all()
    existing_usernames: set[str] = set()
    for cfg in configs:
        if isinstance(cfg, dict) and "channel" in cfg:
            existing_usernames.add(str(cfg["channel"]))

    # Filter catalog
    candidates = get_catalog_excluding(existing_usernames)
    if not candidates:
        return []

    # 2. Compute interest vector
    interest_vec = await _compute_interest_vector(db)

    # 3. Embed catalog descriptions (reuse singleton to avoid reloading the model)
    embedding_service = _get_embedding_service()
    descriptions = [ch.description for ch in candidates]
    catalog_embeddings = await embedding_service.embed_batch(descriptions)

    if interest_vec is None:
        # Cold start — return channels in catalog order without scores
        logger.info("No interest vector available, returning catalog in default order")
        return [_channel_to_dict(ch, score=None) for ch in candidates[:top_k]]

    # 4. Rank by cosine similarity
    catalog_matrix = np.array(catalog_embeddings, dtype=np.float32)

    # Normalize catalog vectors
    norms = np.linalg.norm(catalog_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid division by zero
    catalog_matrix = catalog_matrix / norms

    # Cosine similarity = dot product (both are unit vectors)
    similarities = catalog_matrix @ interest_vec

    # 5. Sort and return top-k
    ranked_indices = np.argsort(similarities)[::-1][:top_k]

    suggestions = []
    for idx in ranked_indices:
        ch = candidates[idx]
        score = float(similarities[idx])
        suggestions.append(_channel_to_dict(ch, score=score))

    logger.info(
        "Generated {} channel suggestions (top score: {:.3f})",
        len(suggestions),
        suggestions[0]["similarity_score"] if suggestions else 0,
    )
    return suggestions


def _channel_to_dict(ch: CatalogChannel, score: float | None) -> dict:
    return {
        "username": ch.username,
        "name": ch.name,
        "description": ch.description,
        "language": ch.language,
        "tags": ch.tags,
        "similarity_score": score,
    }
