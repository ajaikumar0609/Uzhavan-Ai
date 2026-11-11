"""FP-007 AC-4: settings validation matrix (fail-closed)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from backend.shared.settings import SettingsError, load_settings

ROOT = Path(__file__).resolve().parents[2]
STRONG = "x7" * 24  # 48 chars
PROD_OK = {
    "ENV": "production",
    "JWT_SECRET": STRONG,
    "DATABASE_URL": "postgresql://u@db/uzhavan",
    "REDIS_URL": "redis://cache:6379/0",
    "CORS_ORIGINS": "https://app.example.org",
    "ALLOW_ANONYMOUS": "false",
}
MANAGED = list(PROD_OK) + ["OTP_DEV_LOG", "LLM_PROVIDER", "ANTHROPIC_API_KEY", "SMS_PROVIDER"]


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("ENV_FILE", "none")
    for k in MANAGED:
        monkeypatch.delenv(k, raising=False)

    def _set(**kw):
        for k, v in kw.items():
            monkeypatch.setenv(k, v)
    return _set


def test_env_missing_is_an_error_naming_env(env):
    env(JWT_SECRET=STRONG)
    with pytest.raises(SettingsError, match="ENV: required"):
        load_settings()


def test_env_invalid_value(env):
    env(ENV="dev", JWT_SECRET=STRONG)
    with pytest.raises(SettingsError, match="ENV"):
        load_settings()


def test_jwt_secret_missing(env):
    env(ENV="development")
    with pytest.raises(SettingsError, match="JWT_SECRET: required"):
        load_settings()


def test_development_defaults_ok(env):
    env(ENV="development", JWT_SECRET="short-dev-secret")
    s = load_settings()
    assert s.allow_anonymous is True
    assert s.otp_dev_log_enabled is False
    assert "https://localhost" in s.cors_origins and "http://localhost:5180" in s.cors_origins


def test_otp_dev_log_only_in_development(env):
    env(ENV="test", JWT_SECRET="x", OTP_DEV_LOG="true")
    assert load_settings().otp_dev_log_enabled is False
    env(ENV="development")
    assert load_settings().otp_dev_log_enabled is True


def test_production_ok(env):
    env(**PROD_OK)
    s = load_settings()
    assert s.is_production and s.allow_anonymous is False
    assert s.cors_origins == ["https://app.example.org"]


@pytest.mark.parametrize("secret", ["change_me_to_a_long_random_string_in_production", "too-short"])
def test_production_rejects_weak_secret(env, secret):
    env(**{**PROD_OK, "JWT_SECRET": secret})
    with pytest.raises(SettingsError, match="JWT_SECRET"):
        load_settings()


@pytest.mark.parametrize("missing", ["DATABASE_URL", "REDIS_URL", "CORS_ORIGINS"])
def test_production_requires(env, monkeypatch, missing):
    env(**PROD_OK)
    monkeypatch.delenv(missing)
    with pytest.raises(SettingsError, match=f"{missing}: required in production"):
        load_settings()


def test_production_rejects_anonymous(env):
    env(**{**PROD_OK, "ALLOW_ANONYMOUS": "true"})
    with pytest.raises(SettingsError, match="ALLOW_ANONYMOUS"):
        load_settings()


def test_production_rejects_otp_dev_log(env):
    env(**PROD_OK, OTP_DEV_LOG="true")
    with pytest.raises(SettingsError, match="OTP_DEV_LOG"):
        load_settings()


@pytest.mark.parametrize("provider", ["claude", "openai", "gemini", "anthropic"])
@pytest.mark.parametrize("environment", ["development", "production"])
def test_external_llm_providers_are_rejected(env, provider, environment):
    """Zero-paid-API policy: only LLM_PROVIDER=ollama is accepted, in every environment."""
    base = PROD_OK if environment == "production" else {"ENV": "development", "JWT_SECRET": STRONG}
    env(**{**base, "LLM_PROVIDER": provider})
    with pytest.raises(SettingsError, match="LLM_PROVIDER"):
        load_settings()


def test_ollama_provider_is_accepted(env):
    env(**PROD_OK, LLM_PROVIDER="ollama")
    assert load_settings().LLM_PROVIDER == "ollama"


def _start_app(extra_env: dict) -> subprocess.CompletedProcess:
    child_env = {k: v for k, v in os.environ.items() if k not in MANAGED}
    child_env.update({"ENV_FILE": "none", **extra_env})
    return subprocess.run(
        [sys.executable, "-c", "import backend.conversation.main"],
        cwd=ROOT, env=child_env, capture_output=True, text=True, timeout=120,
    )


def test_app_refuses_to_start_without_env():
    proc = _start_app({"JWT_SECRET": STRONG})
    assert proc.returncode == 1
    assert "ENV: required but not set" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_app_refuses_production_with_weak_secret():
    proc = _start_app({**PROD_OK, "JWT_SECRET": "change_me_to_a_long_random_string_in_production"})
    assert proc.returncode == 1
    assert "JWT_SECRET" in proc.stderr
