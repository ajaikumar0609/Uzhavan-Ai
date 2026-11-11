"""
Unit and integration tests for UZHAVAN Conversational Voice Assistant.

Covers:
1. Spoken Response Planner (markdown removal, bullet expansion, unit expansion, safety preservation)
2. Emotion & Conversational State Analyzer (worried, confused, urgent, informational)
3. Multi-turn conversational context understanding (e.g., "45 நாள்" follow-up resolving to previous paddy crop)
4. Spoken text integration in ResponseObject and SSE stream
"""
from __future__ import annotations

import pytest

from backend.cognitive.voice.spoken_planner import plan_spoken_response
from backend.cognitive.voice.emotion_analyzer import analyze_conversational_state
from backend.cognitive.graph.nodes.intent import intent_router, _extract_entities, _classify_intent
from backend.session.history import ConversationTurn
from backend.shared.models.context import ConversationContext, KnowledgeContext, SystemContext
from backend.shared.models.farmer import FarmContext, FarmerContext
from backend.shared.models.response import ResponseObject


def test_spoken_planner_strips_markdown_and_citations():
    raw = (
        "## நெல் இலை மஞ்சள் நோய் ஆலோசனை\n"
        "**பரிந்துரை:**\n"
        "- 18 மிமீ மழை பெய்யும் வாய்ப்பு உள்ளது.\n"
        "- 1.8 ha நிலத்திற்கு [TNAU] உரம் இடவும்.\n"
        "- மேலும் விவரங்களுக்கு https://agritech.tnau.ac.in பார்க்கவும்.\n"
        "[Farm: Crop: paddy, Area: 1.8 ha]\n"
        "```json\n{'status': 'ok'}\n```"
    )
    spoken = plan_spoken_response(raw, language="Tamil")

    # Assertions
    assert "##" not in spoken
    assert "**" not in spoken
    assert "https://" not in spoken
    assert "```" not in spoken
    assert "[TNAU]" not in spoken
    assert "[Farm:" not in spoken
    assert "18 மில்லிமீட்டர்" in spoken
    assert "1.8 ஹெக்டேர்" in spoken
    assert "முதலில், " in spoken or "அடுத்ததாக, " in spoken


def test_spoken_planner_english_units_and_bullets():
    raw = (
        "### Weather and Irrigation Advice\n"
        "* 25mm rain is expected tomorrow.\n"
        "* Apply 50kg urea per ha.\n"
        "* Check soil moisture first."
    )
    spoken = plan_spoken_response(raw, language="English")

    assert "###" not in spoken
    assert "*" not in spoken
    assert "25 millimeters" in spoken
    assert "50 kilograms" in spoken
    assert "First, " in spoken
    assert "Next, " in spoken


def test_spoken_planner_replaces_bureaucratic_tamil():
    raw = "பின்வரும் பரிந்துரைகளை கடைப்பிடிக்கவும்: 1. இலைகளை சரிபார்க்கவும். அச்சம் கொள்ளத் தேவையில்லை."
    spoken = plan_spoken_response(raw, language="Tamil")

    assert "பின்வரும் பரிந்துரைகளை கடைப்பிடிக்கவும்" not in spoken
    assert "அச்சம் கொள்ளத் தேவையில்லை" not in spoken
    assert "கவலைப்படாதீங்க" in spoken


def test_emotion_analyzer_worried_farmer():
    text = "அண்ணா என் நெல்லு இலை எல்லாம் மஞ்சளா ஆகுது என்ன பண்ணுறதுன்னே தெரியல கவலையா இருக்கு"
    tone = analyze_conversational_state(text)

    assert tone.state == "worried"
    assert "ஆறுதலளிக்கும்" in tone.guidance_ta or "கவலைப்படாதீங்க" in tone.guidance_ta


def test_emotion_analyzer_confused_farmer():
    text = "எனக்கு இது சுத்தமா புரியல எப்படி செய்யணும்னு சொல்லுங்க"
    tone = analyze_conversational_state(text)

    assert tone.state == "confused"
    assert "படிப்படியாக" in tone.guidance_ta


def test_emotion_analyzer_urgent_farmer():
    text = "நோய் உடனே முழுக்க பரவுது அவசரம் காப்பாத்துங்க"
    tone = analyze_conversational_state(text)

    assert tone.state == "urgent"
    assert "உடனடி" in tone.guidance_ta or "எச்சரிக்கை" in tone.guidance_ta


def test_emotion_analyzer_informational():
    text = "தஞ்சாவூரில் நாளை மழை வருமா?"
    tone = analyze_conversational_state(text)

    assert tone.state == "informational"


@pytest.mark.asyncio
async def test_multiturn_context_understanding():
    """
    Farmer Turn 1: "என் நெல்லில் இலை மஞ்சளா இருக்கு." -> disease intent, crop=paddy
    Farmer Turn 2: "45 நாள்." -> without context it is off_topic, with context it resolves to disease on paddy!
    """
    # Simulate prior turn in session
    turn1 = ConversationTurn(
        conversation_id="conv-123",
        session_id="sess-123",
        farmer_id="farmer-1",
        question="என் நெல்லில் இலை மஞ்சளா இருக்கு.",
        intent="disease",
        intent_confidence=0.9,
        answer="புரிகிறது. இது எந்த வயது பயிர்?",
        extracted_entities={"crop": "paddy"},
    )

    ctx = ConversationContext(
        system=SystemContext(trace_id="t1", session_id="sess-123", request_id="r1"),
        farmer=FarmerContext(farmer_id="farmer-1", district="Thanjavur"),
        farm=None,  # No explicit farm record, context comes from dialog
        current_question="45 நாள்.",
    )

    state = {
        "context": ctx,
        "user_message": "45 நாள்.",
        "recent_turns": [turn1],
        "trace": [],
    }

    result = await intent_router(state)

    assert result["intent"] == "disease", f"Should inherit disease intent, got {result['intent']}"
    assert result["extracted_entities"].get("crop") == "paddy", "Should inherit paddy crop from prior turn"
    assert result["extracted_entities"].get("crop_age_days") == 45, "Should extract 45 days crop age"
    assert result["intent_confidence"] >= 0.8
