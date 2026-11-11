from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DiseaseResult(BaseModel):
    disease_label: str
    crop: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Literal["low", "medium", "high"]
    image_path: str | None = None


class TNAUGuidance(BaseModel):
    disease_label: str
    crop: str
    symptoms: str
    chemical_control: str | None = None
    biological_control: str | None = None
    cultural_practices: str | None = None
    source: str = "TNAU Plant Protection Manual"
    source_tamil: str | None = None


class DiseaseContext(BaseModel):
    result: DiseaseResult | None = None
    guidance: TNAUGuidance | None = None
