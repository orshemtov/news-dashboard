import asyncio
from functools import partial

from loguru import logger
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from app.config import Settings, get_settings


class EmbeddingService:
    """Generates text embeddings via local sentence-transformers or OpenAI."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._local_model: SentenceTransformer | None = None
        self._openai_client: AsyncOpenAI | None = None

    # ------------------------------------------------------------------
    # Local model (lazy-loaded)
    # ------------------------------------------------------------------

    def _get_local_model(self) -> SentenceTransformer:
        """Lazy-load the sentence-transformers model on first use."""
        if self._local_model is None:
            logger.info("Loading local embedding model: {}", self._settings.embedding_model)
            self._local_model = SentenceTransformer(self._settings.embedding_model)
        return self._local_model

    def _get_openai_client(self) -> AsyncOpenAI:
        """Lazy-load the OpenAI async client."""
        if self._openai_client is None:
            api_key = self._settings.openai_api_key
            if not api_key:
                raise ValueError("openai_api_key is required when embedding_provider is 'openai'")
            self._openai_client = AsyncOpenAI(api_key=api_key, timeout=60.0)
        return self._openai_client

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
        """Call the OpenAI embeddings API."""
        client = self._get_openai_client()
        response = await client.embeddings.create(
            model=self._settings.openai_embedding_model,
            input=texts,
        )
        sorted_items = sorted(response.data, key=lambda d: d.index)
        return [item.embedding for item in sorted_items]

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
