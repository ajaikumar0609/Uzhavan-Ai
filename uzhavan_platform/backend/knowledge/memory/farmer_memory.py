from __future__ import annotations

from backend.shared.models.memory import ConversationMemory, PastAdvice


class MemoryService:
    """
    ai_memory table read/write. No knowledge of agents, LangGraph, or LLM.
    Phase D: implement with asyncpg queries against the ai_memory table
    created in migration 004.
    """

    async def recall(self, farmer_id: str, intent: str, limit: int = 5) -> ConversationMemory:
        raise NotImplementedError("Phase D: implement ai_memory recall query")

    async def save(self, farmer_id: str, advice: PastAdvice) -> None:
        raise NotImplementedError("Phase D: implement ai_memory save")

    async def health(self) -> bool:
        return False
