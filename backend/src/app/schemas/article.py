from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaAttachment(BaseModel):
    """A single media attachment on an article."""

    type: str  # "photo" | "video"
    url: str  # relative path served by /api/media/
    thumbnail_url: str | None = None
    mime_type: str | None = None
    file_size: int | None = None  # bytes
    width: int | None = None
    height: int | None = None
    duration: float | None = None  # seconds, for video


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
    media_attachments: list[MediaAttachment] = []


class ArticleResponse(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    summary: str | None = None
    ingested_at: datetime
    is_duplicate: bool = False
    is_hidden: bool = False
    dedup_cluster_id: UUID | None = None
    metadata_: dict = {}
    media_attachments: list[MediaAttachment] = []


class ArticleDetail(ArticleResponse):
    raw_data: dict = {}
    embedding: list[float] | None = None


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Facets
# ---------------------------------------------------------------------------


class FacetValue(BaseModel):
    value: str
    count: int


class FacetsResponse(BaseModel):
    sources: list[FacetValue]
    languages: list[FacetValue]
    forwarded: list[FacetValue]
