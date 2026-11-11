"""
POST /conversation — UZHAVAN AI Session Engine entry point.

Request:
  Authorization: Bearer <jwt>  (optional in dev mode)
  body: ConversationRequest

Response:
  Content-Type: text/event-stream
  SSE events: session_started → intent_detected → planning → tool_complete →
              evidence_ready → grounding → reasoning → response_complete → completed

No business logic here. This route orchestrates transport and session lifecycle.
The Cognitive Engine owns all AI reasoning.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import logging

from backend.cognitive.graph.conversation import build_graph
from backend.cognitive.graph.nodes.formatter import filter_to_retrieved
from backend.cognitive.graph.nodes.llm_node import fallback_for
from backend.auth.deps import get_repository
from backend.conversation.auth import ANONYMOUS_FARMER_ID, get_farmer_id
from backend.meta.catalog import get_district
from backend.shared.api_errors import not_found
from backend.conversation.rate_limit import check_rate_limit
from backend.diary.store import auto_log, get_diary_store_factory
from backend.session.history import ConversationTurn, get_last_n_turns, persist_turn
from backend.session.manager import Session, get_session_manager
from backend.session.metrics import get_metrics
from backend.session.stream import (
    SSEEvent,
    SSEEventType,
    format_sse,
    node_to_sse_event,
)
from backend.shared.models.context import ConversationContext, KnowledgeContext, SystemContext
from backend.shared.models.farmer import FarmContext, FarmerContext
from backend.shared.models.message import Message

router = APIRouter()
logger = logging.getLogger("uzhavan.conversation")

# Contract §9 error event: {code, message:{en,ta}} — never an exception text or stack trace.
ERROR_MESSAGE = {
    "en": "Something went wrong while preparing the answer. Please try again.",
    "ta": "பதிலை தயாரிக்கும்போது பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.",
}


def _language(value: str | None) -> str:
    return "English" if (value or "").strip().lower() in ("english", "en") else "Tamil"

# Module-level compiled graph (shared across requests)
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph().compile()
    return _graph


# ── Request / Response models ─────────────────────────────────────────────────

class ConversationRequest(BaseModel):
    question: str
    session_id: str | None = None          # None = create new session
    district: str | None = None             # override from JWT if provided
    crop: str | None = None
    crop_stage: str | None = None
    area_ha: float | None = None
    soil_type: str | None = None
    language: str = "Tamil"
    farm_id: str | None = None              # 🔒 with a token: farm values replace client-sent ones
    disease_context: dict[str, Any] | None = None  # research demo scan context


def get_repository_factory():
    """Returns the repository factory without opening a DB pool (only used when farm_id is sent)."""
    return get_repository


async def _apply_farm(request: ConversationRequest, farmer_id: str, repo_factory) -> None:
    """API contract §9: with a token and farm_id, fill district/crop/stage/area from the farm.
    If district remains unassigned, fill from farmer profile or default to Thanjavur."""
    if not request.farm_id or farmer_id == ANONYMOUS_FARMER_ID:
        request.farm_id = None
        if not request.district:
            request.district = "Thanjavur"
        return

    repo = await repo_factory()
    farm = await repo.get_farm(request.farm_id)
    if farm is None or str(farm["farmer_id"]) != farmer_id:
        raise not_found("Farm not found")
    district = get_district(farm["district_id"]) if farm.get("district_id") else None
    request.district = district["name"]["en"] if district else None
    request.crop = farm["crop_id"].replace("_", " ") if farm.get("crop_id") else None
    request.crop_stage = farm.get("crop_stage_id")
    request.area_ha = farm.get("area_ha")
    request.soil_type = None

    if not request.district and farmer_id != ANONYMOUS_FARMER_ID:
        if repo is None:
            repo = await repo_factory()
        farmer = await repo.get_farmer(farmer_id)
        if farmer and farmer.get("district_id"):
            district = get_district(farmer["district_id"])
            if district:
                request.district = district["name"]["en"]
        if not request.district:
            farms = await repo.list_farms(farmer_id)
            if farms:
                f0 = farms[0]
                if f0.get("district_id"):
                    d = get_district(f0["district_id"])
                    request.district = d["name"]["en"] if d else None
                if not request.crop and f0.get("crop_id"):
                    request.crop = f0["crop_id"].replace("_", " ")

    if not request.district:
        request.district = "Thanjavur"


# ── SSE stream generator ──────────────────────────────────────────────────────

async def _stream_conversation(
    request: ConversationRequest,
    farmer_id: str,
) -> AsyncGenerator[str, None]:
    start_ns = time.monotonic_ns()
    session_mgr = get_session_manager()
    language = _language(request.language)

    # ── Session setup ─────────────────────────────────────────────────────────
    session: Session | None = None
    if request.session_id:
        session = await session_mgr.get(request.session_id)

    if session is None:
        farmer = FarmerContext(
            farmer_id=farmer_id,
            district=request.district,
            language=language,
        )
        farm = FarmContext(
            farm_id=request.farm_id or str(uuid.uuid4()),
            farmer_id=farmer_id,
            crop=request.crop,
            crop_stage=request.crop_stage,
            area_ha=request.area_ha,
            district=request.district,
            soil_type=request.soil_type,
        ) if any([request.crop, request.district, request.area_ha]) else None
        session = await session_mgr.create(farmer=farmer, farm=farm)
    else:
        await session_mgr.new_turn(session)

    conversation_id = session.conversation_id
    sid = session.session_id

    # ── Emit session_started ──────────────────────────────────────────────────
    yield format_sse(SSEEvent(
        event=SSEEventType.SESSION_STARTED,
        session_id=sid,
        conversation_id=conversation_id,
        data={"session_id": sid, "conversation_id": conversation_id, "turn": session.turn_count},
    ))

    # ── Fetch recent turns for conversational context ────────────────────────
    recent_turns = await get_last_n_turns(conversation_id, n=5) if conversation_id else []
    history_msgs: list[Message] = []
    for t in recent_turns:
        if t.question:
            history_msgs.append(Message(role="user", content=t.question))
        if t.answer:
            history_msgs.append(Message(role="assistant", content=t.answer))

    # ── Build ConversationContext ─────────────────────────────────────────────
    trace_id = str(uuid.uuid4())
    context = ConversationContext(
        system=SystemContext(
            trace_id=trace_id,
            session_id=sid,
            request_id=str(uuid.uuid4()),
            language=language,   # FP-015: the requested language drives prompts, checks and fallback
        ),
        farmer=session.farmer,
        farm=session.farm,
        current_question=request.question,
        conversation_history=history_msgs,
        knowledge=KnowledgeContext(),
    )

    initial_state: dict[str, Any] = {
        "context": context,
        "user_message": request.question,
        "disease_context": request.disease_context,
        "recent_turns": recent_turns,
        "trace": [],
    }

    # ── Stream graph execution ────────────────────────────────────────────────
    final_state: dict[str, Any] = {}
    graph = get_graph()

    try:
        async for chunk in graph.astream(initial_state, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                if node_name == "__start__":
                    continue
                # Accumulate state for persistence
                final_state.update(node_output)

                sse_event = node_to_sse_event(node_name, node_output, sid, conversation_id)
                if sse_event:
                    yield format_sse(sse_event)

    except Exception as exc:
        logger.exception("conversation graph failed: %s", type(exc).__name__)
        yield format_sse(SSEEvent(
            event=SSEEventType.ERROR,
            session_id=sid,
            conversation_id=conversation_id,
            data={"code": "graph_error", "message": dict(ERROR_MESSAGE)},
        ))
        return

    # ── Persist conversation turn ─────────────────────────────────────────────
    total_latency_ms = int((time.monotonic_ns() - start_ns) / 1_000_000)

    turn = ConversationTurn.from_final_state(
        state=final_state,
        conversation_id=conversation_id,
        session_id=sid,
        farmer_id=farmer_id,
        question=request.question,
        total_latency_ms=total_latency_ms,
    )
    await persist_turn(turn)

    # ── Update metrics ─────────────────────────────────────────────────────────
    evidence = final_state.get("evidence")
    resp = final_state.get("final_response")
    get_metrics().record(
        intent=final_state.get("intent", "unknown"),
        latency_ms=total_latency_ms,
        is_fallback=final_state.get("is_fallback", True),
        grounding_passed=final_state.get("grounding_passed", False),
        safety_passed=final_state.get("safety_passed", True),
        confidence=evidence.overall_confidence if evidence else 0.0,
        tools_used=evidence.tools_used if evidence else [],
    )

    # ── Final sources event ───────────────────────────────────────────────────
    # Contract §9 / FP-015: only when TNAU/RAG chunks were actually retrieved and used; every
    # source must match a retrieved chunk (second guard, independent of the formatter).
    sources = filter_to_retrieved(resp.sources, final_state.get("tool_results") or []) if resp and not resp.is_fallback else []
    if sources:
        yield format_sse(SSEEvent(
            event=SSEEventType.SOURCES,
            session_id=sid,
            conversation_id=conversation_id,
            data={"sources": [{"source": s.source, "title": s.title, "confidence": s.confidence,
                               **({"url": s.url} if s.url else {})} for s in sources]},
        ))

    spoken_text = ""
    if resp and getattr(resp, "spoken_text", None):
        spoken_text = resp.spoken_text
    elif resp and resp.answer:
        from backend.cognitive.voice.spoken_planner import plan_spoken_response
        spoken_text = plan_spoken_response(resp.answer, language=language)
    else:
        spoken_text = fallback_for(language)

    # ── Completed event ───────────────────────────────────────────────────────
    yield format_sse(SSEEvent(
        event=SSEEventType.COMPLETED,
        session_id=sid,
        conversation_id=conversation_id,
        data={
            "answer": resp.answer if resp else fallback_for(language),
            "spoken_text": spoken_text,
            "is_fallback": resp.is_fallback if resp else True,
            "grounded": bool(resp.grounded) if resp else False,
            "grounding_mode": (resp.grounding_mode if resp else ""),
            "confidence": resp.confidence if resp else 0.0,
            "total_latency_ms": total_latency_ms,
            "session_id": sid,
            "conversation_id": conversation_id,
            "turn_id": turn.turn_id,
        },
    ))


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/conversation")
async def conversation(
    request: ConversationRequest,
    farmer_id: str = Depends(get_farmer_id),
    repo_factory=Depends(get_repository_factory),
    diary_factory=Depends(get_diary_store_factory),
) -> StreamingResponse:
    check_rate_limit(farmer_id)
    await _apply_farm(request, farmer_id, repo_factory)
    # Contract §8: with a farmer token, the question is logged to the diary (route layer only;
    # best-effort, never blocks the answer; anonymous callers are not logged).
    await auto_log(diary_factory, farmer_id, "question", request.question, farm_id=request.farm_id)

    return StreamingResponse(
        _stream_conversation(request, farmer_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
