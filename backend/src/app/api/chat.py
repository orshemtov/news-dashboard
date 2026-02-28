import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.chat import ChatConversation, ChatMessage
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationListResponse,
    ConversationResponse,
)

router = APIRouter(tags=["chat"])


@router.post("/", response_model=ChatMessageResponse)
async def send_message(
    body: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """Send a chat message.

    This is a placeholder – the real implementation will use pydantic-ai to
    answer questions about ingested articles.
    """
    # Resolve or create conversation
    if body.conversation_id is not None:
        result = await db.execute(
            select(ChatConversation).where(ChatConversation.id == body.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = ChatConversation(
            title=body.message[:80] if body.message else "New conversation",
        )
        db.add(conversation)
        await db.flush()

    # Persist the user message
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.flush()

    # Placeholder assistant reply
    assistant_msg = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=(
            "AI chat will be implemented with pydantic-ai. "
            "Once configured, I will be able to answer questions about "
            "your ingested news articles, summarize content, and more."
        ),
        model_used="placeholder",
        cited_article_ids=[],
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    return ChatMessageResponse.model_validate(assistant_msg)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """List all conversations (without messages)."""
    result = await db.execute(
        select(ChatConversation).order_by(ChatConversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations]
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Get a conversation with all its messages."""
    result = await db.execute(
        select(ChatConversation)
        .where(ChatConversation.id == conversation_id)
        .options(selectinload(ChatConversation.messages))
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conversation)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(ChatConversation).where(ChatConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conversation)
