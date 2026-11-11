"""
UZHAVAN AI — Shared Domain Contracts
Every inter-layer communication uses these models. Never pass raw dicts between layers.
"""
from backend.shared.models.citation import Citation, SourceCitation
from backend.shared.models.service import ServiceMetadata, ServiceResult
from backend.shared.models.context import ConversationContext, KnowledgeContext, SystemContext
from backend.shared.models.conversation import ConversationState
from backend.shared.models.crop import CropContext, CropStage, Scheme, SchemeContext
from backend.shared.models.decision import (
    CapabilityRequest,
    Decision,
    PlannerOutput,
    ResolvedCapability,
)
from backend.shared.models.disease import DiseaseContext, DiseaseResult, TNAUGuidance
from backend.shared.models.events import (
    DeltaEvent,
    DoneEvent,
    ErrorEvent,
    MetaEvent,
    SourcesEvent,
    SSEEventType,
    SuggestionsEvent,
)
from backend.shared.models.farmer import FarmContext, FarmerContext
from backend.shared.models.market import MarketContext, MarketPrice, PriceTrend
from backend.shared.models.memory import ConversationMemory, PastAdvice
from backend.shared.models.message import Message
from backend.shared.models.response import ResponseObject
from backend.shared.models.tool import AgentManifest, ToolCapability, ToolResult
from backend.shared.models.weather import WeatherContext, WeatherData

__all__ = [
    # Citation
    "Citation",
    "SourceCitation",
    # Context
    "ConversationContext",
    "KnowledgeContext",
    "SystemContext",
    # Conversation / State
    "ConversationState",
    "Message",
    # Crop
    "CropContext",
    "CropStage",
    "Scheme",
    "SchemeContext",
    # Decision
    "CapabilityRequest",
    "Decision",
    "PlannerOutput",
    "ResolvedCapability",
    # Disease
    "DiseaseContext",
    "DiseaseResult",
    "TNAUGuidance",
    # Events (SSE)
    "DeltaEvent",
    "DoneEvent",
    "ErrorEvent",
    "MetaEvent",
    "SourcesEvent",
    "SSEEventType",
    "SuggestionsEvent",
    # Farmer
    "FarmContext",
    "FarmerContext",
    # Market
    "MarketContext",
    "MarketPrice",
    "PriceTrend",
    # Memory
    "ConversationMemory",
    "PastAdvice",
    # Response
    "ResponseObject",
    # Tool
    "AgentManifest",
    "ToolCapability",
    "ToolResult",
    # Weather
    "WeatherContext",
    "WeatherData",
    # Service
    "ServiceMetadata",
    "ServiceResult",
]
