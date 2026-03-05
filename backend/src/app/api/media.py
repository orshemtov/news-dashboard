"""API endpoint for serving stored media files."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from app.services.media import _get_media_root

router = APIRouter()


@router.get("/{file_path:path}")
async def serve_media(file_path: str) -> FileResponse:
    """Serve a media file from local storage.

    The ``file_path`` is the relative path stored in
    ``media_attachments[].url`` on an article.
    """
    media_root = _get_media_root()
    abs_path = (media_root / file_path).resolve()

    # Prevent path traversal
    if not str(abs_path).startswith(str(media_root.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    if not abs_path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")

    # Guess content type from extension
    suffix = abs_path.suffix.lower()
    content_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
    }
    media_type = content_type_map.get(suffix, "application/octet-stream")

    return FileResponse(
        path=abs_path,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
