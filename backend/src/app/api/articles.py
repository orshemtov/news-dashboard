import asyncio
import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.article import Article
from app.schemas.article import (
    ArticleDetail,
    ArticleListResponse,
    ArticleResponse,
    FacetsResponse,
    FacetValue,
)
from app.services.events import event_bus

router = APIRouter(tags=["articles"])


# ------------------------------------------------------------------
# Shared filter builder
# ------------------------------------------------------------------


def _apply_filters(
    stmt: Select,
    *,
    source_type: str | None = None,
    source_name: str | None = None,
    language: str | None = None,
    is_duplicate: bool | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    sources_include: list[str] | None = None,
    sources_exclude: list[str] | None = None,
    languages_include: list[str] | None = None,
    languages_exclude: list[str] | None = None,
    forwarded: bool | None = None,
    exclude_keywords: list[str] | None = None,
    dedup_cluster_id: UUID | None = None,
    include_hidden: bool = False,
) -> Select:
    """Apply all supported filters to a SELECT statement."""
    # Hidden articles filter
    if not include_hidden:
        stmt = stmt.where(Article.is_hidden == False)

    # Legacy single-value filters
    if source_type is not None:
        stmt = stmt.where(Article.source_type == source_type)
    if source_name is not None:
        stmt = stmt.where(Article.source_name == source_name)
    if language is not None:
        stmt = stmt.where(Article.language == language)
    if is_duplicate is not None:
        stmt = stmt.where(Article.is_duplicate == is_duplicate)
    if from_date is not None:
        stmt = stmt.where(Article.published_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(Article.published_at <= to_date)
    if dedup_cluster_id is not None:
        stmt = stmt.where(Article.dedup_cluster_id == dedup_cluster_id)

    # Facet-style multi-value filters
    if sources_include:
        stmt = stmt.where(Article.source_name.in_(sources_include))
    if sources_exclude:
        stmt = stmt.where(Article.source_name.notin_(sources_exclude))
    if languages_include:
        stmt = stmt.where(Article.language.in_(languages_include))
    if languages_exclude:
        stmt = stmt.where(Article.language.notin_(languages_exclude))
    if forwarded is not None:
        if forwarded:
            stmt = stmt.where(Article.metadata_["forwarded"].as_boolean().is_(True))
        else:
            stmt = stmt.where(Article.metadata_["forwarded"].as_boolean().isnot(True))

    # Keyword exclusion
    if exclude_keywords:
        for kw in exclude_keywords:
            pattern = f"%{kw}%"
            stmt = stmt.where(~Article.content.ilike(pattern))

    return stmt


# ------------------------------------------------------------------
# SSE stream – real-time article notifications
# ------------------------------------------------------------------
# NOTE: This route MUST be declared before /{article_id} so that
# FastAPI does not try to match "stream" as a UUID path parameter.
# ------------------------------------------------------------------


@router.get("/stream")
async def article_stream() -> StreamingResponse:
    """Server-Sent Events endpoint that pushes notifications when new
    articles are ingested.  Frontend clients can use ``EventSource`` to
    subscribe and invalidate their query cache instantly.
    """

    async def _generate():
        queue = event_bus.subscribe()
        try:
            # Send an initial heartbeat so the client knows the
            # connection is alive.
            yield "event: connected\ndata: {}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"event: new_articles\ndata: {json.dumps(event.to_dict())}\n\n"
                except asyncio.TimeoutError:
                    # Send a keepalive comment to prevent proxy/browser
                    # timeouts.
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ------------------------------------------------------------------
# Facets
# ------------------------------------------------------------------


@router.get("/facets", response_model=FacetsResponse)
async def get_facets(
    # All the same filter params so facet counts reflect current filters
    source_type: str | None = None,
    source_name: str | None = None,
    language: str | None = None,
    is_duplicate: bool | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    sources_include: list[str] | None = Query(None),
    sources_exclude: list[str] | None = Query(None),
    languages_include: list[str] | None = Query(None),
    languages_exclude: list[str] | None = Query(None),
    forwarded: bool | None = None,
    exclude_keywords: list[str] | None = Query(None),
    dedup_cluster_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> FacetsResponse:
    """Return aggregated facet counts using cross-dimensional filtering.

    Each facet dimension's counts are computed with all filters applied
    EXCEPT that dimension's own include/exclude filter.  This is the
    standard Datadog / Elasticsearch behaviour – selecting a source
    narrows language & forwarded counts but still shows all sources
    with their (cross-filtered) counts.
    """

    # --- Source facet: apply all filters EXCEPT source include/exclude ---
    source_base = _apply_filters(
        select(Article),
        source_type=source_type,
        source_name=source_name,
        language=language,
        is_duplicate=is_duplicate,
        from_date=from_date,
        to_date=to_date,
        exclude_keywords=exclude_keywords,
        dedup_cluster_id=dedup_cluster_id,
        languages_include=languages_include,
        languages_exclude=languages_exclude,
        forwarded=forwarded,
    ).subquery()

    source_stmt = (
        select(source_base.c.source_name, func.count().label("cnt"))
        .group_by(source_base.c.source_name)
        .order_by(func.count().desc())
    )
    source_result = await db.execute(source_stmt)
    sources = [FacetValue(value=row.source_name, count=row.cnt) for row in source_result.all()]

    # --- Language facet: apply all filters EXCEPT language include/exclude ---
    lang_base = _apply_filters(
        select(Article),
        source_type=source_type,
        source_name=source_name,
        language=language,
        is_duplicate=is_duplicate,
        from_date=from_date,
        to_date=to_date,
        exclude_keywords=exclude_keywords,
        dedup_cluster_id=dedup_cluster_id,
        sources_include=sources_include,
        sources_exclude=sources_exclude,
        forwarded=forwarded,
    ).subquery()

    lang_stmt = (
        select(
            func.coalesce(lang_base.c.language, "unknown").label("lang"),
            func.count().label("cnt"),
        )
        .group_by("lang")
        .order_by(func.count().desc())
    )
    lang_result = await db.execute(lang_stmt)
    languages = [FacetValue(value=row.lang, count=row.cnt) for row in lang_result.all()]

    # --- Forwarded facet: apply all filters EXCEPT forwarded ---
    fwd_base = _apply_filters(
        select(Article),
        source_type=source_type,
        source_name=source_name,
        language=language,
        is_duplicate=is_duplicate,
        from_date=from_date,
        to_date=to_date,
        exclude_keywords=exclude_keywords,
        dedup_cluster_id=dedup_cluster_id,
        sources_include=sources_include,
        sources_exclude=sources_exclude,
        languages_include=languages_include,
        languages_exclude=languages_exclude,
    ).subquery()

    fwd_expr = case(
        (fwd_base.c.metadata["forwarded"].as_boolean().is_(True), "true"),
        else_="false",
    ).label("fwd")
    fwd_stmt = (
        select(fwd_expr, func.count().label("cnt"))
        .group_by(fwd_expr)
        .order_by(func.count().desc())
    )
    fwd_result = await db.execute(fwd_stmt)
    forwarded_facet = [FacetValue(value=row.fwd, count=row.cnt) for row in fwd_result.all()]

    return FacetsResponse(
        sources=sources,
        languages=languages,
        forwarded=forwarded_facet,
    )


# ------------------------------------------------------------------
# CRUD routes
# ------------------------------------------------------------------


@router.get("/", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: str | None = None,
    source_name: str | None = None,
    language: str | None = None,
    is_duplicate: bool | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    sources_include: list[str] | None = Query(None),
    sources_exclude: list[str] | None = Query(None),
    languages_include: list[str] | None = Query(None),
    languages_exclude: list[str] | None = Query(None),
    forwarded: bool | None = None,
    exclude_keywords: list[str] | None = Query(None),
    dedup_cluster_id: UUID | None = None,
    include_hidden: bool = False,
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    """List articles with pagination and filtering."""
    base = select(Article)
    base = _apply_filters(
        base,
        source_type=source_type,
        source_name=source_name,
        language=language,
        is_duplicate=is_duplicate,
        from_date=from_date,
        to_date=to_date,
        sources_include=sources_include,
        sources_exclude=sources_exclude,
        languages_include=languages_include,
        languages_exclude=languages_exclude,
        forwarded=forwarded,
        exclude_keywords=exclude_keywords,
        dedup_cluster_id=dedup_cluster_id,
        include_hidden=include_hidden,
    )

    # Total count
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar_one()

    # Paginated results
    stmt = (
        base.order_by(Article.published_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    return ArticleListResponse(
        items=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ArticleDetail:
    """Get a single article with full details."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleDetail.model_validate(article)


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an article."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    await db.delete(article)


@router.post("/{article_id}/hide", response_model=ArticleResponse)
async def hide_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ArticleResponse:
    """Hide an article from the feed."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    article.is_hidden = True
    await db.commit()
    await db.refresh(article)
    return ArticleResponse.model_validate(article)


@router.post("/{article_id}/unhide", response_model=ArticleResponse)
async def unhide_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ArticleResponse:
    """Unhide an article."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    article.is_hidden = False
    await db.commit()
    await db.refresh(article)
    return ArticleResponse.model_validate(article)
