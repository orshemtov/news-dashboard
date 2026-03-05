from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.article import Article
from app.models.source import Source
from app.schemas.stats import DashboardStats
from app.services.theme import ThemeService

router = APIRouter(tags=["stats"])


@router.get("/trending")
async def get_trending_themes(
    window_minutes: int = Query(180, ge=30, le=720),
    limit: int = Query(10, ge=1, le=20),
    min_sources: int = Query(2, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get trending themes/clusters from the last X minutes."""
    svc = ThemeService(db)
    return await svc.get_trending_themes(
        window_minutes=window_minutes,
        limit=limit,
        min_sources=min_sources,
    )


@router.get("", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
) -> DashboardStats:
    """Aggregate dashboard statistics with real SQL queries."""
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    twenty_four_hours_ago = now - timedelta(hours=24)

    # ── Total articles ────────────────────────────────────────────────
    total_articles: int = (await db.execute(select(func.count(Article.id)))).scalar_one()

    # ── Articles today ────────────────────────────────────────────────
    articles_today: int = (
        await db.execute(select(func.count(Article.id)).where(Article.ingested_at >= today_start))
    ).scalar_one()

    # ── Sources ───────────────────────────────────────────────────────
    total_sources: int = (await db.execute(select(func.count(Source.id)))).scalar_one()

    active_sources: int = (
        await db.execute(select(func.count(Source.id)).where(Source.enabled.is_(True)))
    ).scalar_one()

    # ── Articles by source name ───────────────────────────────────────
    by_source_rows = (
        await db.execute(
            select(Article.source_name, func.count(Article.id))
            .group_by(Article.source_name)
            .order_by(func.count(Article.id).desc())
        )
    ).all()
    articles_by_source: dict[str, int] = {name: count for name, count in by_source_rows}

    # ── Articles by hour (last 24 h) ─────────────────────────────────
    # Use date_trunc to bucket by hour.
    hour_col = func.date_trunc("hour", Article.ingested_at)
    hourly_rows = (
        await db.execute(
            select(hour_col.label("hour"), func.count(Article.id))
            .where(Article.ingested_at >= twenty_four_hours_ago)
            .group_by(hour_col)
            .order_by(hour_col)
        )
    ).all()
    articles_by_hour: list[dict] = [{"hour": h.isoformat(), "count": c} for h, c in hourly_rows]

    # ── Languages breakdown ───────────────────────────────────────────
    lang_rows = (
        await db.execute(
            select(
                func.coalesce(Article.language, "unknown"),
                func.count(Article.id),
            )
            .group_by(Article.language)
            .order_by(func.count(Article.id).desc())
        )
    ).all()
    languages: dict[str, int] = {lang: count for lang, count in lang_rows}

    # ── Latest ingestion time ─────────────────────────────────────────
    latest_ingestion: datetime | None = (
        await db.execute(select(func.max(Article.ingested_at)))
    ).scalar_one_or_none()

    return DashboardStats(
        total_articles=total_articles,
        articles_today=articles_today,
        active_sources=active_sources,
        total_sources=total_sources,
        articles_by_source=articles_by_source,
        articles_by_hour=articles_by_hour,
        languages=languages,
        latest_ingestion=latest_ingestion,
    )
