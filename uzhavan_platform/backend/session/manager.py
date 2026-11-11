"""
SessionManager — session lifecycle for UZHAVAN AI.

Session lifecycle:
  create() → session_id
  get(session_id) → Session
  update() → persists context changes
  expire() → invalidate

Sessions survive across multiple conversation turns.
ConversationContext is rebuilt for each turn using stored FarmerContext + FarmContext.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from backend.session.store import store_delete, store_get, store_set
from backend.shared.models.farmer import FarmContext, FarmerContext

_SESSION_TTL = 3600  # 1 hour idle timeout


class Session(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    farmer_id: str
    farmer: FarmerContext
    farm: FarmContext | None = None
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_active: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    turn_count: int = 0
    active: bool = True


class SessionManager:
    async def create(
        self,
        farmer: FarmerContext,
        farm: FarmContext | None = None,
    ) -> Session:
        session = Session(farmer_id=farmer.farmer_id, farmer=farmer, farm=farm)
        await store_set(f"session:{session.session_id}", session.model_dump(), ttl=_SESSION_TTL)
        return session

    async def get(self, session_id: str) -> Session | None:
        data = await store_get(f"session:{session_id}")
        if data is None:
            return None
        return Session(**data)

    async def update(self, session: Session) -> None:
        session.last_active = datetime.now(timezone.utc).isoformat()
        await store_set(f"session:{session.session_id}", session.model_dump(), ttl=_SESSION_TTL)

    async def new_turn(self, session: Session) -> Session:
        """Increment turn counter and optionally rotate conversation_id."""
        session.turn_count += 1
        session.last_active = datetime.now(timezone.utc).isoformat()
        await self.update(session)
        return session

    async def expire(self, session_id: str) -> None:
        await store_delete(f"session:{session_id}")


# Module-level singleton
_manager = SessionManager()


def get_session_manager() -> SessionManager:
    return _manager
