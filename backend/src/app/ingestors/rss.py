import hashlib
import time
from datetime import UTC, datetime

import feedparser
import httpx
from loguru import logger

from app.ingestors.base import BaseIngestor, RawArticle

_FETCH_TIMEOUT = 30.0


def _struct_time_to_datetime(st: time.struct_time | None) -> datetime:
    """Convert a ``time.struct_time`` (as returned by feedparser) to an
    aware ``datetime`` in UTC.  Falls back to *now* when *st* is ``None``."""
    from calendar import timegm

    if st is None:
        return datetime.now(tz=UTC)
    return datetime.fromtimestamp(timegm(st), tz=UTC)


def _extract_content(entry: dict) -> str:
    """Return the best available textual content from a feed entry."""
    if "content" in entry:
        parts: list[str] = [c.get("value", "") for c in entry["content"] if c.get("value")]
        if parts:
            return "\n".join(parts)

    return entry.get("summary", "") or entry.get("description", "") or ""


def _entry_id(entry: dict) -> str:
    """Derive a stable external_id from a feed entry."""
    if entry.get("id"):
        return str(entry["id"])
    if entry.get("link"):
        return str(entry["link"])
    blob = (entry.get("title", "") + entry.get("summary", "")).encode()
    return hashlib.sha256(blob).hexdigest()


def _detect_language(feed: dict, entry: dict) -> str | None:
    """Try to detect the language from feed or entry metadata."""
    if entry.get("summary_detail", {}).get("language"):
        return str(entry["summary_detail"]["language"])
    if feed.get("feed", {}).get("language"):
        return str(feed["feed"]["language"])
    return None


class RSSIngestor(BaseIngestor):
    """Ingestor for RSS / Atom feeds."""

    def __init__(self, source_name: str, config: dict) -> None:
        super().__init__(source_name, config)
        self._url: str = config.get("url", "")

    async def validate_config(self) -> tuple[bool, str]:
        if not self._url:
            return False, "Feed URL is not set in the source config."

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=_FETCH_TIMEOUT) as client:
                resp = await client.get(self._url)
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            return False, f"Failed to reach feed URL: {exc}"

        feed = feedparser.parse(resp.text)
        if feed.bozo and not feed.entries:
            return False, f"Feed could not be parsed: {feed.bozo_exception}"

        return True, "OK"

    async def fetch(self) -> list[RawArticle]:
        if not self._url:
            logger.warning("RSS ingestor {}: no URL configured", self.source_name)
            return []

        async with httpx.AsyncClient(follow_redirects=True, timeout=_FETCH_TIMEOUT) as client:
            resp = await client.get(self._url)
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        articles: list[RawArticle] = []

        for entry in feed.entries:
            entry_dict: dict = dict(entry)
            content = _extract_content(entry_dict)
            if not content:
                logger.debug("Skipping entry with no content: {}", entry_dict.get("link"))
                continue

            title_raw = entry_dict.get("title")
            url_raw = entry_dict.get("link")
            author_raw = entry_dict.get("author")
            pub_parsed = entry_dict.get("published_parsed") or entry_dict.get("updated_parsed")

            articles.append(
                RawArticle(
                    external_id=_entry_id(entry_dict),
                    source_type="rss",
                    source_name=self.source_name,
                    title=str(title_raw) if title_raw else None,
                    content=content,
                    url=str(url_raw) if url_raw else None,
                    author=str(author_raw) if author_raw else None,
                    language=_detect_language(feed, entry_dict),
                    published_at=_struct_time_to_datetime(
                        pub_parsed if isinstance(pub_parsed, time.struct_time) else None
                    ),
                    raw_data=entry_dict,
                )
            )

        logger.info(
            "RSS ingestor {}: fetched {} articles from {}",
            self.source_name,
            len(articles),
            self._url,
        )
        return articles
