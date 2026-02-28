import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.db.session import async_session_factory
from app.models.source import Source
from app.schemas.source import (
    SourceCreate,
    SourcePreset,
    SourceResponse,
    SourceTestRequest,
    SourceTestResponse,
    SourceUpdate,
)
from app.services.ingestion import ingest_source

router = APIRouter(tags=["sources"])

# Set to prevent background tasks from being garbage-collected
_ingest_tasks: set[asyncio.Task] = set()

# ---------------------------------------------------------------------------
# Preset source configurations
# ---------------------------------------------------------------------------
_PRESETS: list[SourcePreset] = [
    SourcePreset(
        name="Abu Ali Express",
        source_type="telegram",
        config={"channel": "abualiexpress"},
        category="telegram",
        description="אבו עלי אקספרס – real-time security and military updates (Hebrew/Arabic)",
    ),
    SourcePreset(
        name="Amit Segal",
        source_type="telegram",
        config={"channel": "amitsegal"},
        category="telegram",
        description="עמית סגל – political commentary and breaking news (Hebrew)",
    ),
    SourcePreset(
        name="301 Arab World",
        source_type="telegram",
        config={"channel": "arabworld301news"},
        category="telegram",
        description="חדשות 301 העולם הערבי – Arab world news and analysis (Hebrew)",
    ),
    SourcePreset(
        name="Rotter HaMadlif",
        source_type="telegram",
        config={"channel": "rotter_HaMadlif"},
        category="telegram",
        description="רוטר המדליף – breaking news leaks and updates (Hebrew)",
    ),
    SourcePreset(
        name="MyGPLANET",
        source_type="telegram",
        config={"channel": "MyGPLANET"},
        category="telegram",
        description="MyGPLANET – geopolitical news and analysis",
    ),
    SourcePreset(
        name="Saleh Desk",
        source_type="telegram",
        config={"channel": "salehdesk1"},
        category="telegram",
        description="סאלח דסק – security and military news (Hebrew/Arabic)",
    ),
    SourcePreset(
        name="Yinon News",
        source_type="telegram",
        config={"channel": "yinonews"},
        category="telegram",
        description="ינון מגזין – news and current affairs (Hebrew)",
    ),
]


@router.get("/", response_model=list[SourceResponse])
async def list_sources(
    db: AsyncSession = Depends(get_db),
) -> list[SourceResponse]:
    """List all configured sources."""
    result = await db.execute(select(Source).order_by(Source.name))
    sources = result.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]


@router.post("/", response_model=SourceResponse, status_code=201)
async def create_source(
    body: SourceCreate,
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Create a new news source and kick off initial ingestion."""
    # Check for duplicate name
    existing = await db.execute(select(Source).where(Source.name == body.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Source with this name already exists")

    source = Source(**body.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)

    response = SourceResponse.model_validate(source)

    # Fire-and-forget background ingestion (uses its own DB session)
    source_id = source.id
    task = asyncio.create_task(_background_ingest(source_id))
    _ingest_tasks.add(task)
    task.add_done_callback(_ingest_tasks.discard)

    return response


@router.get("/presets", response_model=list[SourcePreset])
async def get_presets() -> list[SourcePreset]:
    """Return preset source configurations for quick setup."""
    return _PRESETS


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Get a single source by ID."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse.model_validate(source)


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    body: SourceUpdate,
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Update an existing source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await db.flush()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)


@router.post("/test", response_model=SourceTestResponse)
async def test_source(body: SourceTestRequest) -> SourceTestResponse:
    """Test a source configuration."""
    if body.source_type == "telegram":
        return SourceTestResponse(
            success=False,
            message="Telegram source testing requires Telegram API credentials. "
            "Configure them in the application settings first.",
        )

    return SourceTestResponse(
        success=False,
        message=f"Unknown source type: {body.source_type}",
    )


@router.get("/telegram/search")
async def search_telegram_channels(
    query: str = "",
    limit: int = 20,
) -> list[dict]:
    """Search Telegram channels by keyword.

    Returns a list of channel dicts with ``id``, ``title``, ``username``,
    and ``participants_count``.  If Telegram credentials are not configured
    the endpoint returns the presets that match the query instead.
    """
    settings = get_settings()

    if not query.strip():
        return []

    # If credentials are available, do a live Telegram search
    if settings.telegram_api_id and settings.telegram_api_hash:
        from app.ingestors.telegram import search_channels
        from app.services.telegram_client import get_telegram_client

        try:
            client = await get_telegram_client()
            results = await search_channels(client, query, limit=limit)
            return results
        except Exception:
            logger.exception("Telegram channel search failed")
            raise HTTPException(
                status_code=502,
                detail="Telegram channel search failed. Check credentials.",
            ) from None

    # Fallback: search presets by name/description
    q = query.lower()
    return [
        {
            "id": None,
            "title": p.name,
            "username": p.config.get("channel"),
            "participants_count": None,
        }
        for p in _PRESETS
        if q in p.name.lower() or q in (p.description or "").lower()
    ]


@router.post("/{source_id}/ingest")
async def trigger_ingest(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    """Manually trigger ingestion for a specific source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        count = await ingest_source(source, db)
    except Exception as exc:
        logger.exception("Ingestion failed for source {}", source.name)
        raise HTTPException(status_code=500, detail=str(exc)) from None
    return {"source": source.name, "new_articles": count}


# ---------------------------------------------------------------------------
# Background ingestion helper
# ---------------------------------------------------------------------------


async def _background_ingest(source_id: UUID) -> None:
    """Run ingestion in background with its own DB session.

    This is spawned via ``asyncio.create_task`` so it runs concurrently
    without blocking the API response.
    """
    try:
        async with async_session_factory() as db, db.begin():
            result = await db.execute(select(Source).where(Source.id == source_id))
            source = result.scalar_one_or_none()
            if source is None:
                logger.warning("Background ingest: source {} not found", source_id)
                return
            count = await ingest_source(source, db)
            logger.info(
                "Background ingest complete for {}: {} new articles",
                source.name,
                count,
            )
    except Exception:
        logger.exception("Background ingestion failed for source {}", source_id)
