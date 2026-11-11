"""
Phase F Integration Tests — Session Engine

DoD: Flutter → POST /conversation → JWT → Session → Cognitive Engine
     → SSE events → Persist ConversationTurn → Structured Response

Tests use the ASGI test client (httpx) — no live server needed.
"""
from __future__ import annotations

import json
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.conversation.main import app
from backend.conversation.auth import create_token
from backend.session.history import get_turns
from backend.session.metrics import get_metrics
from backend.session.store import store_clear_expired


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_sse(raw: str) -> list[dict[str, Any]]:
    """
    Parse SSE stream text into list of dicts: {event, data, session_id, conversation_id}.

    Each SSE `data:` line is a serialized SSEEvent object:
      {"event": "...", "session_id": "...", "conversation_id": "...", "data": {...}}
    We promote the inner "data" dict so callers can do event["data"]["answer"] directly.
    """
    events = []
    current_event: dict[str, Any] = {}
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("event:"):
            current_event["event"] = line[len("event:"):].strip()
        elif line.startswith("data:"):
            payload = line[len("data:"):].strip()
            try:
                parsed = json.loads(payload)
                # SSEEvent serializes with a nested "data" dict — unwrap it
                current_event["data"] = parsed.get("data", parsed)
                current_event["session_id"] = parsed.get("session_id", "")
                current_event["conversation_id"] = parsed.get("conversation_id", "")
            except json.JSONDecodeError:
                current_event["data"] = payload
        elif line == "" and current_event:
            events.append(current_event)
            current_event = {}
    if current_event:
        events.append(current_event)
    return events


@pytest.fixture(scope="module")
def farmer_token() -> str:
    return create_token(farmer_id="test_farmer_01", district="Thanjavur")


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


