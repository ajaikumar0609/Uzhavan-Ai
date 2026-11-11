"""
UZHAVAN AI: the single settings module (FP-007 AC-4).

Every entry point reads configuration from here. Validation is fail-closed:
- ENV is required (development | test | production), with no default.
- In production: JWT_SECRET >= 32 chars and not a known placeholder; DATABASE_URL,
  REDIS_URL and CORS_ORIGINS required; ALLOW_ANONYMOUS must be false; OTP_DEV_LOG
  must not be true.
- A missing or invalid setting raises SettingsError naming the variable.

The .env file is loaded from the project root (or ENV_FILE if set) into os.environ
without overriding variables that are already set, so modules that still read
os.getenv at import time (LLM service, RAG engine, voice) see the same values.
Set ENV_FILE=none to disable .env loading (tests do this).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PLACEHOLDER_SECRETS = {
    "change_me_to_a_long_random_string_in_production",
    "change_me",
    "changeme",
    "secret",
    "your-secret-key",
    "test-secret-key-32chars-minimum!!!",
}

DEV_CORS_DEFAULTS = [
    "http://localhost:5173",
    "http://localhost:5180",
    "http://127.0.0.1:5180",
    "http://10.0.2.2:8000",
    "https://localhost",
    "capacitor://localhost",
]


class SettingsError(RuntimeError):
    """Raised at start-up when configuration is missing or unsafe."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # ── Core ────────────────────────────────────────────────────────────────
    ENV: Literal["development", "test", "production"]
    JWT_SECRET: str
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    CORS_ORIGINS: Optional[str] = None
    ALLOW_ANONYMOUS: Optional[bool] = None  # default: true outside production

    # ── Auth / OTP (FP-008) ─────────────────────────────────────────────────
    OTP_DEV_LOG: bool = False
    OTP_HMAC_KEY: Optional[str] = None      # default: derived from JWT_SECRET
    SMS_PROVIDER: Literal["none", "msg91", "twilio"] = "none"
    MSG91_AUTH_KEY: Optional[str] = None
    MSG91_TEMPLATE_ID: Optional[str] = None
    MSG91_SENDER_ID: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    AUTH_DEMO_MODE: bool = False
    DEMO_PHONE_NUMBER: str = "9876543210"
    DEMO_OTP: str = "123456"

    # ── LLM (read by backend/cognitive/llm/service.py) ──────────────────────
    # Zero-paid-API policy: ollama (local Qwen2.5) is the ONLY allowed provider. Any other value
    # (e.g. claude/openai) fails start-up validation; there is no external-AI fallback.
    LLM_PROVIDER: Literal["ollama"] = "ollama"
    OLLAMA_HOST: Optional[str] = None
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_BASE_URL: Optional[str] = None
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct"
    LLM_TIMEOUT_S: float = 60.0

    # ── RAG ─────────────────────────────────────────────────────────────────
    EMBED_MODEL: str = "BAAI/bge-m3"
    CHROMA_PATH: str = "./rag/chroma"
    TOP_K_RETRIEVAL: int = 6
    RAG_SCORE_THRESHOLD: float = 0.35
    KNOWLEDGE_BASE: str = "./knowledge/tnau"

    # ── Versions ────────────────────────────────────────────────────────────
    AI_VERSION: str = "0.1.0"
    GRAPH_VERSION: str = "1.0.0"
    PROMPT_VERSION: str = "1"
    RAG_VERSION: str = "1"
    EMBEDDING_VERSION: str = "1.0"

    # ── Disease / voice ─────────────────────────────────────────────────────
    DISEASE_SERVICE_URL: Optional[str] = None
    DISEASE_TIMEOUT_S: float = 15.0
    # Contract §10: until the M4 model is independently approved, /api/disease/scan
    # answers 503 model_unavailable and never calls the model service.
    DISEASE_MODEL_APPROVED: bool = False
    M4_DEMO_MODE: bool = False
    WHISPER_PROVIDER: str = "browser-only"
    TTS_PROVIDER: str = "browser-only"   # on-device TTS; no cloud TTS is supported

    # ── Data files (read-only project data) ─────────────────────────────────
    UZHAVAN_DATA_DIR: Optional[str] = None   # default: <agri>/uzhavan_data next to the platform

    # ── Feature flags (read by backend/feature_flags.py) ────────────────────
    ENABLE_WEATHER: bool = True
    ENABLE_DISEASE: bool = True
    ENABLE_SCHEMES: bool = True
    ENABLE_MARKET: bool = True   # FP-015: the assistant serves observed FP-011 prices
    ENABLE_SATELLITE: bool = False
    ENABLE_MEMORY: bool = True
    ENABLE_MCP: bool = False
    ENABLE_STREAMING: bool = True

    @field_validator(
        "DATABASE_URL", "REDIS_URL", "CORS_ORIGINS",
        "OTP_HMAC_KEY", "DISEASE_SERVICE_URL",
        "MSG91_AUTH_KEY", "MSG91_TEMPLATE_ID", "MSG91_SENDER_ID",
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER", "OLLAMA_HOST", "UZHAVAN_DATA_DIR",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("ALLOW_ANONYMOUS", mode="before")
    @classmethod
    def _blank_bool(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    # ── Derived ─────────────────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    @property
    def allow_anonymous(self) -> bool:
        if self.ALLOW_ANONYMOUS is None:
            return not self.is_production
        return self.ALLOW_ANONYMOUS

    @property
    def otp_dev_log_enabled(self) -> bool:
        """OTP is logged only when ENV=development AND OTP_DEV_LOG=true."""
        return self.ENV == "development" and self.OTP_DEV_LOG

    @property
    def data_dir(self) -> Path:
        if self.UZHAVAN_DATA_DIR:
            return Path(self.UZHAVAN_DATA_DIR).expanduser()
        return PROJECT_ROOT.parent / "uzhavan_data"

    @property
    def cors_origins(self) -> list[str]:
        if self.CORS_ORIGINS:
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return [] if self.is_production else list(DEV_CORS_DEFAULTS)

    @property
    def otp_hmac_key(self) -> bytes:
        if self.OTP_HMAC_KEY:
            return self.OTP_HMAC_KEY.encode()
        import hashlib
        return hashlib.sha256(b"uzhavan-otp-hmac:" + self.JWT_SECRET.encode()).digest()

    def validate_for_env(self) -> "Settings":
        errors: list[str] = []
        if len(self.JWT_SECRET.strip()) == 0:
            errors.append("JWT_SECRET: must not be empty")
        if self.is_production:
            if len(self.JWT_SECRET) < 32:
                errors.append("JWT_SECRET: must be at least 32 characters in production")
            if self.JWT_SECRET.strip().lower() in PLACEHOLDER_SECRETS or "change_me" in self.JWT_SECRET.lower():
                errors.append("JWT_SECRET: is a known placeholder; generate one with "
                              "python -c \"import secrets;print(secrets.token_urlsafe(48))\"")
            for name in ("DATABASE_URL", "REDIS_URL", "CORS_ORIGINS"):
                if not getattr(self, name):
                    errors.append(f"{name}: required in production")
            if self.ALLOW_ANONYMOUS:
                errors.append("ALLOW_ANONYMOUS: must be false in production")
            if self.OTP_DEV_LOG:
                errors.append("OTP_DEV_LOG: must not be true in production")
            if self.AUTH_DEMO_MODE:
                errors.append("AUTH_DEMO_MODE: must not be true in production")
            if self.M4_DEMO_MODE:
                errors.append("M4_DEMO_MODE: must not be true in production "
                              "(it bypasses the DISEASE_MODEL_APPROVED gate)")
        if errors:
            raise SettingsError("Invalid configuration:\n  - " + "\n  - ".join(errors))
        return self


def _load_env_file() -> None:
    env_file = os.environ.get("ENV_FILE")
    if env_file and env_file.lower() == "none":
        return
    path = Path(env_file) if env_file else PROJECT_ROOT / ".env"
    if path.is_file():
        from dotenv import load_dotenv
        load_dotenv(path, override=False)


def load_settings() -> Settings:
    """Parse and validate settings from the environment. Raises SettingsError."""
    _load_env_file()
    try:
        settings = Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        parts = []
        for err in exc.errors():
            name = ".".join(str(p) for p in err["loc"]) or "?"
            if err["type"] == "missing":
                parts.append(f"{name}: required but not set")
            else:
                parts.append(f"{name}: {err['msg']}")
        raise SettingsError("Invalid configuration:\n  - " + "\n  - ".join(parts)) from None
    return settings.validate_for_env()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()
