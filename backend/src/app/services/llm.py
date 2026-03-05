from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from loguru import logger

from app.config import get_settings


class ThemeRankOutput(BaseModel):
    scores: dict[str, float] = Field(default_factory=dict)


class LLMService:
    """Service for summarization and deduplication verification via PydanticAI."""

    def __init__(self, model: str | None = None) -> None:
        self.settings = get_settings()
        self.model = model or self.settings.llm_model

        provider_base = self._ollama_base_url()
        model_name = self._model_name()

        self._model = OpenAIChatModel(
            model_name=model_name,
            provider=OllamaProvider(base_url=provider_base),
        )
        self._text_agent = Agent(self._model)
        self._rank_agent = Agent(self._model, output_type=ThemeRankOutput)

    def _model_name(self) -> str:
        if self.model.startswith("ollama/"):
            return self.model.split("/", 1)[1]
        return self.model

    def _ollama_base_url(self) -> str:
        base = (self.settings.llm_api_base or "http://localhost:11434").rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        return base

    async def summarize(self, text: str) -> str | None:
        """Generate a concise summary of the given text."""
        if not self.settings.llm_enabled:
            return None

        prompt = (
            "Summarize the following news article in exactly one short sentence. "
            "Focus on the core event. "
            "Keep the language of the summary the same as the article language.\n\n"
            f"Article: {text[:4000]}"
        )

        try:
            result = await self._text_agent.run(prompt)
            output = result.output
            return output.strip() if isinstance(output, str) else str(output)
        except Exception:
            logger.exception("Failed to generate summary with LLM")
            return None

    async def summarize_theme(self, snippets: list[str]) -> str | None:
        """Summarize multiple snippets from one event cluster."""
        if not self.settings.llm_enabled or not snippets:
            return None

        joined = "\n\n".join(s[:900] for s in snippets[:4])
        prompt = (
            "You are a professional news editor. "
            "Summarize this developing news event from multiple sources into exactly ONE clean sentence. "
            "Rules:\n"
            "- Same language as the majority of the snippets\n"
            "- Maximum 160 characters\n"
            "- State only verified facts from the snippets\n"
            "- No source/channel names, no hashtags, no URLs, no emoji\n"
            "- No telegram promotional text (e.g. 'for easy reading', 'join our channel')\n"
            "- No meta-commentary about the sources\n"
            "- End with a period\n\n"
            f"Snippets:\n{joined}"
        )

        try:
            result = await self._text_agent.run(prompt)
            output = result.output
            text = output.strip() if isinstance(output, str) else str(output)
            text = " ".join(text.split())
            return text[:180]
        except Exception:
            logger.exception("Failed to summarize trending theme with LLM")
            return None

    async def verify_is_same_event(self, text1: str, text2: str) -> bool:
        """
        Verify if two articles describe the exact same news event.
        Returns True if they are the same event, False otherwise.
        """
        if not self.settings.llm_enabled or not self.settings.llm_dedup_verify:
            return True  # Fallback to semantic similarity if disabled

        prompt = (
            "Analyze these two news snippets and determine if they describe the EXACT SAME EVENT. "
            "Different events happening at the same time/location should be NO. "
            "Only return the word 'YES' or 'NO'. Do not explain.\n\n"
            f"Snippet 1: {text1[:2000]}\n\n"
            f"Snippet 2: {text2[:2000]}\n"
        )

        try:
            result = await self._text_agent.run(prompt)
            output = result.output
            text = output.strip().upper() if isinstance(output, str) else str(output).upper()
            return "YES" in text
        except Exception:
            logger.exception("Failed to verify duplicate with LLM")
            return True  # Fallback to True to maintain original semantic behavior

    async def rank_themes_by_importance(
        self,
        themes: list[dict[str, str | int | float]],
    ) -> dict[str, float]:
        """Rank trending themes by importance using the LLM.

        Returns a map of theme_id -> score (0-100). Empty map on failure.
        """
        if not self.settings.llm_enabled or not themes:
            return {}

        compact = [
            {
                "id": str(t.get("id")),
                "theme": str(t.get("theme", ""))[:340],
                "sources": int(t.get("source_count", 0)),
                "articles": int(t.get("article_count", 0)),
                "minutes_ago": int(t.get("minutes_ago", 0)),
            }
            for t in themes
        ]

        prompt = (
            "You are ranking real-time news themes by editorial importance. "
            "Prefer major military, political, security, or high-impact public events. "
            "De-prioritize opinion/personality chatter.\n\n"
            "For EACH item, output a score from 0 to 100.\n"
            "Return structured output only.\n\n"
            f"Items: {compact}"
        )

        try:
            result = await self._rank_agent.run(prompt)
            output = result.output
            scores: dict[str, float] = {}
            for key, value in output.scores.items():
                scores[str(key)] = max(0.0, min(100.0, float(value)))
            return scores
        except Exception:
            logger.exception("Failed to rank trending themes with LLM")
            return {}
