from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from backend.shared.models.citation import SourceCitation


class DeltaEvent(BaseModel):
    event: Literal["delta"] = "delta"
    data: str  # LLM token chunk


class SourcesEvent(BaseModel):
    event: Literal["sources"] = "sources"
    data: list[SourceCitation]


class MetaEvent(BaseModel):
    event: Literal["meta"] = "meta"
    data: dict[str, Any]  # intent, confidence, tools_used


class SuggestionsEvent(BaseModel):
    event: Literal["suggestions"] = "suggestions"
    data: list[str]  # 3 follow-up questions in farmer's language


class DoneEvent(BaseModel):
    event: Literal["done"] = "done"
    data: dict[str, Any] = {}


class ErrorEvent(BaseModel):
    event: Literal["error"] = "error"
    data: str


SSEEventType = DeltaEvent | SourcesEvent | MetaEvent | SuggestionsEvent | DoneEvent | ErrorEvent
