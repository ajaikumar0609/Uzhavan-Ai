from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.shared.models.farmer import FarmerContext, FarmContext
from backend.shared.models.weather import WeatherContext
from backend.shared.models.market import MarketContext
from backend.shared.models.disease import DiseaseContext
from backend.shared.models.crop import CropContext, SchemeContext
from backend.shared.models.memory import ConversationMemory
from backend.shared.models.message import Message


class SystemContext(BaseModel):
    trace_id: str
    session_id: str
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    language: Literal["Tamil", "English"] = "Tamil"


class KnowledgeContext(BaseModel):
    """Aggregated output from all knowledge sources. Populated by EvidenceFusionEngine."""
    rag_chunks: list[Any] = []          # list[Citation]
    weather: WeatherContext | None = None
    disease: DiseaseContext | None = None
    market: MarketContext | None = None
    crop: CropContext | None = None
    schemes: SchemeContext | None = None
    overall_confidence: float = 0.0


class ConversationContext(BaseModel):
    """
    Passed to every agent and every LangGraph node. One object. Everything.
    No agent or node should require data outside this object.
    """
    system: SystemContext
    farmer: FarmerContext
    farm: FarmContext | None = None
    memory: ConversationMemory | None = None
    current_question: str = ""
    conversation_history: list[Message] = []
    knowledge: KnowledgeContext = Field(default_factory=KnowledgeContext)


