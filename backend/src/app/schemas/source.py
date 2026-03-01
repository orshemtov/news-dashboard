from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SourceBase(BaseModel):
    name: str
    source_type: str  # telegram
    config: dict = {}  # Telegram channel info
    poll_interval_seconds: int = 300
    enabled: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    poll_interval_seconds: int | None = None
    enabled: bool | None = None


class SourceResponse(SourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    last_polled_at: datetime | None = None
    article_count: int = 0
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class SourceTestRequest(BaseModel):
    source_type: str
    config: dict


class SourceTestResponse(BaseModel):
    success: bool
    message: str
    sample_items: list[dict] = []


# Preset source templates
class SourcePreset(BaseModel):
    name: str
    source_type: str
    config: dict
    category: str  # "israeli", "foreign", "telegram"
    description: str


# Channel suggestion
class ChannelSuggestion(BaseModel):
    username: str
    name: str
    description: str
    language: str
    tags: list[str] = []
    similarity_score: float | None = None
