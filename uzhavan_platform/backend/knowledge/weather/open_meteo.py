from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta, timezone

import httpx

from backend.shared.models.service import ServiceMetadata, ServiceResult
from backend.shared.models.weather import WeatherContext, WeatherData

# Open-Meteo free tier — no API key required
_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_CACHE_TTL_CURRENT_S = 1800   # 30 min
_CACHE_TTL_FORECAST_S = 10800  # 3 hours

# FP-015: the legacy district coordinate table (with its silent Thanjavur fallback) and the
# unverified Tamil WMO strings were removed; locations come from backend/meta.


class WeatherService:
    """
    Data access only. No farming logic.
    Legacy agent-facing API (WeatherAgent) on top of the FP-010 PointWeatherClient.
    WeatherAgent applies all agricultural interpretation.
    """

    VERSION = "1.0"

    def __init__(self, redis_client=None, timeout_s: float = 8.0) -> None:
        self._redis = redis_client
        self._timeout = timeout_s

    async def get_current(self, district: str) -> ServiceResult[WeatherData]:
        """FP-015: backed by the FP-010 PointWeatherClient (raw values; a missing value stays None).
        Unknown district → ValueError (never a substituted location)."""
        start_ns = time.monotonic_ns()
        lat, lon = self._resolve_coords(district)
        res = await self._point().current(lat, lon)
        c = res["data"]
        observed = res.get("observed_at")
        data = WeatherData(
            district=district,
            date=ist_date_of_utc_iso(observed) or ist_date(datetime.now(timezone.utc)),   # D2: IST day
            temperature_c=c.get("temperature_c"),
            humidity_pct=c.get("humidity_pct"),
            rain_mm=c.get("precipitation_mm"),
            description=(c.get("condition") or {}).get("en"),
            description_tamil=None,   # FP-010: no verified Tamil condition strings
            observed_at=observed,
        )
        return ServiceResult(data=data, metadata=ServiceMetadata(
            source="redis-cache" if res.get("cache_hit") else "open-meteo",
            cache_hit=bool(res.get("cache_hit")), latency_ms=self._ms(start_ns)))

    async def get_forecast(self, district: str, days: int = 3) -> ServiceResult[list[WeatherData]]:
        """Daily rows starting TODAY (Open-Meteo convention). Missing values stay None."""
        start_ns = time.monotonic_ns()
        lat, lon = self._resolve_coords(district)
        res = await self._point().daily(lat, lon, days)
        result: list[WeatherData] = []
        for r in res["data"]["daily"]:
            result.append(WeatherData(
                district=district,
                date=date.fromisoformat(r["date"]),
                temp_max_c=r.get("temp_max_c"),
                temp_min_c=r.get("temp_min_c"),
                rain_mm=r.get("precipitation_mm"),
                precipitation_probability_pct=r.get("precipitation_probability_pct"),
                description=(r.get("condition") or {}).get("en"),
                description_tamil=None,
            ))
        return ServiceResult(data=result, metadata=ServiceMetadata(
            source="redis-cache" if res.get("cache_hit") else "open-meteo",
            cache_hit=bool(res.get("cache_hit")), latency_ms=self._ms(start_ns)))

    def _point(self) -> "PointWeatherClient":
        return PointWeatherClient(redis_client=self._redis, timeout_s=self._timeout)

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get("https://api.open-meteo.com/v1/forecast", params={"latitude": 10.787, "longitude": 79.138, "current": "temperature_2m"})
                return r.status_code == 200
        except Exception:
            return False

    def version(self) -> str:
        return self.VERSION

    async def last_updated(self) -> datetime:
        return datetime.now(timezone.utc)

    async def get(self, key: str, **kwargs) -> ServiceResult[WeatherData]:
        return await self.get_current(key)

    async def search(self, query: str, **kwargs) -> ServiceResult[list[WeatherData]]:
        days = kwargs.get("days", 3)
        return await self.get_forecast(query, days)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _resolve_coords(self, district: str) -> tuple[float, float]:
        """District HQ point from backend/meta (38 TN districts). FP-015: an unknown district
        raises instead of silently answering for another place."""
        from backend.meta.catalog import district_id_from_name, get_district

        d = get_district(district_id_from_name(district) or "")
        if d is None:
            raise ValueError(f"Unknown district: {district!r}")
        return (d["lat"], d["lon"])

    async def _get(self, params: dict) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(_OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            return resp.json()

    async def _cache_get(self, key: str) -> str | None:
        if not self._redis:
            return None
        try:
            return await self._redis.get(key)
        except Exception:
            return None

    async def _cache_set(self, key: str, value: str, ttl: int) -> None:
        if not self._redis:
            return
        try:
            await self._redis.setex(key, ttl, value)
        except Exception:
            pass

    @staticmethod
    def _ms(start_ns: int) -> int:
        return int((time.monotonic_ns() - start_ns) / 1_000_000)


# ═══════════════════════════════════════════════════════════════════════════════
# FP-010 point API (used by /api/weather/*). Raw provider values only: no defaults,
# a missing value stays None. Provider failure raises WeatherProviderError (→ 503).
# ═══════════════════════════════════════════════════════════════════════════════

OPEN_METEO_SOURCE_URL = "https://open-meteo.com"

_CURRENT_VARS = (
    "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,"
    "wind_speed_10m,wind_direction_10m,weather_code,is_day"
)
_DAILY_VARS = (
    "temperature_2m_max,temperature_2m_min,precipitation_sum,"
    "precipitation_probability_max,wind_speed_10m_max,weather_code"
)

# WMO weather interpretation codes (WMO 4677 subset documented by Open-Meteo,
# https://open-meteo.com/en/docs). English only: no verified Tamil strings, so ta is null.
WMO_CONDITIONS_EN: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def wmo_condition(code) -> dict:
    if code is None:
        return {"en": None, "ta": None}
    return {"en": WMO_CONDITIONS_EN.get(int(code), f"Unknown weather code {int(code)}"), "ta": None}


class WeatherProviderError(RuntimeError):
    """Open-Meteo unreachable, non-2xx, or a malformed response."""


def _num(values, i=None):
    v = values if i is None else (values[i] if values is not None and i < len(values) else None)
    return None if v is None else float(v)


def _int(values, i=None):
    v = values if i is None else (values[i] if values is not None and i < len(values) else None)
    return None if v is None else int(v)


def _utc_iso_from_gmt(t: str | None) -> str | None:
    """Open-Meteo with timezone=GMT returns 'YYYY-MM-DDTHH:MM' in UTC."""
    if not t:
        return None
    return t + ":00Z" if len(t) == 16 else t


class PointWeatherClient:
    """Current conditions and a daily forecast for a lat/lon point, with a Redis cache
    (current 30 min, forecast 3 h). Cached payloads keep their original retrieved_at."""

    def __init__(self, redis_client=None, timeout_s: float = 8.0, http_client_factory=None, now_fn=None) -> None:
        self._redis = redis_client
        self._timeout = timeout_s
        self._client_factory = http_client_factory or (lambda: httpx.AsyncClient(timeout=self._timeout))
        self._now = now_fn or (lambda: datetime.now(timezone.utc))

    async def current(self, lat: float, lon: float) -> dict:
        key = f"weather:v2:current:{lat:.3f}:{lon:.3f}"
        cached = await self._cache_get(key)
        if cached:
            return json.loads(cached) | {"cache_hit": True}
        raw = await self._fetch({"latitude": lat, "longitude": lon, "current": _CURRENT_VARS,
                                 "timezone": "GMT", "wind_speed_unit": "kmh"})
        c = raw.get("current")
        if not isinstance(c, dict) or "time" not in c:
            raise WeatherProviderError("malformed current response")
        code = _int(c.get("weather_code"))
        is_day = c.get("is_day")
        payload = {
            "data": {
                "temperature_c": _num(c.get("temperature_2m")),
                "apparent_temperature_c": _num(c.get("apparent_temperature")),
                "humidity_pct": _num(c.get("relative_humidity_2m")),
                "precipitation_mm": _num(c.get("precipitation")),
                "wind_speed_kmph": _num(c.get("wind_speed_10m")),
                "wind_direction_deg": _num(c.get("wind_direction_10m")),
                "weather_code": code,
                "condition": wmo_condition(code),
                "is_day": None if is_day is None else bool(is_day),
            },
            "observed_at": _utc_iso_from_gmt(c.get("time")),
            "retrieved_at": _now_iso(),
        }
        await self._cache_set(key, json.dumps(payload), _CACHE_TTL_CURRENT_S)
        return payload | {"cache_hit": False}

    async def daily(self, lat: float, lon: float, days: int) -> dict:
        days = max(1, min(int(days), 7))
        # D2: daily rows are Asia/Kolkata calendar days. The cache key carries the IST date so a
        # payload cached before IST midnight is never served as "today" after midnight.
        ist_today = ist_date(self._now())
        key = f"weather:v2:daily:{ist_today.isoformat()}:{lat:.3f}:{lon:.3f}:{days}"
        cached = await self._cache_get(key)
        if cached:
            return json.loads(cached) | {"cache_hit": True}
        raw = await self._fetch({"latitude": lat, "longitude": lon, "daily": _DAILY_VARS,
                                 "timezone": "Asia/Kolkata", "forecast_days": days, "wind_speed_unit": "kmh"})
        d = raw.get("daily")
        if not isinstance(d, dict) or not isinstance(d.get("time"), list):
            raise WeatherProviderError("malformed daily response")
        rows = []
        for i, day in enumerate(d["time"][:days]):
            code = _int(d.get("weather_code"), i)
            rows.append({
                "date": day,
                "temp_max_c": _num(d.get("temperature_2m_max"), i),
                "temp_min_c": _num(d.get("temperature_2m_min"), i),
                "precipitation_mm": _num(d.get("precipitation_sum"), i),
                "precipitation_probability_pct": _num(d.get("precipitation_probability_max"), i),
                "wind_max_kmph": _num(d.get("wind_speed_10m_max"), i),
                "weather_code": code,
                "condition": wmo_condition(code),
            })
        payload = {"data": {"daily": rows}, "observed_at": None, "retrieved_at": _now_iso()}
        await self._cache_set(key, json.dumps(payload), _CACHE_TTL_FORECAST_S)
        return payload | {"cache_hit": False}

    async def _fetch(self, params: dict) -> dict:
        try:
            async with self._client_factory() as client:
                resp = await client.get(_OPEN_METEO_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise WeatherProviderError(type(exc).__name__) from None
        if not isinstance(data, dict) or data.get("error"):
            raise WeatherProviderError("provider returned an error")
        return data

    async def _cache_get(self, key: str) -> str | None:
        if self._redis is None:
            return None
        try:
            return await self._redis.get(key)
        except Exception:
            return None

    async def _cache_set(self, key: str, value: str, ttl: int) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.setex(key, ttl, value)
        except Exception:
            pass


IST = timezone(timedelta(hours=5, minutes=30))   # India has no DST


def ist_date(moment: datetime) -> date:
    """Calendar date in Asia/Kolkata for an aware (or UTC-naive) datetime."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(IST).date()


def ist_date_of_utc_iso(value: str | None) -> date | None:
    """IST calendar date of an ISO-8601 UTC timestamp such as '2026-09-25T19:00:00Z'."""
    if not value:
        return None
    return ist_date(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
