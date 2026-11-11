from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


CropStage = Literal[
    "seedling", "vegetative", "tillering", "flowering",
    "grain_fill", "harvest", "unknown"
]


class CropContext(BaseModel):
    crop_name: str
    crop_name_tamil: str | None = None
    stage: CropStage = "unknown"
    days_after_sowing: int | None = None
    area_ha: float | None = None
    variety: str | None = None
    district: str | None = None


class Scheme(BaseModel):
    scheme_id: str
    name: str
    name_tamil: str | None = None
    description: str
    eligibility: str
    benefit_amount_inr: float | None = None
    application_url: str | None = None
    source: str = "Government of Tamil Nadu"


class SchemeContext(BaseModel):
    applicable_schemes: list[Scheme] = []
