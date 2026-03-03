from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError

from app.ingestors.base import SourceDisabledError
from app.ingestors.telegram import TelegramIngestor


def _make_ingestor(channel: str = "TestChannel", *, min_id: int = 0) -> TelegramIngestor:
    client = AsyncMock()
    client.is_connected = MagicMock(return_value=True)
    config = {"channel": channel, "limit": 10}
    return TelegramIngestor(
        source_name="Test Source",
        config=config,
        client=client,
        min_id=min_id,
    )


@pytest.mark.asyncio
async def test_fetch_raises_source_disabled_on_username_invalid():
    ingestor = _make_ingestor("NonExistentChannel")

    # Simulate UsernameInvalidError from Telethon
    request = MagicMock()
    ingestor._client.get_entity.side_effect = UsernameInvalidError(request)

    with pytest.raises(SourceDisabledError, match="does not exist or was deleted"):
        await ingestor.fetch()


@pytest.mark.asyncio
async def test_fetch_raises_source_disabled_on_username_not_occupied():
    ingestor = _make_ingestor("DeletedChannel")

    request = MagicMock()
    ingestor._client.get_entity.side_effect = UsernameNotOccupiedError(request)

    with pytest.raises(SourceDisabledError, match="does not exist or was deleted"):
        await ingestor.fetch()


@pytest.mark.asyncio
async def test_fetch_returns_empty_on_transient_error():
    """Transient errors (e.g. network) should return [] without raising."""
    ingestor = _make_ingestor("SomeChannel")
    ingestor._client.get_entity.side_effect = ConnectionError("network timeout")

    result = await ingestor.fetch()
    assert result == []


@pytest.mark.asyncio
async def test_fetch_returns_empty_when_no_channel_configured():
    ingestor = _make_ingestor("")

    result = await ingestor.fetch()
    assert result == []
