from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from backend.shared.models.message import Message


class PastAdvice(BaseModel):
    question: str
    intent: str
    advice: str
    crop: str | None = None
    district: str | None = None
    timestamp: datetime


class ConversationMemory(BaseModel):
    farmer_id: str
    recent_messages: list[Message] = []
    relevant_past_advice: list[PastAdvice] = []
