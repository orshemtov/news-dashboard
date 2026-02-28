import contextlib
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from telethon import TelegramClient

from app.ingestors.base import BaseIngestor, RawArticle

_DEFAULT_LIMIT = 50


class TelegramIngestor(BaseIngestor):
    """Ingestor for Telegram channel messages via Telethon."""

    def __init__(
        self,
        source_name: str,
        config: dict,
        client: TelegramClient,
    ) -> None:
        super().__init__(source_name, config)
        self._client = client
        self._channel: str = config.get("channel", "")
        self._limit: int = config.get("limit", _DEFAULT_LIMIT)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def validate_config(self) -> tuple[bool, str]:
        if not self._channel:
            return False, "Channel is not set in the source config."

        if not self._client.is_connected():
            try:
                await self._client.connect()
            except Exception as exc:
                return False, (
                    f"Telegram client failed to connect. "
                    f"Ensure API ID and hash are configured correctly: {exc}"
                )

        try:
            entity = await self._client.get_entity(self._channel)
        except ValueError:
            return False, (f"Channel '{self._channel}' not found. Check the username or ID.")
        except Exception as exc:
            return False, f"Failed to resolve channel: {exc}"

        if entity is None:
            return False, f"Channel '{self._channel}' could not be resolved."

        return True, "OK"

    async def fetch(self) -> list[RawArticle]:
        if not self._channel:
            logger.warning("Telegram ingestor {}: no channel configured", self.source_name)
            return []

        if not self._client.is_connected():
            await self._client.connect()

        try:
            entity = await self._client.get_entity(self._channel)
        except Exception:
            logger.exception(
                "Telegram ingestor {}: failed to resolve channel {}",
                self.source_name,
                self._channel,
            )
            return []

        raw_messages = await self._client.get_messages(entity, limit=self._limit)
        messages: list[Any] = list(raw_messages) if raw_messages else []  # type: ignore[arg-type]
        articles: list[RawArticle] = []

        for msg in messages:
            content = _extract_message_content(msg)
            if not content:
                continue

            published_at: datetime = msg.date or datetime.now(tz=UTC)
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=UTC)

            raw_data: dict = {}
            if msg.to_dict is not None:
                with contextlib.suppress(Exception):
                    raw_data = msg.to_dict()

            fwd_meta: dict = {}
            if msg.forward is not None:
                fwd_meta["forwarded"] = True
                if hasattr(msg.forward, "from_name") and msg.forward.from_name:
                    fwd_meta["forwarded_from"] = msg.forward.from_name

            articles.append(
                RawArticle(
                    external_id=f"tg-{self._channel}-{msg.id}",
                    source_type="telegram",
                    source_name=self.source_name,
                    title=None,
                    content=content,
                    url=_build_message_url(self._channel, msg.id),
                    author=_get_author(msg),
                    language=None,
                    published_at=published_at,
                    raw_data=raw_data,
                    metadata=fwd_meta,
                )
            )

        logger.info(
            "Telegram ingestor {}: fetched {} messages from {}",
            self.source_name,
            len(articles),
            self._channel,
        )
        return articles


# ----------------------------------------------------------------------
# Channel search
# ----------------------------------------------------------------------


async def search_channels(
    client: TelegramClient,
    query: str,
    limit: int = 20,
) -> list[dict]:
    """Search for Telegram channels by keyword.

    Returns a list of dicts with keys ``id``, ``title``, ``username``,
    and ``participants_count`` (when available).
    """
    from telethon.tl.functions.contacts import SearchRequest

    if not client.is_connected():
        await client.connect()

    result = await client(SearchRequest(q=query, limit=limit))

    channels: list[dict] = []
    chats: list[Any] = getattr(result, "chats", []) or []
    for chat in chats:
        channels.append(
            {
                "id": getattr(chat, "id", None),
                "title": getattr(chat, "title", None),
                "username": getattr(chat, "username", None),
                "participants_count": getattr(chat, "participants_count", None),
            }
        )
    return channels


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _extract_message_content(msg: Any) -> str:
    """Return text content from a Telegram message, including captions."""
    text: str = getattr(msg, "text", None) or ""
    if not text:
        text = getattr(msg, "message", None) or ""
    return text.strip()


def _get_author(msg: Any) -> str | None:
    """Try to extract an author string from the message sender."""
    sender = getattr(msg, "sender", None)
    if sender is None:
        return None
    first = getattr(sender, "first_name", "") or ""
    last = getattr(sender, "last_name", "") or ""
    name = f"{first} {last}".strip()
    return name or getattr(sender, "username", None)


def _build_message_url(channel: str, message_id: int) -> str:
    """Build a t.me link to the message."""
    clean = channel.lstrip("@")
    return f"https://t.me/{clean}/{message_id}"
