import contextlib
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from telethon import TelegramClient

from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError

from app.ingestors.base import BaseIngestor, RawArticle, SourceDisabledError

_DEFAULT_LIMIT = 50

# Regex to strip full t.me URLs down to the bare username
_TME_URL_RE = re.compile(r"^https?://(?:www\.)?t\.me/", re.IGNORECASE)


def sanitize_channel(raw: str) -> str:
    """Normalise a Telegram channel identifier to a bare username.

    Handles ``@channel``, ``https://t.me/channel``, and plain ``channel``.
    """
    value = raw.strip()
    # Strip t.me URLs first
    value = _TME_URL_RE.sub("", value)
    # Remove leading @ if present
    value = value.lstrip("@")
    # Strip trailing slashes (from copy-pasted URLs)
    value = value.rstrip("/")
    return value


class TelegramIngestor(BaseIngestor):
    """Ingestor for Telegram channel messages via Telethon."""

    def __init__(
        self,
        source_name: str,
        config: dict,
        client: TelegramClient,
        *,
        min_id: int = 0,
    ) -> None:
        super().__init__(source_name, config)
        self._client = client
        self._channel: str = sanitize_channel(config.get("channel", ""))
        self._limit: int = config.get("limit", _DEFAULT_LIMIT)
        self._min_id: int = min_id

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
            # Covers UsernameInvalidError and other Telethon RPC errors
            return False, (
                f"Channel '{self._channel}' could not be resolved: {exc}. "
                f"The channel may have been deleted or renamed."
            )

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
        except (UsernameInvalidError, UsernameNotOccupiedError) as exc:
            raise SourceDisabledError(
                f"Channel '{self._channel}' does not exist or was deleted: {exc}"
            ) from exc
        except Exception:
            logger.exception(
                "Telegram ingestor {}: failed to resolve channel {}",
                self.source_name,
                self._channel,
            )
            return []

        # Use min_id to only fetch messages newer than the last known one.
        # This avoids missing messages when a channel posts more than `limit`
        # messages between polls, and makes dedup cheaper.
        kwargs: dict[str, Any] = {"limit": self._limit}
        if self._min_id > 0:
            kwargs["min_id"] = self._min_id

        raw_messages = await self._client.get_messages(entity, **kwargs)
        messages: list[Any] = list(raw_messages) if raw_messages else []  # type: ignore[arg-type]
        articles: list[RawArticle] = []

        for msg in messages:
            content = _extract_message_content(msg)
            has_media = _has_media(msg)

            # Skip messages with no text AND no media
            if not content and not has_media:
                continue

            # Clean Telegram formatting
            if content:
                content = _clean_telegram_content(content)

            # After cleaning, if still no text and no media, skip
            if not content and not has_media:
                continue

            # For media-only messages, use a placeholder so dedup/embedding work
            if not content:
                content = "[media]"

            published_at: datetime = msg.date or datetime.now(tz=UTC)
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=UTC)

            raw_data: dict = {}
            if msg.to_dict is not None:
                with contextlib.suppress(Exception):
                    raw_data = _make_json_safe(msg.to_dict())

            fwd_meta: dict = {}
            if msg.forward is not None:
                fwd_meta["forwarded"] = True
                if hasattr(msg.forward, "from_name") and msg.forward.from_name:
                    fwd_meta["forwarded_from"] = msg.forward.from_name

            # Download media attachments
            media_attachments: list[dict] = []
            if has_media:
                try:
                    from app.services.media import download_telegram_media

                    ext_id = f"tg-{self._channel}-{msg.id}"
                    media_attachments = await download_telegram_media(self._client, msg, ext_id)
                except Exception:
                    logger.warning(
                        "Media download failed for msg {} in {}",
                        msg.id,
                        self._channel,
                    )

            articles.append(
                RawArticle(
                    external_id=f"tg-{self._channel}-{msg.id}",
                    source_type="telegram",
                    source_name=self.source_name,
                    title=None,
                    content=content,
                    url=_build_message_url(self._channel, msg.id),
                    author=_get_author(msg),
                    language=_detect_language(content),
                    published_at=published_at,
                    raw_data=raw_data,
                    metadata=fwd_meta,
                    media_attachments=media_attachments,
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


def _make_json_safe(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable values (datetime, bytes, etc.)."""
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.hex()
    # Fall back to str for any other exotic types
    try:
        # Primitives (str, int, float, bool, None) are fine
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
    except Exception:
        pass
    return str(obj)


def _extract_message_content(msg: Any) -> str:
    """Return text content from a Telegram message, including captions."""
    text: str = getattr(msg, "text", None) or ""
    if not text:
        text = getattr(msg, "message", None) or ""
    return text.strip()


def _has_media(msg: Any) -> bool:
    """Check whether a Telegram message contains downloadable photo/video media."""
    media = getattr(msg, "media", None)
    if media is None:
        return False

    from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

    if isinstance(media, MessageMediaPhoto):
        return True
    if isinstance(media, MessageMediaDocument):
        doc = media.document
        if doc is None:
            return False
        mime = getattr(doc, "mime_type", "") or ""
        return mime.startswith("video/")
    return False


def _clean_telegram_content(text: str) -> str:
    """Strip Telegram markdown formatting and navigation cruft from content."""
    # Remove empty markdown links: [ ](url)
    text = re.sub(r"\[\s*\]\([^)]*\)", "", text)
    # Convert markdown links to just the text: [visible](url) -> visible
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    # Remove markdown bold: **text** -> text
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    # Remove markdown italic: __text__ -> text
    text = re.sub(r"__([^_]+)__", r"\1", text)
    # Remove single asterisk emphasis: *text* -> text
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    # Remove bare URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove common navigation emojis
    text = re.sub(r"[👈🏽👉🏽⬇️⬆️➡️⬅️🔗📢📌]+", "", text)
    # Remove Hebrew navigation prompts
    text = re.sub(r"לקריאה?\s+נוחה?\s+(במחשב|בנייד)", "", text)
    text = re.sub(r"הצטרפו\s+ל(ערוץ|קבוצה)", "", text)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


_HEBREW_RE = re.compile(r"[\u0590-\u05FF]")


def _detect_language(text: str) -> str | None:
    """Simple heuristic language detection based on character ranges."""
    # Count Hebrew characters vs Latin
    hebrew_count = len(_HEBREW_RE.findall(text))
    latin_count = sum(
        1 for ch in text if unicodedata.category(ch).startswith("L") and ord(ch) < 0x0590
    )

    total = hebrew_count + latin_count
    if total == 0:
        return None
    if hebrew_count / total > 0.3:
        return "he"
    if latin_count / total > 0.3:
        return "en"
    return None


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
    clean = sanitize_channel(channel)
    return f"https://t.me/{clean}/{message_id}"
