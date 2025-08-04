"""
FastAPI router exposing POST /v1/stream ➜ SSE.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.infrastructure.conversation_repository import get_repository
from app.langgraph.graph import GRAPH
from app.models import (
    ErrorPayload,
    FinalSummaryPayload,
    RecordDonePayload,
    RouterDecisionPayload,
    SseEnvelope,
    StreamRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["streaming"])


def _is_custom_event(path, value) -> bool:
    """
    All user-generated CustomEvents come through the special
    __custom__ channel. That is stable across LangGraph versions.
    """
    return path and path[-1] == "__custom__"


def _sse(event: SseEnvelope) -> str:
    """
    Encode one Server-Sent-Event frame with ID for resumable streams.
    """
    payload = event.model_dump(mode="json")
    return f"id: {event.seq}\nevent: {event.event}\ndata: {json.dumps(payload, default=str)}\n\n"


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
)
async def stream_endpoint(req: StreamRequest) -> StreamingResponse:
    """
    One SSE stream per request.
    """

    async def _event_gen() -> AsyncGenerator[str, None]:
        seq = 0
        repo = get_repository()

        # Create conversation record
        await repo.create_conversation(thread_id=req.thread_id, user_message=req.message, input_data=req.input)

        # Initialize state for map-reduce flow
        init_state = {
            "thread_id": req.thread_id,
            "messages": [HumanMessage(content=req.message)],
            "summaries": [],  # For reducer
        }

        try:
            # Track state for incremental updates
            router_decision_sent = False
            processed_record_ids = set()

            async for chunk in GRAPH.astream(init_state, stream_mode="values"):

                # Dataset loading stats - emit when stats are available
                if "stats" in chunk and not router_decision_sent:
                    seq += 1
                    stats = chunk.get("stats", {})
                    total_records = stats.get("host_count", 0) + stats.get("cert_count", 0)
                    event = SseEnvelope(
                        event="router_decision",
                        thread_id=req.thread_id,
                        seq=seq,
                        payload=RouterDecisionPayload(
                            selected_experts=["host_fan", "cert_fan"],  # Fixed experts for demo
                            reasoning=f"Router: {stats.get('host_count', 0)} hosts, "
                            + f"{stats.get('cert_count', 0)} certs – experts chosen accordingly",
                            total_records=total_records,
                        ).model_dump(),
                    )
                    await repo.store_sse_event(event)
                    yield _sse(event)
                    router_decision_sent = True

                # Individual record analyses complete (record_done events)
                current_summaries = chunk.get("summaries", [])
                for s in current_summaries:
                    record_id = s.get("record_id")
                    if record_id and record_id not in processed_record_ids:
                        processed_record_ids.add(record_id)
                        seq += 1

                        # Send record_done event for individual record analysis
                        event = SseEnvelope(
                            event="record_done",
                            thread_id=req.thread_id,
                            seq=seq,
                            payload=RecordDonePayload(kind=s["kind"], id=record_id, summary=s["content"]).model_dump(),
                        )
                        await repo.store_sse_event(event)
                        yield _sse(event)

                # Final comprehensive analysis
                if "final_summary" in chunk:
                    seq += 1
                    summaries = chunk.get("summaries", [])
                    stats = chunk.get("stats", {})

                    total_time = sum(s.get("processing_time_ms", 500) for s in summaries)
                    total_records = stats.get("host_count", 0) + stats.get("cert_count", 0)

                    event = SseEnvelope(
                        event="final_summary",
                        thread_id=req.thread_id,
                        seq=seq,
                        payload=FinalSummaryPayload(
                            summary=chunk["final_summary"],
                            expert_count=total_records,  # Individual record analyses count
                            total_processing_time_ms=total_time,
                        ).model_dump(),
                    )
                    await repo.store_sse_event(event)
                    await repo.update_conversation_status(req.thread_id, "completed", chunk["final_summary"])
                    yield _sse(event)

        except Exception as exc:
            logger.exception("Graph execution failed")
            seq += 1
            event = SseEnvelope(
                event="error",
                thread_id=req.thread_id,
                seq=seq,
                payload=ErrorPayload(
                    error_code=exc.__class__.__name__,
                    message=str(exc),
                ).model_dump(),
            )
            # Store error event and update conversation status
            await repo.store_sse_event(event)
            await repo.update_conversation_status(req.thread_id, "error")
            yield _sse(event)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return StreamingResponse(
        _event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
