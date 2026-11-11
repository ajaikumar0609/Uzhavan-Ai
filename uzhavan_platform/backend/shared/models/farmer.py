from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class FarmerContext(BaseModel):
    farmer_id: str
    name: str | None = None
    language: Literal["Tamil", "English"] = "Tamil"
    district: str | None = None
    primary_crop: str | None = None
    phone: str | None = None


class FarmContext(BaseModel):
    farm_id: str
    farmer_id: str
    area_ha: float | None = None
    district: str | None = None
    crop: str | None = None
    crop_stage: str | None = None
    soil_type: str | None = None
    irrigation_type: str | None = None
