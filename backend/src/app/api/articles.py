import asyncio
import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.article import Article
from app.schemas.article import ArticleDetail, ArticleListResponse, ArticleResponse
from app.services.events import event_bus

router = APIRouter(tags=["articles"])


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
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    """List articles with pagination and filtering."""
    base = select(Article)

    if source_type is not None:
        base = base.where(Article.source_type == source_type)
    if source_name is not None:
        base = base.where(Article.source_name == source_name)
    if language is not None:
        base = base.where(Article.language == language)
    if is_duplicate is not None:
        base = base.where(Article.is_duplicate == is_duplicate)
    if from_date is not None:
        base = base.where(Article.published_at >= from_date)
    if to_date is not None:
        base = base.where(Article.published_at <= to_date)

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
