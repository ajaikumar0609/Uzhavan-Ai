"""
ConversationHistory — stores every conversation turn for replay and analytics.

A turn captures everything needed to replay any conversation:
  Intent → Planner → Agents → Evidence → Prompt → LLM → Response

Stored under key: "conversation:{conversation_id}:turns"
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from backend.session.store import store_append, store_get
from backend.shared.models.version import PlatformVersion


class ConversationTurn(BaseModel):
    """
    Single question-answer exchange. Fully replayable.
    Includes every AI version so historical analysis is possible.
    """
    turn_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    session_id: str
    farmer_id: str

    # ── Question ──────────────────────────────────────────────────────────────
    question: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # ── Cognitive Engine outputs ──────────────────────────────────────────────
    intent: str = ""
    intent_confidence: float = 0.0
    capabilities_used: list[str] = Field(default_factory=list)
    evidence_confidence: float = 0.0
    grounding_passed: bool = False
    grounding_failures: list[str] = Field(default_factory=list)

    # ── LLM ──────────────────────────────────────────────────────────────────
    system_prompt: str = ""       # full prompt — enables replay
    user_prompt: str = ""
    raw_llm_response: str = ""
    llm_provider: str = ""
    llm_latency_ms: int = 0

    # ── Response ──────────────────────────────────────────────────────────────
    answer: str = ""
    spoken_text: str = ""
    extracted_entities: dict[str, Any] = Field(default_factory=dict)
    is_fallback: bool = False
    source_count: int = 0
    sources: list[str] = Field(default_factory=list)

    # ── Observability ────────────────────────────────────────────────────────
    total_latency_ms: int = 0
    node_trace: list[dict[str, Any]] = Field(default_factory=list)

    # ── Versioning ────────────────────────────────────────────────────────────
    platform_version: dict[str, str] = Field(
        default_factory=lambda: PlatformVersion.current().model_dump()
    )

    @classmethod
    def from_final_state(
        cls,
        state: dict[str, Any],
        conversation_id: str,
        session_id: str,
        farmer_id: str,
        question: str,
        total_latency_ms: int,
    ) -> "ConversationTurn":
        resp = state.get("final_response")
        evidence = state.get("evidence")
        trace = state.get("trace", [])
        return cls(
            conversation_id=conversation_id,
            session_id=session_id,
            farmer_id=farmer_id,
            question=question,
            intent=state.get("intent", ""),
            intent_confidence=state.get("intent_confidence", 0.0),
            capabilities_used=[r.tool for r in (state.get("tool_results") or []) if r.success],
            evidence_confidence=evidence.overall_confidence if evidence else 0.0,
            grounding_passed=state.get("grounding_passed", False),
            grounding_failures=state.get("grounding_failures", []),
            system_prompt=state.get("system_prompt", ""),
            user_prompt=state.get("user_prompt", ""),
            raw_llm_response=state.get("raw_llm_response", ""),
            llm_provider=state.get("llm_provider", ""),
            llm_latency_ms=state.get("llm_latency_ms", 0),
            answer=resp.answer if resp else "",
            spoken_text=resp.spoken_text if resp and hasattr(resp, "spoken_text") else "",
            extracted_entities=state.get("extracted_entities", {}),
            is_fallback=resp.is_fallback if resp else True,
            source_count=len(resp.sources) if resp else 0,
            sources=[s.source for s in (resp.sources if resp else [])],
            total_latency_ms=total_latency_ms,
            node_trace=[
                {"node": t.node, "duration_ms": t.duration_ms, "success": t.success}
                for t in trace
            ],
        )


async def persist_turn(turn: ConversationTurn) -> None:
    key = f"conversation:{turn.conversation_id}:turns"
    await store_append(key, turn.model_dump())


async def get_turns(conversation_id: str) -> list[ConversationTurn]:
    key = f"conversation:{conversation_id}:turns"
    raw = await store_get(key) or []
    return [ConversationTurn(**t) for t in raw]


async def get_last_n_turns(conversation_id: str, n: int = 5) -> list[ConversationTurn]:
    turns = await get_turns(conversation_id)
    return turns[-n:]
