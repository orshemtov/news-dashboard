"""One-off script to generate thumbnails for existing videos using ffmpeg.

Finds all video attachments with missing thumbnail_url, extracts a frame
from the video file, and updates the database record.

Usage:
    cd backend && uv run python scripts/backfill_video_thumbs.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Add the backend src to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import asyncio
import json

from sqlalchemy import text

from app.config import get_settings
from app.db.session import async_session_factory


def _get_media_root() -> Path:
    settings = get_settings()
    root = Path(settings.media_storage_path)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[1] / root
    return root


def _extract_thumbnail(video_path: Path, thumb_path: Path) -> bool:
    """Use ffmpeg to extract a frame at 1s (or first frame) as a JPEG thumbnail."""
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-ss",
                "0.5",  # seek to 0.5s
                "-frames:v",
                "1",  # grab one frame
                "-q:v",
                "2",  # high quality JPEG
                str(thumb_path),
            ],
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0 and thumb_path.exists()
    except Exception as e:
        print(f"  ffmpeg error: {e}")
        return False


async def main() -> None:
    media_root = _get_media_root()
    print(f"Media root: {media_root}")

    async with async_session_factory() as session:
        # Find all video attachments with no thumbnail
        rows = (
            await session.execute(
                text("""
                    SELECT a.id,
                           a.media_attachments
                    FROM articles a
                    WHERE EXISTS (
                        SELECT 1 FROM jsonb_array_elements(a.media_attachments) att
                        WHERE att->>'type' = 'video'
                          AND (att->>'thumbnail_url' IS NULL
                               OR att->>'thumbnail_url' = '')
                    )
                """)
            )
        ).all()

        if not rows:
            print("No videos with missing thumbnails found.")
            return

        print(f"Found {len(rows)} article(s) to process.\n")

        updated = 0
        for row in rows:
            article_id = row.id
            attachments = row.media_attachments
            changed = False

            for att in attachments:
                if att.get("type") != "video":
                    continue
                if att.get("thumbnail_url"):
                    continue

                video_url = att.get("url", "")
                video_path = media_root / video_url
                if not video_path.exists():
                    print(f"  SKIP {video_url} -- file not found on disk")
                    continue

                thumb_name = video_path.stem + "_thumb.jpg"
                thumb_path = video_path.parent / thumb_name
                thumb_rel = str(thumb_path.relative_to(media_root))

                print(f"  Processing {video_url} ...", end=" ")

                if _extract_thumbnail(video_path, thumb_path):
                    att["thumbnail_url"] = thumb_rel
                    changed = True
                    print("OK")
                else:
                    print("FAILED")

            if changed:
                await session.execute(
                    text("""
                        UPDATE articles
                        SET media_attachments = CAST(:attachments AS jsonb)
                        WHERE id = :id
                    """),
                    {
                        "attachments": json.dumps(attachments),
                        "id": article_id,
                    },
                )
                updated += 1

        await session.commit()
        print(f"\nDone. Updated {updated}/{len(rows)} article(s).")


if __name__ == "__main__":
    asyncio.run(main())
