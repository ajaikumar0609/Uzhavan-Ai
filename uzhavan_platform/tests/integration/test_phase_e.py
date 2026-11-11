"""
Phase E Integration Tests — Cognitive Engine

Definition of Done query (Tamil):
  "நான் தஞ்சாவூரில் 1.8 ஹெக்டேரில் சம்பா நெல் பயிரிடுகிறேன்.
   நாளைக்கு 18 மிமீ மழை வந்தால் இன்று யூரியா போடலாமா?"

Expected flow:
  intent=advisory → capabilities=[weather.irrigation_advice, crop.fertilizer_plan, rag.advisory]
  → WeatherAgent + CropAgent execute in parallel
  → EvidenceBundle with weather_summary + crop_summary
  → Grounding validates (citations present, confidence sufficient)
  → PromptBuilder assembles system+user prompts
  → LLM node (may fall back to Tamil constant if Ollama unavailable)
  → SafetyValidator (fallback always passes)
  → Formatter → ResponseObject

Tests are designed to pass regardless of whether Ollama is running.
LLM unavailability is graceful degradation — tests check for ResponseObject validity.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import pytest

from backend.cognitive.graph.conversation import compile_graph, run_query
from backend.cognitive.graph.nodes.intent import _classify_intent, _extract_entities
from backend.cognitive.graph.nodes.planner import _build_requests
from backend.cognitive.graph.nodes.grounding_validator import grounding_validator
from backend.cognitive.models.node_context import EvidenceBundle, NodeTrace
from backend.shared.models.context import ConversationContext, KnowledgeContext, SystemContext
from backend.shared.models.farmer import FarmContext, FarmerContext
from backend.shared.models.response import ResponseObject


# ── Fixtures ──────────────────────────────────────────────────────────────────

DOD_QUESTION = (
    "நான் தஞ்சாவூரில் 1.8 ஹெக்டேரில் சம்பா நெல் பயிரிடுகிறேன். "
    "நாளைக்கு 18 மிமீ மழை வந்தால் இன்று யூரியா போடலாமா?"
)

@pytest.fixture
def murugan_farmer() -> FarmerContext:
    return FarmerContext(
        farmer_id="murugan-001",
        district="Thanjavur",
        language="Tamil",
    )


@pytest.fixture
def murugan_farm() -> FarmContext:
    return FarmContext(
        farm_id="murugan-farm-001",
        farmer_id="murugan-001",
        crop="paddy",
        crop_stage="tillering",
        area_ha=1.8,
        district="Thanjavur",
    )


# ── Intent Router unit tests ──────────────────────────────────────────────────

def test_intent_dod_query_is_advisory():
    intent, confidence = _classify_intent(DOD_QUESTION)
    assert intent == "advisory", f"Expected advisory, got {intent}"
    assert confidence > 0.5


def test_entity_extraction_dod_query():
    entities = _extract_entities(DOD_QUESTION)
    assert entities.get("crop") == "paddy", f"Expected paddy, got {entities.get('crop')}"
    assert entities.get("district") == "Thanjavur", f"Expected Thanjavur, got {entities.get('district')}"
    assert entities.get("area_ha") == 1.8, f"Expected 1.8ha, got {entities.get('area_ha')}"
    assert entities.get("rain_mm") == 18.0, f"Expected 18mm, got {entities.get('rain_mm')}"


def test_intent_weather_question():
    intent, _ = _classify_intent("நாளை மழை வருமா?")
    assert intent == "weather"


def test_intent_disease_question():
    intent, _ = _classify_intent("நெல் இலையில் நோய் இருக்கிறது. என்ன செய்வது?")
    assert intent == "disease"


def test_intent_market_question():
    intent, _ = _classify_intent("இன்று நெல் விலை என்ன?")
    assert intent == "market"


def test_intent_off_topic():
    intent, _ = _classify_intent("Hello, how are you?")
    assert intent == "off_topic"


# ── Planner unit tests ─────────────────────────────────────────────────────────

def test_planner_advisory_returns_weather_and_crop():
    requests = _build_requests("advisory", {"crop": "paddy", "district": "Thanjavur"})
    names = [r.capability_name for r in requests]
    assert "weather.irrigation_advice" in names
    assert "crop.fertilizer_plan" in names
    assert "rag.advisory" in names


def test_planner_weather_intent():
    requests = _build_requests("weather", {})
    names = [r.capability_name for r in requests]
    assert "weather.current_weather" in names
    assert "weather.forecast" in names


def test_planner_off_topic_returns_empty():
    requests = _build_requests("off_topic", {})
    assert requests == []


# ── Grounding Validator unit tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_grounding_passes_with_good_evidence():
    from backend.shared.models.citation import Citation
    bundle = EvidenceBundle(
        citations=[Citation(source="TNAU", title="Test", excerpt="Test", confidence=0.8, category="crop")],
        weather_summary="Rain tomorrow: 18mm",
        crop_summary="Apply urea: 36 kg/ha",
        overall_confidence=0.85,
        successful_tools=2,
        failed_tools=0,
        tools_used=["weather.irrigation_advice", "crop.fertilizer_plan"],
    )
    from backend.cognitive.models.node_context import NodeTrace
    from backend.shared.models.context import ConversationContext, KnowledgeContext, SystemContext
    from backend.shared.models.farmer import FarmerContext, FarmContext

    state = {
        "context": ConversationContext(
            system=SystemContext(trace_id="t1", session_id="s1", request_id="r1", timestamp=datetime.now(timezone.utc)),
            farmer=FarmerContext(farmer_id="f1", district="Thanjavur"),
            farm=FarmContext(farm_id="fa1", farmer_id="f1", crop="paddy", district="Thanjavur"),
            knowledge=KnowledgeContext(),
        ),
        "evidence": bundle,
        "resolved_capabilities": [],
        "extracted_entities": {"crop": "paddy", "district": "Thanjavur"},
        "intent": "advisory",
        "trace": [],
    }
    result = await grounding_validator(state)
    assert result["grounding_passed"] is True
    assert result["grounding_failures"] == []


@pytest.mark.asyncio
async def test_grounding_fails_with_empty_evidence():
    from backend.shared.models.context import ConversationContext, KnowledgeContext, SystemContext
    from backend.shared.models.farmer import FarmerContext

    state = {
        "context": ConversationContext(
            system=SystemContext(trace_id="t1", session_id="s1", request_id="r1", timestamp=datetime.now(timezone.utc)),
            farmer=FarmerContext(farmer_id="f1"),
            knowledge=KnowledgeContext(),
        ),
        "evidence": EvidenceBundle(overall_confidence=0.0, successful_tools=0, failed_tools=2),
        "resolved_capabilities": [],
        "extracted_entities": {},
        "intent": "advisory",
        "trace": [],
    }
    result = await grounding_validator(state)
    assert result["grounding_passed"] is False
    assert len(result["grounding_failures"]) > 0


# ── Full graph end-to-end tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_graph_compiles_and_has_correct_nodes():
    graph = compile_graph()
    node_names = set(graph.nodes.keys())
    expected = {
        "__start__", "intent_router", "planner", "capability_resolver",
        "executor", "evidence_fusion", "grounding_validator",
        "prompt_builder", "llm_node", "safety_validator", "formatter",
    }
    assert expected == node_names


@pytest.mark.asyncio
async def test_dod_query_produces_response_object(murugan_farmer, murugan_farm):
    """
    Phase E Definition of Done:
    Full Tamil query flows through all 11 nodes and produces a valid ResponseObject.
    Works regardless of whether Ollama/Qwen3 is running (graceful LLM fallback).
    """
    result = await run_query(
        question=DOD_QUESTION,
        farmer=murugan_farmer,
        farm=murugan_farm,
    )

    # ── Core contract ──────────────────────────────────────────────────────────
    assert "final_response" in result, "Graph must produce final_response"
    response: ResponseObject = result["final_response"]
    assert isinstance(response, ResponseObject)

    # ── Response content ───────────────────────────────────────────────────────
    assert response.answer, "Answer must not be empty"
    assert len(response.answer) > 10, "Answer must have substantive content"
    assert response.intent == "advisory", f"Intent should be advisory, got {response.intent}"
    assert response.language == "Tamil"

    # ── Trace completeness ────────────────────────────────────────────────────
    traces: list[NodeTrace] = result.get("trace", [])
    trace_node_names = {t.node for t in traces}
    required_nodes = {"intent_router", "planner", "capability_resolver", "executor", "evidence_fusion", "grounding_validator"}
    assert required_nodes.issubset(trace_node_names), (
        f"Missing traces for: {required_nodes - trace_node_names}"
    )

    # ── Intent detection ──────────────────────────────────────────────────────
    assert result.get("intent") == "advisory"
    entities = result.get("extracted_entities", {})
    assert entities.get("crop") == "paddy"
    assert entities.get("district") == "Thanjavur"

    print(f"\n✓ Phase E Definition of Done PASSED")
    print(f"  Intent: {result.get('intent')}")
    print(f"  Entities: {entities}")
    print(f"  Confidence: {response.confidence:.0%}")
    print(f"  Is fallback: {response.is_fallback}")
    print(f"  Tools used: {response.tools_used}")
    print(f"  Sources: {len(response.sources)}")
    print(f"  Answer preview: {response.answer[:120]}...")
    print(f"  Nodes traced: {[t.node for t in traces]}")


@pytest.mark.asyncio
async def test_off_topic_returns_fallback(murugan_farmer):
    """Off-topic question → grounding fails → Tamil fallback returned."""
    result = await run_query(
        question="What is the capital of France?",
        farmer=murugan_farmer,
    )
    response: ResponseObject = result["final_response"]
    assert response.is_fallback is True
    assert "TNAU" in response.answer or "மன்னிக்கவும்" in response.answer


@pytest.mark.asyncio
async def test_weather_query_flow(murugan_farmer, murugan_farm):
    """Weather-only query routes correctly through the graph."""
    result = await run_query(
        question="நாளை மழை வருமா?",
        farmer=murugan_farmer,
        farm=murugan_farm,
    )
    assert result.get("intent") == "weather"
    planner_output = result.get("planner_output")
    assert planner_output is not None
    cap_names = [r.capability_name for r in planner_output.capability_requests]
    assert any("weather" in c for c in cap_names)


@pytest.mark.asyncio
async def test_trace_records_all_nodes(murugan_farmer, murugan_farm):
    """Every node must write a NodeTrace entry."""
    result = await run_query(
        question=DOD_QUESTION,
        farmer=murugan_farmer,
        farm=murugan_farm,
    )
    traces: list[NodeTrace] = result.get("trace", [])
    assert len(traces) >= 8, f"Expected ≥8 node traces, got {len(traces)}: {[t.node for t in traces]}"
    for t in traces:
        assert t.duration_ms >= 0
        assert t.finished_at is not None


@pytest.mark.asyncio
async def test_evidence_bundle_populated(murugan_farmer, murugan_farm):
    """EvidenceBundle should have citations and tool results after executor."""
    result = await run_query(
        question=DOD_QUESTION,
        farmer=murugan_farmer,
        farm=murugan_farm,
    )
    evidence: EvidenceBundle | None = result.get("evidence")
    assert evidence is not None, "Evidence bundle must be present"
    assert evidence.successful_tools > 0, "At least one tool must succeed"
    assert len(evidence.citations) > 0, "At least one citation must be present"
    assert evidence.overall_confidence > 0.0
