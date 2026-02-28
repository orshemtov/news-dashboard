import abc
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawArticle:
    """Normalized article data from any source."""

    external_id: str
    source_type: str
    source_name: str
    title: str | None
    content: str
    url: str | None = None
    author: str | None = None
    language: str | None = None
    published_at: datetime = field(default_factory=datetime.now)
    raw_data: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class BaseIngestor(abc.ABC):
    """Abstract base for all news source ingestors."""

    def __init__(self, source_name: str, config: dict) -> None:
        self.source_name = source_name
        self.config = config

    @abc.abstractmethod
    async def fetch(self) -> list[RawArticle]:
        """Fetch new articles from the source."""
        ...

    @abc.abstractmethod
    async def validate_config(self) -> tuple[bool, str]:
        """Validate the source configuration. Returns (success, message)."""
        ...
