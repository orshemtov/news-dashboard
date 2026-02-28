from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.article import Article
from app.schemas.article import ArticleResponse
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/", response_model=SearchResponse)
async def search_articles(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Search articles.

    Currently implements keyword search via SQL ``ILIKE``.  Semantic and hybrid
    modes will be added once the embedding pipeline is wired up.
    """
    pattern = f"%{body.query}%"

    base = select(Article).where(
        or_(
            Article.title.ilike(pattern),
            Article.content.ilike(pattern),
        )
    )

    if not body.include_duplicates:
        base = base.where(Article.is_duplicate.is_(False))
    if body.sources:
        base = base.where(Article.source_name.in_(body.sources))
    if body.source_types:
        base = base.where(Article.source_type.in_(body.source_types))
    if body.language:
        base = base.where(Article.language == body.language)
    if body.from_date:
        base = base.where(Article.published_at >= body.from_date)
    if body.to_date:
        base = base.where(Article.published_at <= body.to_date)

    # Total count
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar_one()

    # Paginated results
    stmt = (
        base.order_by(Article.published_at.desc())
        .offset((body.page - 1) * body.page_size)
        .limit(body.page_size)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    return SearchResponse(
        items=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        query=body.query,
        mode=body.mode,
    )
