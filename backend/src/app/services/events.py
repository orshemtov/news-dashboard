"""In-process event bus for pushing new-article notifications to SSE clients.

Uses ``asyncio.Queue`` per subscriber so each connected SSE client gets its
own copy of every event without blocking the publisher.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from app.models.article import Article


# ------------------------------------------------------------------
# Serialisation helper
# ------------------------------------------------------------------


def article_to_sse_dict(article: Article) -> dict[str, Any]:
    """Serialise an Article ORM instance to a dict matching ArticleResponse."""
    return {
        "id": str(article.id),
        "title": article.title,
        "content": article.content,
        "url": article.url,
        "author": article.author,
        "language": article.language,
        "source_type": article.source_type,
        "source_name": article.source_name,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "summary": article.summary,
        "ingested_at": (
            article.ingested_at.isoformat()
            if article.ingested_at
            else datetime.now(tz=UTC).isoformat()
        ),
        "is_duplicate": article.is_duplicate,
        "dedup_cluster_id": str(article.dedup_cluster_id) if article.dedup_cluster_id else None,
        "metadata_": article.metadata_ or {},
        "media_attachments": article.media_attachments or [],
    }


# ------------------------------------------------------------------
# Event types
# ------------------------------------------------------------------


@dataclass
class NewArticlesEvent:
    """Emitted whenever new articles are persisted."""

    count: int
    source_name: str
    articles: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "new_articles",
            "count": self.count,
            "source_name": self.source_name,
            "articles": self.articles,
            "timestamp": self.timestamp,
        }


# ------------------------------------------------------------------
# Broker
# ------------------------------------------------------------------


class EventBus:
    """Simple in-process pub/sub backed by per-subscriber queues."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[NewArticlesEvent]] = set()

    def subscribe(self) -> asyncio.Queue[NewArticlesEvent]:
        q: asyncio.Queue[NewArticlesEvent] = asyncio.Queue()
        self._subscribers.add(q)
        logger.debug("SSE client subscribed (total={})", len(self._subscribers))
        return q

    def unsubscribe(self, q: asyncio.Queue[NewArticlesEvent]) -> None:
        self._subscribers.discard(q)
        logger.debug("SSE client unsubscribed (total={})", len(self._subscribers))

    def publish(self, event: NewArticlesEvent) -> None:
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # drop event for slow consumers


# Module-level singleton
event_bus = EventBus()
