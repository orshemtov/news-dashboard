import asyncio
from functools import partial

from loguru import logger
from sentence_transformers import SentenceTransformer

from app.config import Settings, get_settings


class EmbeddingService:
    """Generates text embeddings via local sentence-transformers."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        """Lazy-load the sentence-transformers model on first use."""
        if self._model is None:
            logger.info("Loading local embedding model: {}", self._settings.embedding_model)
            self._model = SentenceTransformer(self._settings.embedding_model)
        return self._model

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text string."""
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []

        model = self._get_model()
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(
            None,
            partial(model.encode, texts, show_progress_bar=False),
        )
        return [vec.tolist() for vec in embeddings]
