"""Media storage service for downloading and serving Telegram attachments.

Downloads photos and videos from Telegram messages to the local filesystem,
organised by date and article external ID. Files are served back through a
FastAPI static-file endpoint.
"""

from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from typing import Any

from loguru import logger
from telethon import TelegramClient
from telethon.tl.types import (
    MessageMediaDocument,
    MessageMediaPhoto,
)

from app.config import get_settings

# Map Telegram media types to our simplified type strings
_PHOTO_MIME = "image/jpeg"

# Video MIME types we recognise
_VIDEO_MIMES = frozenset(
    {
        "video/mp4",
        "video/quicktime",
        "video/x-matroska",
        "video/webm",
        "video/mpeg",
    }
)


def _get_media_root() -> Path:
    """Return the absolute path to the media storage directory."""
    settings = get_settings()
    root = Path(settings.media_storage_path)
    if not root.is_absolute():
        # Relative paths are resolved from the backend/ directory
        root = Path(__file__).resolve().parents[3] / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def _build_relative_path(external_id: str, extension: str) -> str:
    """Build a deterministic relative file path for a media attachment.

    Layout: ``<external_id>/<uuid>.<ext>``
    """
    # Sanitise the external_id so it's safe as a directory name
    safe_id = external_id.replace("/", "_").replace("\\", "_")
    filename = f"{uuid.uuid4().hex[:12]}{extension}"
    return f"{safe_id}/{filename}"


async def download_telegram_media(
    client: TelegramClient,
    msg: Any,
    external_id: str,
) -> list[dict[str, Any]]:
    """Download media from a Telegram message and return attachment metadata.

    Returns a list of dicts matching the ``MediaAttachment`` schema shape:
    ``{type, url, thumbnail_url, mime_type, file_size, width, height, duration}``.

    Only photos and videos are downloaded; other document types are skipped.
    """
    settings = get_settings()
    if not settings.media_download_enabled:
        return []

    media = getattr(msg, "media", None)
    if media is None:
        return []

    max_bytes = settings.media_max_file_size_mb * 1024 * 1024
    attachments: list[dict[str, Any]] = []

    # ----- Photo -----
    if isinstance(media, MessageMediaPhoto):
        attachment = await _download_photo(client, msg, external_id, max_bytes)
        if attachment:
            attachments.append(attachment)

    # ----- Video (stored as Document with video mime) -----
    elif isinstance(media, MessageMediaDocument):
        doc = media.document
        if doc is None:
            return []

        mime = getattr(doc, "mime_type", "") or ""
        if mime in _VIDEO_MIMES:
            attachment = await _download_video(client, msg, doc, external_id, max_bytes)
            if attachment:
                attachments.append(attachment)

    return attachments


async def _download_photo(
    client: TelegramClient,
    msg: Any,
    external_id: str,
    max_bytes: int,
) -> dict[str, Any] | None:
    """Download a photo attachment and return metadata."""
    try:
        rel_path = _build_relative_path(external_id, ".jpg")
        abs_path = _get_media_root() / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        result = await client.download_media(msg, file=str(abs_path))
        if result is None:
            return None

        # If Telethon chose a different extension, update
        actual = Path(result)
        if actual != abs_path:
            rel_path = str(actual.relative_to(_get_media_root()))

        file_size = actual.stat().st_size
        if file_size > max_bytes:
            actual.unlink(missing_ok=True)
            logger.warning(
                "Photo too large ({:.1f} MB), skipping: {}",
                file_size / 1024 / 1024,
                external_id,
            )
            return None

        # Try to get dimensions from the photo sizes
        width, height = _get_photo_dimensions(msg)

        return {
            "type": "photo",
            "url": rel_path,
            "thumbnail_url": None,
            "mime_type": _PHOTO_MIME,
            "file_size": file_size,
            "width": width,
            "height": height,
            "duration": None,
        }

    except Exception:
        logger.exception("Failed to download photo for {}", external_id)
        return None


async def _download_video(
    client: TelegramClient,
    msg: Any,
    doc: Any,
    external_id: str,
    max_bytes: int,
) -> dict[str, Any] | None:
    """Download a video attachment and return metadata."""
    try:
        # Check size before downloading
        file_size = getattr(doc, "size", 0) or 0
        if file_size > max_bytes:
            logger.warning(
                "Video too large ({:.1f} MB), skipping: {}",
                file_size / 1024 / 1024,
                external_id,
            )
            return None

        mime = getattr(doc, "mime_type", "video/mp4") or "video/mp4"
        ext = mimetypes.guess_extension(mime) or ".mp4"
        rel_path = _build_relative_path(external_id, ext)
        abs_path = _get_media_root() / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        result = await client.download_media(msg, file=str(abs_path))
        if result is None:
            return None

        actual = Path(result)
        if actual != abs_path:
            rel_path = str(actual.relative_to(_get_media_root()))

        # Extract video attributes (width, height, duration)
        width, height, duration = _get_video_attributes(doc)

        return {
            "type": "video",
            "url": rel_path,
            "thumbnail_url": None,
            "mime_type": mime,
            "file_size": file_size or actual.stat().st_size,
            "width": width,
            "height": height,
            "duration": duration,
        }

    except Exception:
        logger.exception("Failed to download video for {}", external_id)
        return None


def _get_photo_dimensions(msg: Any) -> tuple[int | None, int | None]:
    """Extract the largest photo size dimensions from a Telegram message."""
    try:
        photo = getattr(msg, "photo", None)
        if photo is None:
            return None, None
        sizes = getattr(photo, "sizes", []) or []
        if not sizes:
            return None, None
        # Pick the largest size (last in the list)
        largest = sizes[-1]
        w = getattr(largest, "w", None)
        h = getattr(largest, "h", None)
        return w, h
    except Exception:
        return None, None


def _get_video_attributes(doc: Any) -> tuple[int | None, int | None, float | None]:
    """Extract width, height, duration from a Document's video attributes."""
    try:
        attrs = getattr(doc, "attributes", []) or []
        for attr in attrs:
            # DocumentAttributeVideo
            if hasattr(attr, "w") and hasattr(attr, "h") and hasattr(attr, "duration"):
                return (
                    getattr(attr, "w", None),
                    getattr(attr, "h", None),
                    float(getattr(attr, "duration", 0)),
                )
        return None, None, None
    except Exception:
        return None, None, None
