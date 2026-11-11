"""
NodeContext and EvidenceBundle — the backbone of the Cognitive Engine.

Every node in the LangGraph pipeline communicates through ConversationState (TypedDict).
NodeContext is the rich, Pydantic-typed view that nodes construct from state to do their work.

Nodes only modify their own section. This is the compiler-pipeline invariant.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from backend.shared.models.citation import Citation
from backend.shared.models.context import ConversationContext
from backend.shared.models.decision import PlannerOutput, ResolvedCapability
from backend.shared.models.response import ResponseObject
from backend.shared.models.tool import ToolResult


class EvidenceBundle(BaseModel):
    """
    Output of the Evidence Fusion Engine.
    All downstream nodes (GroundingValidator, PromptBuilder, Formatter) read from this.
    """
    citations: list[Citation] = []
    weather_summary: str | None = None
    crop_summary: str | None = None
    disease_summary: str | None = None
    market_summary: str | None = None
    scheme_summary: str | None = None
    rag_excerpts: list[str] = []
    # FP-015: factual lines from the tools (values with their source/date, or "not available"),
    # and the TNAU/RAG chunks that were actually retrieved (the only valid `sources`).
    facts: list[str] = []
    retrieved_chunks: list[Citation] = []
    overall_confidence: float = 0.0
    tools_used: list[str] = []
    conflict_warnings: list[str] = []
    successful_tools: int = 0
    failed_tools: int = 0


class NodeTrace(BaseModel):
    """Single node execution record. Appended to the trace list by each node."""
    node: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    duration_ms: int = 0
    success: bool = True
    error: str | None = None


class NodeContext(BaseModel):
    """
    Typed view of ConversationState for use inside node functions.
    Nodes call NodeContext.from_state(state) → do work → return partial state dict.
    Decouples node logic from LangGraph's TypedDict requirements.
    """
    # ── Immutable (set at graph entry) ──────────────────────────────────────
    conversation: ConversationContext

    # ── Intent Router ────────────────────────────────────────────────────────
    intent: str = ""
    intent_confidence: float = 0.0
    extracted_entities: dict[str, Any] = Field(default_factory=dict)

    # ── Planner ──────────────────────────────────────────────────────────────
    plan: PlannerOutput | None = None

    # ── Capability Resolver ──────────────────────────────────────────────────
    resolved_capabilities: list[ResolvedCapability] = Field(default_factory=list)

    # ── Executor ─────────────────────────────────────────────────────────────
    tool_results: list[ToolResult] = Field(default_factory=list)

    # ── Evidence Fusion ──────────────────────────────────────────────────────
    evidence: EvidenceBundle | None = None

    # ── Grounding Validator ──────────────────────────────────────────────────
    grounding_passed: bool | None = None
    grounding_failures: list[str] = Field(default_factory=list)

    # ── Prompt Builder ───────────────────────────────────────────────────────
    system_prompt: str = ""
    user_prompt: str = ""

    # ── LLM Node ─────────────────────────────────────────────────────────────
    raw_llm_response: str = ""
    llm_provider: str = ""
    llm_latency_ms: int = 0

    # ── Safety Validator ─────────────────────────────────────────────────────
    safety_passed: bool | None = None
    safety_failures: list[str] = Field(default_factory=list)

    # ── Formatter ────────────────────────────────────────────────────────────
    final_response: ResponseObject | None = None
    is_fallback: bool = False

    # ── Observability ────────────────────────────────────────────────────────
    trace: list[NodeTrace] = Field(default_factory=list)

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "NodeContext":
        return cls(
            conversation=state["context"],
            intent=state.get("intent", ""),
            intent_confidence=state.get("intent_confidence", 0.0),
            extracted_entities=state.get("extracted_entities", {}),
            plan=state.get("planner_output"),
            resolved_capabilities=state.get("resolved_capabilities", []),
            tool_results=state.get("tool_results", []),
            evidence=state.get("evidence"),
            grounding_passed=state.get("grounding_passed"),
            grounding_failures=state.get("grounding_failures", []),
            system_prompt=state.get("system_prompt", ""),
            user_prompt=state.get("user_prompt", ""),
            raw_llm_response=state.get("raw_llm_response", ""),
            llm_provider=state.get("llm_provider", ""),
            llm_latency_ms=state.get("llm_latency_ms", 0),
            safety_passed=state.get("safety_passed"),
            safety_failures=state.get("safety_failures", []),
            final_response=state.get("final_response"),
            is_fallback=state.get("is_fallback", False),
            trace=state.get("trace", []),
        )

    def to_state_patch(self) -> dict[str, Any]:
        """Return only the fields that are set, as a partial ConversationState dict."""
        patch: dict[str, Any] = {}
        if self.intent:
            patch["intent"] = self.intent
        if self.intent_confidence:
            patch["intent_confidence"] = self.intent_confidence
        if self.extracted_entities:
            patch["extracted_entities"] = self.extracted_entities
        if self.plan is not None:
            patch["planner_output"] = self.plan
        if self.resolved_capabilities:
            patch["resolved_capabilities"] = self.resolved_capabilities
        if self.tool_results:
            patch["tool_results"] = self.tool_results
        if self.evidence is not None:
            patch["evidence"] = self.evidence
        if self.grounding_passed is not None:
            patch["grounding_passed"] = self.grounding_passed
        if self.grounding_failures:
            patch["grounding_failures"] = self.grounding_failures
        if self.system_prompt:
            patch["system_prompt"] = self.system_prompt
        if self.user_prompt:
            patch["user_prompt"] = self.user_prompt
        if self.raw_llm_response:
            patch["raw_llm_response"] = self.raw_llm_response
        if self.llm_provider:
            patch["llm_provider"] = self.llm_provider
        if self.llm_latency_ms:
            patch["llm_latency_ms"] = self.llm_latency_ms
        if self.safety_passed is not None:
            patch["safety_passed"] = self.safety_passed
        if self.safety_failures:
            patch["safety_failures"] = self.safety_failures
        if self.final_response is not None:
            patch["final_response"] = self.final_response
        if self.is_fallback:
            patch["is_fallback"] = self.is_fallback
        if self.trace:
            patch["trace"] = self.trace
        return patch
