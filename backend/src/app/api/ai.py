from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.article import Article

router = APIRouter(tags=["ai"])


@router.post("/summarize/{article_id}")
async def summarize_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Summarize an article using AI (placeholder).

    The actual implementation will call an LLM to produce a concise summary
    and store it on the article record.
    """
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "article_id": str(article.id),
        "title": article.title,
        "summary": (
            "AI summarization is not yet implemented. "
            "This endpoint will use an LLM to generate a concise summary "
            "of the article content."
        ),
        "status": "placeholder",
    }


@router.post("/translate/{article_id}")
async def translate_article(
    article_id: UUID,
    target_language: str = Query("en", description="Target language code (e.g. 'en', 'he', 'ar')"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Translate an article using AI (placeholder).

    The actual implementation will call an LLM to translate the article
    content into the requested language.
    """
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "article_id": str(article.id),
        "title": article.title,
        "target_language": target_language,
        "translated_content": (
            "AI translation is not yet implemented. "
            f"This endpoint will translate the article into '{target_language}'."
        ),
        "status": "placeholder",
    }
