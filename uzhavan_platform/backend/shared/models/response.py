from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backend.shared.models.citation import SourceCitation


class ResponseObject(BaseModel):
    """Final structured response sent to the Conversation Layer and then to the client."""
    answer: str
    spoken_text: str = ""
    language: Literal["Tamil", "English"] = "Tamil"
    intent: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[SourceCitation] = []
    tools_used: list[str] = []
    recommendations: list[str] = []
    warnings: list[str] = []
    next_questions: list[str] = []
    is_fallback: bool = False
    grounded: bool = False   # FP-015 / contract §9: true only for an evidence-grounded, validated answer
    # grounded_verified | grounded_live_data | general_guidance | safety_critical_unverified | "" (fallback)
    grounding_mode: str = ""
