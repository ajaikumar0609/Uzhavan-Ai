from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class WeatherData(BaseModel):
    """FP-015: every measured value is optional. A value the provider did not return stays None
    (never a substituted default); consumers must say "not available" instead of guessing."""
    district: str
    date: date
    temp_max_c: float | None = None
    temp_min_c: float | None = None
    temperature_c: float | None = None                   # current conditions only
    humidity_pct: float | None = None
    rain_mm: float | None = None
    description: str | None = None
    description_tamil: str | None = None
    precipitation_probability_pct: float | None = None  # available in forecasts, None for current
    observed_at: str | None = None                       # provider timestamp (current only)


class WeatherContext(BaseModel):
    district: str
    current: WeatherData | None = None
    forecast: list[WeatherData] = []
    irrigation_needed: bool | None = None   # None = cannot be assessed from the data
    irrigation_advice: str | None = None
    irrigation_advice_tamil: str | None = None
