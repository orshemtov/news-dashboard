"""One-time Telethon interactive login.

Run this script to authenticate with Telegram and create the session file.
After successful auth, the session is saved and the backend can use it
without further interaction.

Usage:
    cd backend && uv run python auth_telegram.py
"""

import asyncio

from app.config import get_settings


async def main() -> None:
    from telethon import TelegramClient

    settings = get_settings()

    if not settings.telegram_api_id or not settings.telegram_api_hash:
        print("ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
        return

    print(f"Session name: {settings.telegram_session_name}")
    print(f"API ID: {settings.telegram_api_id}")
    print()

    client = TelegramClient(
        settings.telegram_session_name,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )

    await client.start()
    me = await client.get_me()
    print(f"\nAuthenticated as: {me.first_name} (id={me.id})")  # type: ignore[union-attr]
    print(f"Session file saved: {settings.telegram_session_name}.session")
    print("\nYou can now restart the backend — ingestion will work.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
