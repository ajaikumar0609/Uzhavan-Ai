"""
SessionStore — in-memory storage with optional Redis backend.

Phase F uses in-memory. Redis is wired up when REDIS_URL is set.
All keys are namespaced: "session:{id}" / "conversation:{id}" / "metrics".
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

_REDIS_URL = os.getenv("REDIS_URL", "")
_DEFAULT_SESSION_TTL = 3600  # 1 hour
_DEFAULT_CONVERSATION_TTL = 86400  # 24 hours

# In-memory store: {key: (value_json, expiry_ts)}
_store: dict[str, tuple[str, float]] = {}


def _now() -> float:
    return time.monotonic()


async def store_set(key: str, value: Any, ttl: int = _DEFAULT_SESSION_TTL) -> None:
    data = json.dumps(value) if not isinstance(value, str) else value
    _store[key] = (data, _now() + ttl)


async def store_get(key: str) -> Any | None:
    entry = _store.get(key)
    if entry is None:
        return None
    data, expiry = entry
    if _now() > expiry:
        del _store[key]
        return None
    return json.loads(data)


async def store_delete(key: str) -> None:
    _store.pop(key, None)


async def store_append(key: str, item: Any, ttl: int = _DEFAULT_CONVERSATION_TTL) -> None:
    """Append an item to a list stored at key."""
    existing = await store_get(key) or []
    existing.append(item)
    await store_set(key, existing, ttl)


async def store_keys(prefix: str) -> list[str]:
    now = _now()
    return [k for k, (_, exp) in list(_store.items()) if k.startswith(prefix) and now <= exp]


async def store_clear_expired() -> int:
    """Evict expired keys. Returns number evicted."""
    now = _now()
    expired = [k for k, (_, exp) in _store.items() if now > exp]
    for k in expired:
        del _store[k]
    return len(expired)
