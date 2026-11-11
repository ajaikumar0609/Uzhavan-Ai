from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

from backend.shared.models.context import ConversationContext
from backend.shared.models.decision import PlannerOutput, ResolvedCapability
from backend.shared.models.response import ResponseObject
from backend.shared.models.tool import ToolResult

if TYPE_CHECKING:
    from backend.cognitive.models.node_context import EvidenceBundle, NodeTrace


class ConversationState(TypedDict, total=False):
    """
    LangGraph pipeline state. Every node reads from and writes to this.
    Pydantic models are stored as values — LangGraph sees TypedDict, we get type safety.
    """
    # ── Input ────────────────────────────────────────────────────────
    context: ConversationContext        # farmer, farm, system, memory, history
    user_message: str
    disease_context: dict[str, Any] | None
    recent_turns: list[Any]

    # ── Intent ───────────────────────────────────────────────────────
    intent: str                         # advisory|weather|disease|market|scheme|crop|off_topic
    intent_confidence: float
    extracted_entities: dict[str, Any]  # crop, district, date, quantity extracted from message

    # ── Planning ─────────────────────────────────────────────────────
    planner_output: PlannerOutput
    resolved_capabilities: list[ResolvedCapability]  # from Capability Resolver

    # ── Tool Execution ────────────────────────────────────────────────
    tool_results: list[ToolResult]      # one per resolved capability

    # ── Evidence Fusion ───────────────────────────────────────────────
    evidence: Any                       # EvidenceBundle (typed in cognitive layer)
    overall_confidence: float

    # ── Grounding Validation ──────────────────────────────────────────
    grounding_passed: bool
    grounding_failures: list[str]       # which checks failed
    grounding_mode: str                 # grounded_verified | grounded_live_data | general_guidance | safety_critical_unverified
    request_category: str

    # ── Prompt Builder ────────────────────────────────────────────────
    system_prompt: str
    user_prompt: str

    # ── LLM Generation ───────────────────────────────────────────────
    raw_llm_response: str
    llm_provider: str                   # "ollama" | "claude"
    llm_latency_ms: int

    # ── Safety Validation ─────────────────────────────────────────────
    safety_passed: bool
    safety_failures: list[str]

    # ── Final Response ────────────────────────────────────────────────
    final_response: ResponseObject
    is_fallback: bool

    # ── Observability ─────────────────────────────────────────────────
    trace: list[Any]                    # list[NodeTrace], per-node execution records
