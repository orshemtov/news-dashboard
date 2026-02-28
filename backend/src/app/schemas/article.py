from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArticleBase(BaseModel):
    title: str | None = None
    content: str
    url: str | None = None
    author: str | None = None
    language: str | None = None
    source_type: str
    source_name: str
    published_at: datetime


class ArticleCreate(ArticleBase):
    external_id: str
    raw_data: dict = {}
    metadata_: dict = {}


class ArticleResponse(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    summary: str | None = None
    ingested_at: datetime
    is_duplicate: bool = False
    dedup_cluster_id: UUID | None = None
    metadata_: dict = {}


class ArticleDetail(ArticleResponse):
    raw_data: dict = {}
    embedding: list[float] | None = None


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int
