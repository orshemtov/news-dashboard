from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None
    provider: Literal["ollama", "openai"] | None = None
    model: str | None = None


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    cited_article_ids: list[UUID] = []
    model_used: str | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = []


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]


class ChatConfigResponse(BaseModel):
    default_provider: str
    default_model: str
    providers: list[dict]
