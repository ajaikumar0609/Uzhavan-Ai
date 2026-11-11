"""
SSE Event Model for UZHAVAN AI Streaming.

Every SSE message is a typed event — never a raw string.
Flutter reads event type and shows contextual loading states:
  "Checking weather..." / "Searching TNAU..." / "Generating answer..."

Wire format (text/event-stream):
  event: intent_detected
  data: {"event":"intent_detected","session_id":"...","data":{"intent":"advisory"}}

"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SSEEventType(str, Enum):
    SESSION_STARTED = "session_started"
    INTENT_DETECTED = "intent_detected"
    PLANNING = "planning"
    TOOL_COMPLETE = "tool_complete"
    EVIDENCE_READY = "evidence_ready"
    GROUNDING = "grounding"
    REASONING = "reasoning"
    RESPONSE_COMPLETE = "response_complete"
    SOURCES = "sources"
    COMPLETED = "completed"
    ERROR = "error"


class SSEEvent(BaseModel):
    event: SSEEventType
    session_id: str
    conversation_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict[str, Any] = Field(default_factory=dict)


def format_sse(event: SSEEvent) -> str:
    """Encode as SSE wire format with double-newline terminator."""
    payload = event.model_dump_json()
    return f"event: {event.event.value}\ndata: {payload}\n\n"


def format_keepalive() -> str:
    """Heartbeat comment to prevent proxy timeouts."""
    return ": keepalive\n\n"


# ── Node name → SSE event type mapping ───────────────────────────────────────

_NODE_TO_EVENT: dict[str, SSEEventType] = {
    "intent_router": SSEEventType.INTENT_DETECTED,
    "planner": SSEEventType.PLANNING,
    "capability_resolver": SSEEventType.PLANNING,
    "executor": SSEEventType.TOOL_COMPLETE,
    "evidence_fusion": SSEEventType.EVIDENCE_READY,
    "grounding_validator": SSEEventType.GROUNDING,
    "prompt_builder": SSEEventType.REASONING,
    "llm_node": SSEEventType.RESPONSE_COMPLETE,
    "safety_validator": SSEEventType.RESPONSE_COMPLETE,
    "formatter": SSEEventType.RESPONSE_COMPLETE,
}

# ── Node output → SSE data extractor ─────────────────────────────────────────

def _extract_event_data(node_name: str, node_output: dict[str, Any]) -> dict[str, Any]:
    """Pull the relevant fields from a node output for the SSE payload."""
    if node_name == "intent_router":
        return {
            "intent": node_output.get("intent", ""),
            "confidence": node_output.get("intent_confidence", 0),
            "entities": node_output.get("extracted_entities", {}),
        }
    if node_name == "planner":
        plan = node_output.get("planner_output")
        caps = []
        if plan and hasattr(plan, "capability_requests"):
            caps = [r.capability_name for r in plan.capability_requests]
        return {"capabilities_requested": caps}
    if node_name == "executor":
        results = node_output.get("tool_results", [])
        return {
            "tools_run": [r.tool for r in results],
            "succeeded": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
        }
    if node_name == "evidence_fusion":
        evidence = node_output.get("evidence")
        if evidence:
            return {
                "tools_used": evidence.tools_used,
                "confidence": evidence.overall_confidence,
                "citations": len(evidence.citations),
            }
    if node_name == "grounding_validator":
        return {
            "passed": node_output.get("grounding_passed", False),
            "failures": node_output.get("grounding_failures", []),
        }
    if node_name == "llm_node":
        return {
            "provider": node_output.get("llm_provider", ""),
            "latency_ms": node_output.get("llm_latency_ms", 0),
            "is_fallback": node_output.get("is_fallback", False),
        }
    if node_name == "formatter":
        resp = node_output.get("final_response")
        if resp:
            return {
                "is_fallback": resp.is_fallback,
                "confidence": resp.confidence,
                "tools_used": resp.tools_used,
                "source_count": len(resp.sources),
            }
    return {}


def node_to_sse_event(
    node_name: str,
    node_output: dict[str, Any],
    session_id: str,
    conversation_id: str,
) -> SSEEvent | None:
    """Convert a LangGraph node completion into an SSE event. Returns None for silent nodes."""
    event_type = _NODE_TO_EVENT.get(node_name)
    if event_type is None:
        return None
    return SSEEvent(
        event=event_type,
        session_id=session_id,
        conversation_id=conversation_id,
        data=_extract_event_data(node_name, node_output),
    )
