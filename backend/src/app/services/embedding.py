import asyncio
from functools import partial

import httpx
from loguru import logger
from sentence_transformers import SentenceTransformer

from app.config import Settings, get_settings


class EmbeddingService:
    """Generates text embeddings via local sentence-transformers or OpenAI."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._local_model: SentenceTransformer | None = None

    # ------------------------------------------------------------------
    # Local model (lazy-loaded)
    # ------------------------------------------------------------------

    def _get_local_model(self) -> SentenceTransformer:
        """Lazy-load the sentence-transformers model on first use."""
        if self._local_model is None:
            logger.info("Loading local embedding model: {}", self._settings.embedding_model)
            self._local_model = SentenceTransformer(self._settings.embedding_model)
        return self._local_model

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _embed_local(self, texts: list[str]) -> list[list[float]]:
        """Run the synchronous sentence-transformers encoder in a thread."""
        model = self._get_local_model()
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(
            None,
            partial(model.encode, texts, show_progress_bar=False),
        )
        return [vec.tolist() for vec in embeddings]

    async def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        """Call the OpenAI embeddings API via httpx."""
        api_key = self._settings.openai_api_key
        if not api_key:
            raise ValueError("openai_api_key is required when embedding_provider is 'openai'")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._settings.openai_embedding_model,
                    "input": texts,
                },
            )
            response.raise_for_status()
            data = response.json()

        # API returns embeddings sorted by index
        sorted_items = sorted(data["data"], key=lambda d: d["index"])
        return [item["embedding"] for item in sorted_items]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text string."""
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []

        if self._settings.embedding_provider == "openai":
            return await self._embed_openai(texts)
        return await self._embed_local(texts)
