"""Real-time Telegram listener using Telethon event handlers.

Instead of polling, this registers a ``NewMessage`` handler on the shared
Telegram client that fires instantly when any monitored channel posts a
new message.  The message is processed through the same ingestion pipeline
(dedup, embed, store) and an event is published to the SSE bus.
"""

from __future__ import annotations

import contextlib

from loguru import logger
from sqlalchemy import select
from telethon import TelegramClient, events

from app.db.session import async_session_factory
from app.models import Article, Source
from app.services.events import NewArticlesEvent, event_bus

# Keep track of the handler so we can remove it on shutdown
_handler_ref: object | None = None


async def start_realtime_listener(client: TelegramClient) -> None:
    """Register a ``NewMessage`` handler for all enabled Telegram sources."""
    global _handler_ref

    # Gather channel usernames from the database
    async with async_session_factory() as db:
        result = await db.execute(
            select(Source).where(Source.enabled.is_(True), Source.source_type == "telegram")
        )
        sources = list(result.scalars().all())

    if not sources:
        logger.info("No enabled Telegram sources — real-time listener not started")
        return

    # Build a map of channel_username -> source for quick lookup
    channel_to_source: dict[str, Source] = {}
    chat_ids: list[str] = []
    for source in sources:
        channel = (source.config or {}).get("channel", "")
        if channel:
            channel_to_source[channel.lower().lstrip("@")] = source
            chat_ids.append(channel)

    if not chat_ids:
        logger.info("No Telegram channels configured — real-time listener not started")
        return

    # Resolve channel entities so Telethon can filter on them
    resolved_entities = []
    for channel in chat_ids:
        try:
            entity = await client.get_entity(channel)
            resolved_entities.append(entity)
        except Exception:
            logger.warning("Could not resolve channel '{}' for real-time listener", channel)

    if not resolved_entities:
        logger.warning("No channels could be resolved — real-time listener not started")
        return

    async def _on_new_message(event: events.NewMessage.Event) -> None:
        """Handle an incoming message from a monitored channel."""
        from app.ingestors.telegram import (
            _build_message_url,
            _clean_telegram_content,
            _detect_language,
            _extract_message_content,
            _get_author,
        )
        from app.services.ingestion import _compute_dedup_hash

        msg = event.message
        content = _extract_message_content(msg)
        if not content:
            return

        content = _clean_telegram_content(content)
        if not content:
            return

        # Identify which source this belongs to
        chat = await event.get_chat()
        username = (getattr(chat, "username", "") or "").lower()
        source = channel_to_source.get(username)
        if source is None:
            return

        from datetime import UTC, datetime

        published_at = msg.date or datetime.now(tz=UTC)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)

        external_id = f"tg-{username}-{msg.id}"
        dedup_hash = _compute_dedup_hash(content)

        # Persist within its own DB session
        try:
            async with async_session_factory() as db, db.begin():
                # Check dedup
                existing = await db.execute(
                    select(Article.id).where(Article.dedup_hash == dedup_hash).limit(1)
                )
                if existing.scalar_one_or_none() is not None:
                    return

                fwd_meta: dict = {}
                if msg.forward is not None:
                    fwd_meta["forwarded"] = True
                    if hasattr(msg.forward, "from_name") and msg.forward.from_name:
                        fwd_meta["forwarded_from"] = msg.forward.from_name

                article = Article(
                    external_id=external_id,
                    source_id=source.id,
                    source_type="telegram",
                    source_name=source.name,
                    title=None,
                    content=content,
                    url=_build_message_url(username, msg.id),
                    author=_get_author(msg),
                    language=_detect_language(content),
                    published_at=published_at,
                    raw_data={},
                    metadata_=fwd_meta,
                    dedup_hash=dedup_hash,
                )
                db.add(article)

                # Update source bookkeeping
                source_row = await db.get(Source, source.id)
                if source_row:
                    source_row.article_count = (source_row.article_count or 0) + 1
                    source_row.error_message = None

            # Generate embedding in the background (non-blocking)
            try:
                from app.services.embedding import EmbeddingService

                emb_service = EmbeddingService()
                text = f"\n{content[:1000]}"
                embeddings = await emb_service.embed_batch([text])
                if embeddings:
                    async with async_session_factory() as db, db.begin():
                        result = await db.execute(
                            select(Article).where(Article.dedup_hash == dedup_hash)
                        )
                        art = result.scalar_one_or_none()
                        if art:
                            art.embedding = embeddings[0]
            except Exception:
                logger.debug(
                    "Embedding generation failed for real-time article, will be filled on next poll"
                )

            # Publish event to SSE bus
            event_bus.publish(NewArticlesEvent(count=1, source_name=source.name))
            logger.info(
                "Real-time: new article from {} (msg_id={})",
                source.name,
                msg.id,
            )

        except Exception:
            logger.exception("Error processing real-time message from {}", source.name)

    # Register the handler, filtering to resolved channels
    client.add_event_handler(
        _on_new_message,
        events.NewMessage(chats=resolved_entities),
    )
    _handler_ref = _on_new_message
    logger.info(
        "Real-time Telegram listener started for {} channels: {}",
        len(resolved_entities),
        ", ".join(chat_ids),
    )


async def stop_realtime_listener(client: TelegramClient) -> None:
    """Remove the event handler (call on shutdown)."""
    global _handler_ref
    if _handler_ref is not None:
        with contextlib.suppress(Exception):
            client.remove_event_handler(_handler_ref)
        _handler_ref = None
        logger.info("Real-time Telegram listener stopped")
