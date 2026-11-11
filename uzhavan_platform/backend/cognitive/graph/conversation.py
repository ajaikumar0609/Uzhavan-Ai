"""
UZHAVAN Cognitive Engine — Root LangGraph Graph

11-node pipeline:
  Intent Router → Planner → Capability Resolver → Executor →
  Evidence Fusion → Grounding Validator →
    [grounding passed] → Prompt Builder → LLM Node → Safety Validator → Formatter
    [grounding failed] → Formatter (fallback)

The LLM appears exactly once. Everything before it is deterministic.
Everything after it is validation and formatting.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from backend.cognitive.graph.nodes.capability_resolver import capability_resolver
from backend.cognitive.graph.nodes.evidence_fusion import evidence_fusion
from backend.cognitive.graph.nodes.executor import executor
from backend.cognitive.graph.nodes.formatter import formatter
from backend.cognitive.graph.nodes.grounding_validator import grounding_validator
from backend.cognitive.graph.nodes.intent import intent_router
from backend.cognitive.graph.nodes.llm_node import llm_node
from backend.cognitive.graph.nodes.planner import planner
from backend.cognitive.graph.nodes.prompt_builder import prompt_builder
from backend.cognitive.graph.nodes.safety_validator import safety_validator
from backend.shared.models.context import ConversationContext, SystemContext
from backend.shared.models.conversation import ConversationState
from backend.shared.models.farmer import FarmerContext


def _route_after_grounding(state: dict[str, Any]) -> str:
    """Conditional edge: grounding passed → prompt_builder; failed → formatter."""
    return "prompt_builder" if state.get("grounding_passed") else "formatter"


def _route_after_safety(state: dict[str, Any]) -> str:
    """Safety always flows to formatter — formatter reads safety_passed to decide content."""
    return "formatter"


def build_graph() -> StateGraph:
    graph = StateGraph(ConversationState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    graph.add_node("intent_router", intent_router)
    graph.add_node("planner", planner)
    graph.add_node("capability_resolver", capability_resolver)
    graph.add_node("executor", executor)
    graph.add_node("evidence_fusion", evidence_fusion)
    graph.add_node("grounding_validator", grounding_validator)
    graph.add_node("prompt_builder", prompt_builder)
    graph.add_node("llm_node", llm_node)
    graph.add_node("safety_validator", safety_validator)
    graph.add_node("formatter", formatter)

    # ── Edges (linear) ─────────────────────────────────────────────────────────
    graph.set_entry_point("intent_router")
    graph.add_edge("intent_router", "planner")
    graph.add_edge("planner", "capability_resolver")
    graph.add_edge("capability_resolver", "executor")
    graph.add_edge("executor", "evidence_fusion")
    graph.add_edge("evidence_fusion", "grounding_validator")

    # ── Conditional: grounding gate ────────────────────────────────────────────
    graph.add_conditional_edges(
        "grounding_validator",
        _route_after_grounding,
        {"prompt_builder": "prompt_builder", "formatter": "formatter"},
    )

    graph.add_edge("prompt_builder", "llm_node")
    graph.add_edge("llm_node", "safety_validator")
    graph.add_edge("safety_validator", "formatter")
    graph.add_edge("formatter", END)

    return graph


def compile_graph():
    """Compile the LangGraph StateGraph into an executable graph."""
    return build_graph().compile()


# ── Entry point ───────────────────────────────────────────────────────────────

async def run_query(
    question: str,
    farmer: FarmerContext,
    farm=None,
    memory=None,
    session_id: str | None = None,
) -> ConversationState:
    """
    Primary entry point for the Cognitive Engine.

    Usage:
        result = await run_query(
            question="நாளை மழை வருமா?",
            farmer=FarmerContext(farmer_id="f1", district="Thanjavur"),
        )
        print(result["final_response"].answer)
    """
    from backend.shared.models.context import KnowledgeContext

    graph = compile_graph()
    session_id = session_id or str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    context = ConversationContext(
        system=SystemContext(
            trace_id=trace_id,
            session_id=session_id,
            request_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
        ),
        farmer=farmer,
        farm=farm,
        memory=memory,
        current_question=question,
        knowledge=KnowledgeContext(),
    )

    initial_state: ConversationState = {
        "context": context,
        "user_message": question,
        "trace": [],
    }

    result = await graph.ainvoke(initial_state)
    return result


def export_graph_visualization(output_dir: str = ".") -> dict[str, str]:
    """
    Generate graph.mmd (Mermaid) and optionally graph.png.
    Returns dict of {format: file_path} for files successfully written.
    """
    import os
    graph = build_graph()
    compiled = graph.compile()
    outputs: dict[str, str] = {}

    # Mermaid diagram (always available)
    try:
        mmd = compiled.get_graph().draw_mermaid()
        mmd_path = os.path.join(output_dir, "graph.mmd")
        with open(mmd_path, "w") as f:
            f.write(mmd)
        outputs["mermaid"] = mmd_path
    except Exception:
        pass

    # PNG (requires graphviz)
    try:
        png_bytes = compiled.get_graph().draw_mermaid_png()
        png_path = os.path.join(output_dir, "graph.png")
        with open(png_path, "wb") as f:
            f.write(png_bytes)
        outputs["png"] = png_path
    except Exception:
        pass

    return outputs
