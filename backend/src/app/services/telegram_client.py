"""Shared Telegram client singleton.

Telethon uses a SQLite-backed session file under the hood, so creating
multiple ``TelegramClient`` instances that point at the same session causes
``"database is locked"`` errors.  This module provides a single shared
client that is initialised once at application startup and re-used by all
callers.
"""

from loguru import logger
from telethon import TelegramClient

from app.config import get_settings

_client: TelegramClient | None = None


def _create_client() -> TelegramClient:
    settings = get_settings()
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        raise ValueError(
            "Telegram API credentials (TELEGRAM_API_ID, TELEGRAM_API_HASH) "
            "are not configured in .env"
        )
    return TelegramClient(
        settings.telegram_session_name,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )


async def get_telegram_client() -> TelegramClient:
    """Return the shared Telegram client, connecting if necessary."""
    global _client
    if _client is None:
        _client = _create_client()

    if not _client.is_connected():
        await _client.connect()
        logger.info("Telegram client connected")

    return _client


async def disconnect_telegram_client() -> None:
    """Disconnect the shared client (call on shutdown)."""
    global _client
    if _client is not None and _client.is_connected():
        await _client.disconnect()
        logger.info("Telegram client disconnected")
    _client = None
