"""
All shared data models and type aliases live here so that both
the LangGraph nodes and the FastAPI layer import from ONE place.
"""

from __future__ import annotations

import operator
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# SSE CONTRACT – These exact fields are sent over the wire to the browser.
# --------------------------------------------------------------------------- #

EventName = Literal[
    "router_decision",
    "record_done",
    "final_summary",
    "error",
]


class SseEnvelope(BaseModel):
    """
    Every SSE line is:  event: <event>\n
                        data: <json serialized SseEnvelope>\n\n
    """

    event: EventName
    thread_id: str
    seq: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    payload: Dict[str, Any]


# --------------------------------------------------------------------------- #
# LANGGRAPH STATE – This is the single source of truth **inside** the graph.
# --------------------------------------------------------------------------- #


class AgentState(TypedDict, total=False):
    """
    NOTE: We keep this very small on purpose. Add keys as the
    workflow evolves, but resist the urge to bloat it.
    """

    thread_id: str
    records: List[Any]  # HostRecord | CertificateRecord objects from repository
    host_records: List[Any]  # Split hosts for fan-out
    cert_records: List[Any]  # Split certificates for fan-out
    messages: List[Any]  # langchain_core.messages.*
    router_decision: List[str]  # ["host_fan", "cert_fan"]
    summaries: Annotated[List[Dict[str, str]], operator.add]  # list of {"kind": str, "content": str} with add reducer
    stats: Dict[str, int]  # host_count, cert_count
    final_summary: str  # merged answer


# --------------------------------------------------------------------------- #
# EXPERT AND SUMMARY MODELS
# --------------------------------------------------------------------------- #
class ExpertSummary(BaseModel):
    """Individual expert analysis summary."""

    expert_id: str
    expert_type: str
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time_ms: int


class RouterDecisionPayload(BaseModel):
    """Payload for router_decision events."""

    selected_experts: List[str]
    reasoning: str = ""
    total_records: Optional[int] = None


class RecordDonePayload(BaseModel):
    """Payload for record_done events."""

    kind: str  # "host" or "cert"
    id: str  # host.ip or cert.fingerprint_sha256
    summary: str


class FinalSummaryPayload(BaseModel):
    """Payload for final_summary events."""

    summary: str
    expert_count: int
    total_processing_time_ms: int


class ErrorPayload(BaseModel):
    """Payload for error events."""

    error_code: str = "UNSPECIFIED"
    message: str
    details: Optional[str] = None
    expert_id: Optional[str] = None
    error_type: str = ""  # Keep for backward compatibility


# --------------------------------------------------------------------------- #
# FASTAPI REQUEST BODY
# --------------------------------------------------------------------------- #


class StreamRequest(BaseModel):
    """
    POST body for /v1/stream
    """

    thread_id: Optional[str] = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="Caller can provide a UUID to resume a thread; otherwise generated.",
    )
    message: str = Field(..., description="Natural-language query from the user.")
    input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary JSON blob (e.g., host metadata) forwarded to experts.",
    )
