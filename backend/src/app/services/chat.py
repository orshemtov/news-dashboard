import re
from uuid import UUID

from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.article import Article
from app.schemas.search import SearchRequest
from app.services.search import SearchService

CHAT_SYSTEM_PROMPT = """\
You are a news analyst assistant. Answer the user's questions based ONLY on \
the provided articles. Do not use prior knowledge.

When referencing an article, cite it using its number in square brackets, \
e.g. [1], [2]. You may cite multiple articles for a single claim, e.g. [1][3].

If none of the provided articles contain relevant information, say so clearly.
"""


class ChatService:
    """RAG-based chat service grounded in the article database."""

    def __init__(self, db: AsyncSession, settings: Settings | None = None) -> None:
        self.db = db
        self._settings = settings or get_settings()
        self._search = SearchService(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(
        self,
        message: str,
        conversation_id: UUID | None = None,
    ) -> tuple[str, list[UUID]]:
        """Process a user chat message.

        Returns:
            A tuple of (response_text, cited_article_ids).
        """
        # 1. Retrieve relevant articles
        search_request = SearchRequest(
            query=message,
            mode="hybrid",
            page_size=10,
            include_duplicates=False,
        )
        articles, _ = await self._search.hybrid_search(search_request)

        if not articles:
            return (
                "I couldn't find any relevant articles to answer your question.",
                [],
            )

        # 2. Build context
        context = self._build_context(articles)

        # 3. Generate response
        model = self._get_model()
        agent: Agent[None, str] = Agent(model, system_prompt=CHAT_SYSTEM_PROMPT)
        prompt = f"Articles:\n{context}\n\nUser question: {message}"
        result = await agent.run(prompt)
        response_text = result.output

        # 4. Extract cited article IDs
        cited_ids = self._extract_citations(response_text, articles)

        logger.debug("Chat response generated with {} citations", len(cited_ids))
        return response_text, cited_ids

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_model(self) -> OpenAIChatModel | str:
        if self._settings.llm_provider == "ollama":
            base_url = self._settings.ollama_base_url.rstrip("/") + "/v1"
            return OpenAIChatModel(
                model_name=self._settings.llm_model,
                provider=OllamaProvider(base_url=base_url),
            )
        return f"openai:{self._settings.openai_model}"

    def _get_model_name(self) -> str:
        if self._settings.llm_provider == "ollama":
            return f"ollama:{self._settings.llm_model}"
        return self._settings.openai_model

    @staticmethod
    def _build_context(articles: list[Article]) -> str:
        """Format retrieved articles into a numbered context block."""
        parts: list[str] = []
        for idx, article in enumerate(articles, start=1):
            snippet = (article.content or "")[:1500]
            date_str = (
                article.published_at.strftime("%Y-%m-%d %H:%M")
                if article.published_at
                else "unknown date"
            )
            parts.append(
                f"[{idx}] {article.title or 'Untitled'}\n"
                f"    Source: {article.source_name} | Date: {date_str}\n"
                f"    {snippet}\n"
            )
        return "\n".join(parts)

    @staticmethod
    def _extract_citations(response: str, articles: list[Article]) -> list[UUID]:
        """Parse [N] citation markers and map them to article UUIDs."""
        matches = re.findall(r"\[(\d+)]", response)
        cited: list[UUID] = []
        seen: set[UUID] = set()
        for m in matches:
            idx = int(m) - 1  # 1-indexed in the prompt
            if 0 <= idx < len(articles):
                aid = articles[idx].id
                if aid not in seen:
                    cited.append(aid)
                    seen.add(aid)
        return cited
