"""Shared test fixtures for UZHAVAN AI test suite.

Tests run with ENV=test and do NOT load the developer .env (ENV_FILE=none).
Auth/profile/farm tests use an in-memory repository and fakeredis, so no external
service is required. tests/api/test_postgres_integration.py additionally exercises the
real local Postgres when it is reachable.
"""

import os

# Set required env vars before any app import (the settings module validates at import).
os.environ["ENV_FILE"] = "none"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-32chars-minimum!!!")
os.environ.setdefault("DATABASE_URL", "postgresql://ajaikumarn@127.0.0.1:5432/uzhavan_dev")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/15")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from tests.fakes import CapturingSmsProvider, InMemoryDiaryStore, InMemoryRepository  # noqa: E402


@pytest.fixture
def memory_repo() -> InMemoryRepository:
    return InMemoryRepository()


@pytest_asyncio.fixture
async def fake_redis():
    import fakeredis

    r = fakeredis.FakeAsyncRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest.fixture
def sms_capture() -> CapturingSmsProvider:
    return CapturingSmsProvider()


@pytest.fixture
def diary_store() -> InMemoryDiaryStore:
    return InMemoryDiaryStore()


@pytest_asyncio.fixture
async def api_client(memory_repo, fake_redis, sms_capture, diary_store):
    """Main app (backend/conversation/main.py) with in-memory DB, fakeredis and a capturing SMS provider.
    Diary uses an in-memory store; other data stores are overridden per test module."""
    from backend.auth.deps import get_redis, get_repository, get_repository_factory, get_sms_provider
    from backend.conversation.main import app
    from backend.diary.store import get_diary_store, get_diary_store_factory

    async def _repo():
        return memory_repo

    async def _diary():
        return diary_store

    app.dependency_overrides[get_repository] = _repo
    app.dependency_overrides[get_repository_factory] = lambda: _repo
    app.dependency_overrides[get_diary_store] = _diary
    app.dependency_overrides[get_diary_store_factory] = lambda: _diary
    app.dependency_overrides[get_redis] = lambda: fake_redis
    app.dependency_overrides[get_sms_provider] = lambda: sms_capture
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


PG_DSN = "postgresql://ajaikumarn@127.0.0.1:5432/uzhavan_dev"


@pytest_asyncio.fixture
async def temp_schema():
    """A throwaway Postgres schema with empty copies of the loader tables (skips if Postgres is down)."""
    import secrets

    asyncpg = pytest.importorskip("asyncpg")
    try:
        conn = await asyncpg.connect(PG_DSN, timeout=3)
    except Exception:
        pytest.skip("local Postgres not reachable")
    schema = "t_loader_" + secrets.token_hex(4)
    await conn.execute(f"CREATE SCHEMA {schema}")
    for t in ("mandi_prices", "data_sources", "government_schemes"):
        await conn.execute(f"CREATE TABLE {schema}.{t} (LIKE public.{t} INCLUDING ALL)")
    yield schema, conn
    await conn.execute(f"DROP SCHEMA {schema} CASCADE")
    await conn.close()
