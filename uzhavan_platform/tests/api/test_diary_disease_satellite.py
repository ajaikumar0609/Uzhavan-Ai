"""Contract §8 (diary + auto-log), §10 (disease 503 model_unavailable), §11 (satellite status)."""
from datetime import date, timedelta

import pytest

from backend.diary.store import auto_log
from tests.helpers import bearer, login

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


# ── Diary ────────────────────────────────────────────────────────────────────
async def test_diary_requires_auth(api_client):
    assert (await api_client.get("/api/diary")).status_code == 401
    r = await api_client.post("/api/diary", json={"kind": "note", "text": "x", "entry_date": "2026-09-25"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "unauthenticated"


async def test_diary_post_and_list(api_client, sms_capture):
    tok = (await login(api_client, sms_capture))["access_token"]
    today = date.today().isoformat()
    r = await api_client.post("/api/diary", headers=bearer(tok),
                              json={"kind": "expense", "text": "Urea 2 bags", "amount_inr": 600, "entry_date": today})
    assert r.status_code == 201, r.text
    e = r.json()["data"]
    assert e["kind"] == "expense" and e["amount_inr"] == 600 and e["entry_date"] == today and e["ref"] is None
    r = await api_client.post("/api/diary", headers=bearer(tok),
                              json={"kind": "note", "text": "Field flooded", "entry_date": today})
    assert r.status_code == 201
    r = await api_client.get("/api/diary?limit=1", headers=bearer(tok))
    assert r.status_code == 200 and len(r.json()["data"]) == 1
    r = await api_client.get("/api/diary", headers=bearer(tok))
    assert {e["kind"] for e in r.json()["data"]} == {"expense", "note"}


@pytest.mark.parametrize("body,code", [
    ({"kind": "question", "text": "q"}, "invalid_kind"),
    ({"kind": "scan", "text": "q"}, "invalid_kind"),
    ({"kind": "note", "text": "   "}, "invalid_text"),
    ({"kind": "note", "text": "x" * 1001}, "invalid_text"),
    ({"kind": "note", "text": "x", "amount_inr": 5}, "amount_not_allowed"),
    ({"kind": "income", "text": "x", "amount_inr": -1}, "invalid_amount"),
])
async def test_diary_validation(api_client, sms_capture, body, code):
    tok = (await login(api_client, sms_capture))["access_token"]
    r = await api_client.post("/api/diary", headers=bearer(tok), json={**body, "entry_date": date.today().isoformat()})
    assert r.status_code == 400 and r.json()["detail"]["code"] == code


async def test_diary_future_date_and_foreign_farm(api_client, sms_capture, memory_repo):
    tok = (await login(api_client, sms_capture))["access_token"]
    future = (date.today() + timedelta(days=5)).isoformat()
    r = await api_client.post("/api/diary", headers=bearer(tok), json={"kind": "note", "text": "x", "entry_date": future})
    assert r.json()["detail"]["code"] == "invalid_entry_date"
    other, _ = await memory_repo.upsert_farmer_by_phone("9111111111")
    farm = await memory_repo.create_farm(other["farmer_id"], {"name": "F", "district_id": "thanjavur"})
    r = await api_client.post("/api/diary", headers=bearer(tok),
                              json={"kind": "note", "text": "x", "farm_id": farm["farm_id"], "entry_date": date.today().isoformat()})
    assert r.status_code == 404


async def test_auto_log_skips_anonymous_and_swallows_errors(diary_store):
    async def factory():
        return diary_store
    await auto_log(factory, "anonymous", "question", "q")
    await auto_log(factory, "f1", "note", "not an auto kind")
    assert diary_store.entries == []

    async def broken():
        raise RuntimeError("db down")
    await auto_log(broken, "f1", "question", "q")  # must not raise


async def test_conversation_logs_question_with_token(api_client, sms_capture, diary_store, monkeypatch):
    from backend.conversation.routes import conversation as conv

    async def fake_stream(request, farmer_id):
        yield "data: {}\n\n"
    monkeypatch.setattr(conv, "_stream_conversation", fake_stream)

    r = await api_client.post("/conversation", json={"question": "anonymous question"})
    assert r.status_code == 200 and diary_store.entries == []

    tok = (await login(api_client, sms_capture))["access_token"]
    r = await api_client.post("/conversation", headers=bearer(tok), json={"question": "நெல்லுக்கு எந்த உரம்?"})
    assert r.status_code == 200
    assert [(e["kind"], e["text"]) for e in diary_store.entries] == [("question", "நெல்லுக்கு எந்த உரம்?")]


# ── Disease (§10) ────────────────────────────────────────────────────────────
@pytest.fixture
def no_model_call(monkeypatch):
    from backend.knowledge.disease.client import DiseaseService

    async def boom(*a, **k):
        raise AssertionError("model service must not be called")
    monkeypatch.setattr(DiseaseService, "predict_bytes", boom)
    monkeypatch.setattr(DiseaseService, "predict", boom)


async def test_disease_scan_model_unavailable_and_logged(api_client, sms_capture, diary_store, no_model_call):
    tok = (await login(api_client, sms_capture))["access_token"]
    r = await api_client.post("/api/disease/scan", headers=bearer(tok),
                              files={"image": ("leaf.png", PNG, "image/png")}, data={"crop_id": "paddy"})
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "model_unavailable"
    assert [(e["kind"], e["text"]) for e in diary_store.entries] == [("scan", "scan submitted")]


async def test_disease_scan_anonymous_not_logged(api_client, diary_store, no_model_call):
    r = await api_client.post("/api/disease/scan", files={"image": ("leaf.jpg", PNG, "image/jpeg")})
    assert r.status_code == 503 and r.json()["detail"]["code"] == "model_unavailable"
    assert diary_store.entries == []


async def test_disease_scan_validation(api_client, diary_store, no_model_call):
    r = await api_client.post("/api/disease/scan", files={"image": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 415 and r.json()["detail"]["code"] == "unsupported_media_type"
    big = b"0" * (10 * 1024 * 1024 + 1)
    r = await api_client.post("/api/disease/scan", files={"image": ("a.jpg", big, "image/jpeg")})
    assert r.status_code == 413 and r.json()["detail"]["code"] == "image_too_large"
    r = await api_client.post("/api/disease/scan", files={"image": ("a.jpg", PNG, "image/jpeg")}, data={"crop_id": "rose"})
    assert r.status_code == 400 and r.json()["detail"]["code"] == "invalid_crop"
    assert diary_store.entries == []


async def test_disease_setting_defaults_false():
    from backend.shared.settings import Settings
    assert Settings(ENV="test", JWT_SECRET="x").DISEASE_MODEL_APPROVED is False


# ── Satellite (§11) ──────────────────────────────────────────────────────────
async def test_satellite_status_exact(api_client):
    r = await api_client.get("/api/satellite/status")
    assert r.status_code == 200
    assert r.json()["data"] == {
        "available": False, "reason": "under_validation",
        "gates": {"licence": False, "units": False, "geography_scope": "Cauvery Delta only",
                  "independent_evaluation": "baseline only (val, 14 plots)"},
    }
