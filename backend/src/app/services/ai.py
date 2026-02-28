from pydantic_ai import Agent

from app.config import Settings, get_settings

SUMMARIZE_SYSTEM_PROMPT = (
    "You are a concise news summarizer. "
    "Produce a clear, neutral summary that captures the key facts. "
    "Keep it to 2-4 sentences. "
    "If the article is not in the requested language, summarize in the "
    "requested language anyway."
)

TRANSLATE_SYSTEM_PROMPT = (
    "You are a professional translator. "
    "Translate the provided text accurately, preserving meaning and tone. "
    "Output only the translated text with no commentary."
)


class AIService:
    """High-level AI operations backed by pydantic-ai."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def _get_model(self) -> str:
        """Return the pydantic-ai model identifier."""
        return f"ollama:{self._settings.llm_model}"

    async def summarize(self, content: str, language: str | None = None) -> str:
        """Summarize article content.

        If *language* is provided the summary will be in that language,
        otherwise the model decides.
        """
        system = SUMMARIZE_SYSTEM_PROMPT
        if language:
            system += f"\nRespond in {language}."

        agent: Agent[None, str] = Agent(self._get_model(), system_prompt=system)
        prompt = f"Summarize this news article concisely:\n\n{content}"
        result = await agent.run(prompt)
        return result.output

    async def translate(self, content: str, target_language: str) -> str:
        """Translate *content* into *target_language*."""
        agent: Agent[None, str] = Agent(self._get_model(), system_prompt=TRANSLATE_SYSTEM_PROMPT)
        prompt = f"Translate the following text to {target_language}:\n\n{content}"
        result = await agent.run(prompt)
        return result.output
