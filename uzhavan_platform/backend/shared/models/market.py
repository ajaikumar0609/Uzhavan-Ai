from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


class MarketPrice(BaseModel):
    crop: str
    district: str
    price_inr_per_quintal: float
    date: date
    market_name: str | None = None
    source: str = "AGMARKNET"


class PriceTrend(BaseModel):
    crop: str
    direction: Literal["up", "down", "stable"]
    change_pct: float
    days: int
    recommendation: str | None = None
    recommendation_tamil: str | None = None


class MarketContext(BaseModel):
    prices: list[MarketPrice] = []
    trend: PriceTrend | None = None