# ── Health / metrics endpoints ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "ai_version" in body["version"]
    assert body["version"]["ai_version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_includes_all_version_fields(client: AsyncClient):
    resp = await client.get("/health")
    v = resp.json()["version"]
    assert "graph_version" in v
    assert "prompt_version" in v
    assert "rag_version" in v
    assert "model" in v


@pytest.mark.asyncio
async def test_metrics_returns_structured_response(client: AsyncClient):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert "total_requests" in body
    assert "avg_latency_ms" in body
    assert "fallback_rate" in body
    assert "intent_distribution" in body


# ── Authentication ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_anonymous_request_allowed_in_dev_mode(client: AsyncClient):
    """ALLOW_ANONYMOUS=true (default in dev) — no token should still work."""
    resp = await client.post(
        "/conversation",
        json={"question": "What is paddy?", "language": "English"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    resp = await client.post(
        "/conversation",
        json={"question": "test"},
        headers={"Authorization": "Bearer not_a_real_token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_valid_jwt_accepted(client: AsyncClient, farmer_token: str):
    resp = await client.post(
        "/conversation",
        json={"question": "What is paddy NPK requirement?", "language": "English"},
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert resp.status_code == 200


# ── SSE event structure ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sse_stream_starts_with_session_started(client: AsyncClient):
    resp = await client.post(
        "/conversation",
        json={"question": "Paddy irrigation advice", "language": "Tamil"},
    )
    events = _parse_sse(resp.text)
    assert len(events) >= 1
    assert events[0]["event"] == "session_started"


@pytest.mark.asyncio
async def test_sse_stream_ends_with_completed(client: AsyncClient):
    resp = await client.post(
        "/conversation",
        json={"question": "What is paddy?", "language": "English"},
    )
    events = _parse_sse(resp.text)
    event_types = [e["event"] for e in events]
    assert "completed" in event_types


@pytest.mark.asyncio
async def test_session_started_event_has_ids(client: AsyncClient):
    resp = await client.post(
        "/conversation",
        json={"question": "Paddy water requirement?", "language": "English"},
    )
    events = _parse_sse(resp.text)
    started = next(e for e in events if e["event"] == "session_started")
    assert "session_id" in started["data"]
    assert "conversation_id" in started["data"]
    assert started["data"]["session_id"] != ""
    assert started["data"]["conversation_id"] != ""


@pytest.mark.asyncio
async def test_completed_event_has_answer(client: AsyncClient):
    resp = await client.post(
        "/conversation",
        json={"question": "What is paddy fertilizer schedule?", "language": "Tamil"},
    )
    events = _parse_sse(resp.text)
    completed = next((e for e in events if e["event"] == "completed"), None)
    assert completed is not None
    assert "answer" in completed["data"]
    assert "session_id" in completed["data"]
    assert "conversation_id" in completed["data"]
    assert "total_latency_ms" in completed["data"]


@pytest.mark.asyncio
async def test_completed_event_has_is_fallback_field(client: AsyncClient):
    resp = await client.post(
        "/conversation",
        json={"question": "Paddy NPK requirement?", "language": "Tamil"},
    )
    events = _parse_sse(resp.text)
    completed = next((e for e in events if e["event"] == "completed"), None)
    assert completed is not None
    assert "is_fallback" in completed["data"]


@pytest.mark.asyncio
async def test_no_error_event_on_valid_query(client: AsyncClient):
    resp = await client.post(
        "/conversation",
        json={"question": "Paddy irrigation in Thanjavur?", "language": "Tamil"},
    )
    events = _parse_sse(resp.text)
    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 0


# ── Session continuity ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_session_id_reuse_increments_turn_count(client: AsyncClient):
    # First turn — no session_id
    resp1 = await client.post(
        "/conversation",
        json={"question": "First question about paddy", "language": "English"},
    )
    events1 = _parse_sse(resp1.text)
    started1 = next(e for e in events1 if e["event"] == "session_started")
    sid = started1["data"]["session_id"]
    turn1 = started1["data"]["turn"]

    # Second turn — reuse session_id
    resp2 = await client.post(
        "/conversation",
        json={"question": "Second question about urea", "session_id": sid, "language": "English"},
    )
    events2 = _parse_sse(resp2.text)
    started2 = next(e for e in events2 if e["event"] == "session_started")
    assert started2["data"]["session_id"] == sid
    assert started2["data"]["turn"] == turn1 + 1


# ── Conversation persistence ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_conversation_turn_persisted_after_request(client: AsyncClient):
    resp = await client.post(
        "/conversation",
        json={"question": "Paddy basal fertilizer timing?", "language": "English"},
    )
    events = _parse_sse(resp.text)
    completed = next((e for e in events if e["event"] == "completed"), None)
    assert completed is not None

    conversation_id = completed["data"]["conversation_id"]
    turns = await get_turns(conversation_id)
    assert len(turns) >= 1
    assert turns[0].question == "Paddy basal fertilizer timing?"
    assert turns[0].conversation_id == conversation_id


@pytest.mark.asyncio
async def test_persisted_turn_has_platform_version(client: AsyncClient):
    resp = await client.post(
        "/conversation",
        json={"question": "What soil is best for paddy?", "language": "English"},
    )
    events = _parse_sse(resp.text)
    completed = next((e for e in events if e["event"] == "completed"), None)
    cid = completed["data"]["conversation_id"]

    turns = await get_turns(cid)
    assert len(turns) >= 1
    pv = turns[0].platform_version
    assert "ai_version" in pv
    assert pv["ai_version"] == "0.1.0"


# ── DoD Query ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dod_query_full_pipeline(client: AsyncClient, farmer_token: str):
    """
    Phase F DoD:
    Flutter → POST /conversation → JWT → Session → Cognitive Engine
           → SSE events → Persist ConversationTurn → Structured Response

    Query: Tamil advisory with rain+urea question.
    """
    question = (
        "நான் தஞ்சாவூரில் 1.8 ஹெக்டேரில் சம்பா நெல் பயிரிடுகிறேன். "
        "நாளைக்கு 18 மிமீ மழை வந்தால் இன்று யூரியா போடலாமா?"
    )
    resp = await client.post(
        "/conversation",
        json={"question": question, "language": "Tamil"},
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    event_types = [e["event"] for e in events]

    # Must start with session lifecycle
    assert "session_started" in event_types

    # Must end with completed
    assert "completed" in event_types

    # Must not have unhandled errors
    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 0

    # Completed event must carry a non-empty answer
    completed = next(e for e in events if e["event"] == "completed")
    assert completed["data"].get("answer", "") != ""

    # Conversation must be persisted
    cid = completed["data"]["conversation_id"]
    turns = await get_turns(cid)
    assert len(turns) >= 1
    assert turns[0].question == question

    # Metrics must be updated
    snapshot = get_metrics().snapshot()
    assert snapshot.total_requests >= 1
