from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.article import ArticleResponse
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search import SearchService

router = APIRouter(tags=["search"])


@router.post("/", response_model=SearchResponse)
async def search_articles(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Search articles using keyword, semantic, or hybrid (RRF) search."""
    service = SearchService(db)
    articles, total = await service.hybrid_search(body)

    return SearchResponse(
        items=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        query=body.query,
        mode=body.mode,
    )
