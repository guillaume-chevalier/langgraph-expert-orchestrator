"""
Abstract repository implementation for conversation and SSE event persistence.
Clean architecture pattern - swap implementations without changing business logic.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models import SseEnvelope


class ConversationRecord(BaseModel):
    """Represents a stored conversation with metadata."""

    thread_id: str
    created_at: datetime
    updated_at: datetime
    user_message: str
    input_data: Dict[str, Any]
    status: str  # 'streaming', 'completed', 'error'
    final_summary: Optional[str] = None
    total_events: int = 0


class SseEventRecord(BaseModel):
    """Represents a stored SSE event with metadata."""

    id: str
    thread_id: str
    event_type: str
    sequence: int
    timestamp: datetime
    payload: Dict[str, Any]

    @classmethod
    def from_envelope(cls, envelope: SseEnvelope) -> "SseEventRecord":
        """Create record from SSE envelope."""
        return cls(
            id=str(uuid.uuid4()),
            thread_id=envelope.thread_id,
            event_type=envelope.event,
            sequence=envelope.seq,
            timestamp=envelope.timestamp,
            payload=envelope.payload,
        )


class ConversationRepository(ABC):
    """Abstract base class for conversation persistence."""

    @abstractmethod
    async def create_conversation(
        self, thread_id: str, user_message: str, input_data: Dict[str, Any]
    ) -> ConversationRecord:
        """Create a new conversation."""
        pass

    @abstractmethod
    async def get_conversation(self, thread_id: str) -> Optional[ConversationRecord]:
        """Get conversation by thread ID."""
        pass

    @abstractmethod
    async def update_conversation_status(
        self, thread_id: str, status: str, final_summary: Optional[str] = None
    ) -> bool:
        """Update conversation status and optional final summary."""
        pass

    @abstractmethod
    async def list_conversations(self, limit: int = 50) -> List[ConversationRecord]:
        """List recent conversations."""
        pass

    @abstractmethod
    async def store_sse_event(self, event: SseEnvelope) -> SseEventRecord:
        """Store an SSE event."""
        pass

    @abstractmethod
    async def get_conversation_events(self, thread_id: str) -> List[SseEventRecord]:
        """Get all SSE events for a conversation, ordered by sequence."""
        pass

    @abstractmethod
    async def compact_events(self, thread_id: str) -> List[SseEventRecord]:
        """
        Compact multiple chunks into single events where possible.
        This allows reconstruction of UI state efficiently.
        """
        pass


class InMemoryConversationRepository(ConversationRepository):
    """
    In-memory implementation for development and testing.
    Replace with SQLAlchemy/PostgreSQL for production.
    """

    def __init__(self):
        self._conversations: Dict[str, ConversationRecord] = {}
        self._events: Dict[str, List[SseEventRecord]] = {}

    async def create_conversation(
        self, thread_id: str, user_message: str, input_data: Dict[str, Any]
    ) -> ConversationRecord:
        """Create a new conversation."""
        now = datetime.now(tz=timezone.utc)
        conversation = ConversationRecord(
            thread_id=thread_id,
            created_at=now,
            updated_at=now,
            user_message=user_message,
            input_data=input_data,
            status="streaming",
            total_events=0,
        )
        self._conversations[thread_id] = conversation
        self._events[thread_id] = []
        return conversation

    async def get_conversation(self, thread_id: str) -> Optional[ConversationRecord]:
        """Get conversation by thread ID."""
        return self._conversations.get(thread_id)

    async def update_conversation_status(
        self, thread_id: str, status: str, final_summary: Optional[str] = None
    ) -> bool:
        """Update conversation status and optional final summary."""
        if thread_id not in self._conversations:
            return False

        conv = self._conversations[thread_id]
        conv.status = status
        conv.updated_at = datetime.now(tz=timezone.utc)
        if final_summary:
            conv.final_summary = final_summary
        conv.total_events = len(self._events.get(thread_id, []))
        return True

    async def list_conversations(self, limit: int = 50) -> List[ConversationRecord]:
        """List recent conversations."""
        conversations = list(self._conversations.values())
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return conversations[:limit]

    async def store_sse_event(self, event: SseEnvelope) -> SseEventRecord:
        """Store an SSE event."""
        record = SseEventRecord.from_envelope(event)

        if event.thread_id not in self._events:
            self._events[event.thread_id] = []

        self._events[event.thread_id].append(record)

        # Update conversation total events
        if event.thread_id in self._conversations:
            self._conversations[event.thread_id].total_events += 1
            self._conversations[event.thread_id].updated_at = datetime.now(tz=timezone.utc)

        return record

    async def get_conversation_events(self, thread_id: str) -> List[SseEventRecord]:
        """Get all SSE events for a conversation, ordered by sequence."""
        events = self._events.get(thread_id, [])
        return sorted(events, key=lambda x: x.sequence)

    async def compact_events(self, thread_id: str) -> List[SseEventRecord]:
        """
        Compact multiple chunks into single events where possible.
        For demo: combine expert_chunk events into expert_done events.
        """
        events = await self.get_conversation_events(thread_id)
        compacted = []

        # Group chunks by expert_id and combine them
        expert_chunks: Dict[str, List[str]] = {}

        for event in events:
            if event.event_type == "expert_chunk":
                expert_id = event.payload.get("expert_id", "unknown")
                if expert_id not in expert_chunks:
                    expert_chunks[expert_id] = []
                expert_chunks[expert_id].append(event.payload.get("chunk", ""))
            elif event.event_type == "expert_done":
                # If we already have an expert_done, use it as-is
                compacted.append(event)
            else:
                # Keep other events as-is
                compacted.append(event)

        # Create compacted expert_done events from chunks
        for expert_id, chunks in expert_chunks.items():
            # Only create if we don't already have an expert_done for this expert
            has_done = any(e.event_type == "expert_done" and e.payload.get("expert_id") == expert_id for e in compacted)
            if not has_done:
                compacted_record = SseEventRecord(
                    id=str(uuid.uuid4()),
                    thread_id=thread_id,
                    event_type="expert_done",
                    sequence=999,  # Put at end
                    timestamp=datetime.now(tz=timezone.utc),
                    payload={
                        "expert_id": expert_id,
                        "expert_type": expert_id.replace("_expert", ""),
                        "summary": " ".join(chunks),
                        "confidence": 0.85,
                        "processing_time_ms": 500,
                    },
                )
                compacted.append(compacted_record)

        return sorted(compacted, key=lambda x: x.sequence)


# Global repository instance - swap for different implementations
_repository: Optional[ConversationRepository] = None


def get_repository() -> ConversationRepository:
    """Get the current repository instance."""
    global _repository
    if _repository is None:
        _repository = InMemoryConversationRepository()
    return _repository


def set_repository(repo: ConversationRepository) -> None:
    """Set the repository implementation (for testing/production)."""
    global _repository
    _repository = repo
