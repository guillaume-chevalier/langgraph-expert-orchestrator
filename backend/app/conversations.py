"""
REST API endpoints for conversation management.
Allows frontend to reload conversation history and reconstruct UI state.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.infrastructure.conversation_repository import ConversationRecord, SseEventRecord, get_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


class ConversationResponse(BaseModel):
    """Response model for conversation details."""

    conversation: ConversationRecord
    events: List[SseEventRecord]


class ConversationListResponse(BaseModel):
    """Response model for conversation list."""

    conversations: List[ConversationRecord]
    total: int


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(limit: int = 50):
    """List recent conversations."""
    repo = get_repository()
    conversations = await repo.list_conversations(limit=limit)
    return ConversationListResponse(conversations=conversations, total=len(conversations))


@router.get("/{thread_id}", response_model=ConversationResponse)
async def get_conversation(thread_id: str):
    """Get conversation by thread ID with all events for UI reconstruction."""
    repo = get_repository()

    conversation = await repo.get_conversation(thread_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation {thread_id} not found")

    events = await repo.get_conversation_events(thread_id)

    return ConversationResponse(conversation=conversation, events=events)


@router.get("/{thread_id}/compact", response_model=ConversationResponse)
async def get_conversation_compact(thread_id: str):
    """
    Get conversation with compacted events for efficient UI reconstruction.
    Multiple expert_chunk events are combined into single expert_done events.
    """
    repo = get_repository()

    conversation = await repo.get_conversation(thread_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation {thread_id} not found")

    events = await repo.compact_events(thread_id)

    return ConversationResponse(conversation=conversation, events=events)


@router.delete("/{thread_id}")
async def delete_conversation(thread_id: str):
    """Delete a conversation and all its events."""
    repo = get_repository()

    conversation = await repo.get_conversation(thread_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation {thread_id} not found")

    # For in-memory implementation, just remove from storage
    if hasattr(repo, "_conversations"):
        repo._conversations.pop(thread_id, None)
        repo._events.pop(thread_id, None)

    return {"message": f"Conversation {thread_id} deleted"}
