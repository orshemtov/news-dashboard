from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.article import ArticleResponse


class SearchRequest(BaseModel):
    query: str
    mode: Literal["keyword", "semantic", "hybrid"] = "hybrid"
    sources: list[str] | None = None  # filter by source names
    source_types: list[str] | None = None
    language: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    include_duplicates: bool = False
    page: int = 1
    page_size: int = 20


class SearchResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    query: str
    mode: str
