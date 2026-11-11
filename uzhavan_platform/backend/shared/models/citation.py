from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    title: str
    excerpt: str
    confidence: float = Field(ge=0.0, le=1.0)
    page: int | None = None
    url: str | None = None
    category: Literal["rag", "weather", "disease", "market", "scheme", "crop", "satellite"] = "rag"


class SourceCitation(Citation):
    """Serializable citation sent to the client via SSE."""
    pass
