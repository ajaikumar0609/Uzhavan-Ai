"""Shared Postgres pool and Redis client for the main app.

Both are created lazily on first use, so the app (and /health) starts even when
Postgres or Redis is down; endpoints that need them return 503 service_unavailable.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from backend.shared.api_errors import service_unavailable
from backend.shared.settings import get_settings

logger = logging.getLogger("uzhavan.db")

_pool = None  # asyncpg.Pool
_pool_lock = asyncio.Lock()
_redis = None  # redis.asyncio.Redis


async def get_pool():
    """Return the shared asyncpg pool, creating it on first use. Raises 503 if unreachable."""
    global _pool
    if _pool is not None:
        return _pool
    async with _pool_lock:
        if _pool is None:
            import asyncpg

            url = get_settings().DATABASE_URL
            if not url:
                raise service_unavailable("Database not configured")
            try:
                _pool = await asyncpg.create_pool(url, min_size=1, max_size=10, timeout=5)
            except (OSError, asyncio.TimeoutError, asyncpg.PostgresError) as exc:
                logger.error("Postgres unavailable: %s", type(exc).__name__)
                raise service_unavailable("Database unavailable") from None
    return _pool


def get_redis_client():
    """Return the shared redis.asyncio client (connects lazily on first command)."""
    global _redis
    if _redis is None:
        import redis.asyncio as aioredis

        url = get_settings().REDIS_URL
        if not url:
            raise service_unavailable("Redis not configured")
        _redis = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=3)
    return _redis


async def close_all() -> None:
    global _pool, _redis
    if _pool is not None:
        await _pool.close()
        _pool = None
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def database_reachable() -> bool:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False


async def redis_reachable() -> bool:
    try:
        return bool(await get_redis_client().ping())
    except Exception:
        return False


def reset_for_tests(redis_client: Optional[object] = None) -> None:
    global _pool, _redis
    _pool = None
    _redis = redis_client
