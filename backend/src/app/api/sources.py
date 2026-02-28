from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.source import Source
from app.schemas.source import (
    SourceCreate,
    SourcePreset,
    SourceResponse,
    SourceTestRequest,
    SourceTestResponse,
    SourceUpdate,
)

router = APIRouter(tags=["sources"])

# ---------------------------------------------------------------------------
# Preset source configurations
# ---------------------------------------------------------------------------
_PRESETS: list[SourcePreset] = [
    # Israeli sources
    SourcePreset(
        name="Ynet",
        source_type="rss",
        config={"url": "https://www.ynet.co.il/Integration/StoryRss2.xml"},
        category="israeli",
        description="Ynet – Israel's most-visited news site (Hebrew)",
    ),
    SourcePreset(
        name="Walla! News",
        source_type="rss",
        config={"url": "https://rss.walla.co.il/feed/1"},
        category="israeli",
        description="Walla! News – major Israeli news portal (Hebrew)",
    ),
    SourcePreset(
        name="Mako / N12",
        source_type="rss",
        config={"url": "https://rcs.mako.co.il/rss/31750a2610f26110VgnVCM1000004801000aRCRD.xml"},
        category="israeli",
        description="Mako / Channel 12 News (Hebrew)",
    ),
    SourcePreset(
        name="Kan News",
        source_type="rss",
        config={"url": "https://www.kan.org.il/Rss/"},
        category="israeli",
        description="Kan – Israeli public broadcasting news (Hebrew)",
    ),
    SourcePreset(
        name="Israel Hayom",
        source_type="rss",
        config={"url": "https://www.israelhayom.co.il/rss.xml"},
        category="israeli",
        description="Israel Hayom – widely-circulated Israeli daily (Hebrew)",
    ),
    SourcePreset(
        name="Haaretz English",
        source_type="rss",
        config={"url": "https://www.haaretz.com/cmlink/1.628765"},
        category="israeli",
        description="Haaretz – English edition of the Israeli newspaper",
    ),
    SourcePreset(
        name="Times of Israel",
        source_type="rss",
        config={"url": "https://www.timesofisrael.com/feed/"},
        category="israeli",
        description="Times of Israel – English-language Israeli online newspaper",
    ),
    # Foreign / international sources
    SourcePreset(
        name="Fox News",
        source_type="rss",
        config={"url": "https://moxie.foxnews.com/google-publisher/latest.xml"},
        category="foreign",
        description="Fox News – latest headlines",
    ),
    SourcePreset(
        name="CNBC",
        source_type="rss",
        config={"url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
        category="foreign",
        description="CNBC – top news and analysis",
    ),
    SourcePreset(
        name="BBC News",
        source_type="rss",
        config={"url": "https://feeds.bbci.co.uk/news/rss.xml"},
        category="foreign",
        description="BBC News – world news from the BBC",
    ),
    SourcePreset(
        name="Reuters",
        source_type="rss",
        config={"url": "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"},
        category="foreign",
        description="Reuters – international news wire",
    ),
    SourcePreset(
        name="AP News",
        source_type="rss",
        config={"url": "https://feedx.net/rss/ap.xml"},
        category="foreign",
        description="Associated Press – global news",
    ),
    # Telegram channels
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
    """Create a new news source."""
    # Check for duplicate name
    existing = await db.execute(select(Source).where(Source.name == body.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Source with this name already exists")

    source = Source(**body.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


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
    """Test a source configuration (fetch and parse)."""
    if body.source_type == "rss":
        return await _test_rss_source(body.config)

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
async def search_telegram_channels() -> dict[str, str]:
    """Search Telegram channels (placeholder)."""
    return {
        "message": "Telegram channel search requires Telegram API credentials "
        "(api_id and api_hash). This feature will be available once "
        "credentials are configured in the application settings."
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _test_rss_source(config: dict) -> SourceTestResponse:
    """Attempt to fetch and parse an RSS feed, returning sample items."""
    url = config.get("url")
    if not url:
        return SourceTestResponse(success=False, message="Missing 'url' in config")

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "NewsDashboard/0.1"})
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        return SourceTestResponse(
            success=False,
            message=f"Failed to fetch RSS feed: {exc}",
        )

    # Attempt a lightweight parse with the built-in xml parser
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as exc:
        return SourceTestResponse(
            success=False,
            message=f"Failed to parse RSS XML: {exc}",
        )

    # Extract sample <item> elements (RSS 2.0) or <entry> (Atom)
    items: list[dict] = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    rss_items = root.findall(".//item") or root.findall(".//atom:entry", ns)
    for item in rss_items[:5]:
        title = item.findtext("title") or item.findtext("atom:title", namespaces=ns) or ""
        link = item.findtext("link") or item.findtext("atom:link", namespaces=ns) or ""
        pub_date = item.findtext("pubDate") or item.findtext("atom:published", namespaces=ns) or ""
        items.append({"title": title.strip(), "link": link.strip(), "pubDate": pub_date.strip()})

    return SourceTestResponse(
        success=True,
        message=f"Successfully fetched and parsed RSS feed – found {len(rss_items)} item(s).",
        sample_items=items,
    )
