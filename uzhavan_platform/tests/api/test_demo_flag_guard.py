"""Stabilization Sprint 1: demo-flag guard.

Proves production rejects unsafe demo flags, the disease gate stays fail-closed by
default, and development demo output is explicitly labelled research/not certified.
The M4 client is mocked: no model is loaded or run here.
"""
import pytest

from backend.shared.settings import Settings, SettingsError, load_settings
from tests.api.test_settings import PROD_OK, MANAGED  # noqa: F401  (env fixture below)
from tests.helpers import bearer, login

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("ENV_FILE", "none")
    for k in MANAGED + ["M4_DEMO_MODE", "AUTH_DEMO_MODE", "DISEASE_MODEL_APPROVED"]:
        monkeypatch.delenv(k, raising=False)

    def _set(**kw):
        for k, v in kw.items():
            monkeypatch.setenv(k, v)
    return _set


# ── startup guard ────────────────────────────────────────────────────────────
def test_production_rejects_m4_demo_bypass(env):
    env(**PROD_OK, M4_DEMO_MODE="true")
    with pytest.raises(SettingsError, match="M4_DEMO_MODE: must not be true in production"):
        load_settings()


def test_production_rejects_all_unsafe_demo_flags_together(env):
    env(**{**PROD_OK, "ALLOW_ANONYMOUS": "true"}, OTP_DEV_LOG="true",
        AUTH_DEMO_MODE="true", M4_DEMO_MODE="true")
    with pytest.raises(SettingsError) as exc:
        load_settings()
    msg = str(exc.value)
    for name in ("ALLOW_ANONYMOUS", "OTP_DEV_LOG", "AUTH_DEMO_MODE", "M4_DEMO_MODE"):
        assert name in msg


def test_error_message_never_leaks_secret_values(env):
    env(**PROD_OK, M4_DEMO_MODE="true")
    with pytest.raises(SettingsError) as exc:
        load_settings()
    assert PROD_OK["JWT_SECRET"] not in str(exc.value)


def test_production_safe_config_still_loads_and_disease_gate_closed(env):
    env(**PROD_OK)
    s = load_settings()
    assert s.M4_DEMO_MODE is False and s.AUTH_DEMO_MODE is False
    assert s.DISEASE_MODEL_APPROVED is False


def test_development_may_enable_demo_flags(env):
    env(ENV="development", JWT_SECRET="short-dev-secret", M4_DEMO_MODE="true", AUTH_DEMO_MODE="true")
    s = load_settings()
    assert s.M4_DEMO_MODE is True and s.is_production is False


def test_defaults_are_fail_closed():
    s = Settings(ENV="test", JWT_SECRET="x")
    assert s.M4_DEMO_MODE is False
    assert s.AUTH_DEMO_MODE is False
    assert s.DISEASE_MODEL_APPROVED is False


# ── route behaviour ──────────────────────────────────────────────────────────
@pytest.fixture
def mock_m4(monkeypatch):
    calls = {"n": 0}

    async def _ensure(url):
        return None

    async def _infer(**kw):
        calls["n"] += 1
        return {"crop": "groundnut", "predicted_class": "leaf_spot", "predicted_class_id": 1,
                "confidence": 0.9, "top3": [{"class": "leaf_spot", "class_id": 1, "probability": 0.9}],
                "model_architecture": "test", "model_version": "test", "experiment_id": "test",
                "inference_timestamp": "2026-01-01T00:00:00Z", "latency_ms": 1}

    import backend.disease.m4_client as m4
    monkeypatch.setattr(m4, "ensure_m4_server_running", _ensure)
    monkeypatch.setattr(m4, "run_m4_inference", _infer)
    return calls


def _override_settings(api_client, **kw):
    from backend.auth.deps import settings_dep
    from backend.conversation.main import app
    from backend.shared.settings import get_settings
    # Copy of the live test settings (same JWT secret) with only the flags under test changed.
    s = get_settings().model_copy(update=kw)
    app.dependency_overrides[settings_dep] = lambda: s


async def test_dev_demo_output_is_explicitly_research_labelled(api_client, sms_capture, mock_m4):
    tok = (await login(api_client, sms_capture))["access_token"]
    _override_settings(api_client, M4_DEMO_MODE=True)
    r = await api_client.post("/api/disease/scan", headers=bearer(tok),
                              files={"image": ("leaf.jpg", PNG, "image/jpeg")})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "demo_result"
    assert d["demo_mode"] is True
    assert d["production_certified"] is False and d["production_eligible"] is False
    assert "Not Production Certified" in d["meta"]["notes"][0]["en"]
    assert mock_m4["n"] == 1


async def test_production_ignores_demo_bypass_and_stays_closed(api_client, sms_capture, mock_m4):
    tok = (await login(api_client, sms_capture))["access_token"]
    # Settings built directly (bypasses validate_for_env) to prove the route is itself fail-closed.
    _override_settings(api_client, ENV="production", M4_DEMO_MODE=True)
    r = await api_client.post("/api/disease/scan", headers=bearer(tok),
                              files={"image": ("leaf.jpg", PNG, "image/jpeg")})
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "model_unavailable"
    assert mock_m4["n"] == 0


async def test_default_route_state_is_closed(api_client, sms_capture, mock_m4):
    tok = (await login(api_client, sms_capture))["access_token"]
    _override_settings(api_client)
    r = await api_client.post("/api/disease/scan", headers=bearer(tok),
                              files={"image": ("leaf.jpg", PNG, "image/jpeg")})
    assert r.status_code == 503 and mock_m4["n"] == 0
