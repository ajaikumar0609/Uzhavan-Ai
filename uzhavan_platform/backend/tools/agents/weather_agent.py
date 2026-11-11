from __future__ import annotations

import time
from datetime import timedelta
from typing import Any

from backend.knowledge.weather.open_meteo import WeatherService
from backend.shared.agents.base import BaseDomainAgent
from backend.shared.models.citation import Citation
from backend.shared.models.context import ConversationContext
from backend.shared.models.tool import AgentManifest, ToolCapability, ToolResult
from backend.shared.models.weather import WeatherContext, WeatherData


class WeatherAgent(BaseDomainAgent):
    """
    Owns all agricultural reasoning about weather.
    Delegates raw data fetching to WeatherService — never calls OpenMeteo directly.
    """

    VERSION = "1.0"
    _CAPABILITIES = [
        "current_weather", "forecast", "rain_alert",
        "irrigation_advice", "spray_suitability",
    ]

    def __init__(self, service: WeatherService | None = None) -> None:
        self._service = service or WeatherService()

    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_name="weather",
            version=self.VERSION,
            description="Real-time and forecast weather with agricultural interpretation for Tamil Nadu districts",
            avg_latency_ms=300,
            typical_confidence=0.92,
            feature_flag="ENABLE_WEATHER",
            dependencies=["open-meteo", "postgresql"],
            capabilities=[
                ToolCapability(name="current_weather", description="Current temperature, humidity, rainfall for a district", avg_latency_ms=200),
                ToolCapability(name="forecast", description="3-7 day weather forecast with daily breakdown", avg_latency_ms=250),
                ToolCapability(name="rain_alert", description="Alert if significant rainfall expected in next 48 hours", avg_latency_ms=250),
                ToolCapability(name="irrigation_advice", description="Should farmer irrigate today? Based on crop stage + weather", avg_latency_ms=300),
                ToolCapability(name="spray_suitability", description="Is it safe to spray pesticides today?", avg_latency_ms=300),
            ],
        )

    def can_handle(self, capability_name: str) -> bool:
        parts = capability_name.split(".", 1)
        return len(parts) == 2 and parts[0] == "weather" and parts[1] in self._CAPABILITIES

    async def execute(
        self, capability_name: str, context: ConversationContext, params: dict[str, Any]
    ) -> ToolResult:
        start_ns = time.monotonic_ns()
        _, method = capability_name.split(".", 1)
        # FP-015: no default district (was "Chennai"). Unknown → an honest failure.
        district = params.get("district") or (context.farm.district if context.farm else None) or context.farmer.district
        if not district:
            return self._timed_result(capability_name, start_ns, False,
                                      error="district unknown: weather needs the farm or farmer district")
        try:
            if method == "current_weather":
                return await self._current_weather(start_ns, district)
            elif method == "forecast":
                days = int(params.get("days", 3))
                return await self._forecast(start_ns, district, days)
            elif method == "rain_alert":
                threshold_mm = float(params.get("threshold_mm", 10.0))
                return await self._rain_alert(start_ns, district, threshold_mm)
            elif method == "irrigation_advice":
                crop = params.get("crop") or (context.farm.crop if context.farm else None)
                stage = params.get("crop_stage") or (context.farm.crop_stage if context.farm else None)
                return await self._irrigation_advice(start_ns, district, crop, stage)
            elif method == "spray_suitability":
                return await self._spray_suitability(start_ns, district)
            else:
                return self._timed_result(capability_name, start_ns, False, error=f"Unknown method: {method}")
        except NotImplementedError:
            return self._timed_result(capability_name, start_ns, False, error="Weather service not yet implemented (Phase D)")
        except Exception as exc:
            return self._timed_result(capability_name, start_ns, False, error=str(exc))

    async def _current_weather(self, start_ns: int, district: str) -> ToolResult:
        svc_result = await self._service.get_current(district)
        weather = svc_result.data if hasattr(svc_result, "data") else svc_result
        ctx = WeatherContext(
            district=district,
            current=weather,
            irrigation_needed=self._needs_irrigation(weather),
        )
        temp = weather.temperature_c if weather.temperature_c is not None else weather.temp_max_c
        excerpt = (f"{_v(weather.description, '')}. Temperature: {_v(temp, ' °C')}, "
                   f"Rain: {_v(weather.rain_mm, ' mm')}, Humidity: {_v(weather.humidity_pct, ' %')}"
                   + (f" (observed {weather.observed_at})" if weather.observed_at else ""))
        citation = Citation(
            source="Open-Meteo",
            title=f"Current Weather — {district}",
            excerpt=excerpt,
            confidence=0.95,
            category="weather",
        )
        return self._timed_result("weather.current_weather", start_ns, True, data=ctx, citations=[citation], confidence=0.95)

    async def _forecast(self, start_ns: int, district: str, days: int) -> ToolResult:
        svc_result = await self._service.get_forecast(district, days)
        forecast = svc_result.data if hasattr(svc_result, "data") else svc_result
        ctx = WeatherContext(district=district, forecast=forecast)
        citations = [
            Citation(
                source="Open-Meteo",
                title=f"Forecast {d.date} — {district}",
                excerpt=(f"{d.date}: {_v(d.description, '')}, max {_v(d.temp_max_c, ' °C')}, "
                         f"min {_v(d.temp_min_c, ' °C')}, rain {_v(d.rain_mm, ' mm')}, "
                         f"rain probability {_v(d.precipitation_probability_pct, ' %')}"),
                confidence=max(0.95 - i * 0.05, 0.70),  # confidence decreases with forecast days
                category="weather",
            )
            for i, d in enumerate(forecast)
        ]
        return self._timed_result("weather.forecast", start_ns, True, data=ctx, citations=citations, confidence=0.88)

    async def _rain_alert(self, start_ns: int, district: str, threshold_mm: float) -> ToolResult:
        svc_result = await self._service.get_forecast(district, days=2)
        forecast = svc_result.data if hasattr(svc_result, "data") else svc_result
        heavy_rain_days = [d for d in forecast if d.rain_mm is not None and d.rain_mm >= threshold_mm]
        unknown_days = [str(d.date) for d in forecast if d.rain_mm is None]
        facts = [f"Forecast rain on {d.date}: {_v(d.rain_mm, ' mm')} (Open-Meteo)" for d in forecast]
        alert_data = {
            "alert": len(heavy_rain_days) > 0,
            "district": district,
            "heavy_rain_days": [{"date": str(d.date), "rain_mm": d.rain_mm} for d in heavy_rain_days],
            "days_without_rain_data": unknown_days,
            "message_tamil": self._rain_alert_message_tamil(heavy_rain_days, district, bool(unknown_days) or not forecast),
            "facts": facts,
        }
        confidence = 0.90 if forecast else 0.0
        return self._timed_result("weather.rain_alert", start_ns, True, data=alert_data, confidence=confidence)

    async def _irrigation_advice(self, start_ns: int, district: str, crop: str | None, stage: str | None) -> ToolResult:
        curr_result = await self._service.get_current(district)
        fcast_result = await self._service.get_forecast(district, days=3)
        current = curr_result.data if hasattr(curr_result, "data") else curr_result
        forecast = fcast_result.data if hasattr(fcast_result, "data") else fcast_result
        advice = self._compute_irrigation_advice(current, forecast, crop, stage)
        data = {
            "irrigate_today": advice["irrigate"],
            "reason": advice["reason"],
            "advice_tamil": advice["advice_tamil"],
            "quantity_mm": advice.get("quantity_mm"),
            "crop": crop,
            "crop_stage": stage,
            "district": district,
            "facts": [advice["reason"]],
        }
        citation = Citation(
            source="TNAU + Open-Meteo",
            title=f"Irrigation Advice — {crop or 'crop unknown'} ({stage or 'stage unknown'})",
            excerpt=advice["reason"],
            confidence=0.85,
            category="weather",
        )
        return self._timed_result("weather.irrigation_advice", start_ns, True, data=data, citations=[citation], confidence=0.85)

    async def _spray_suitability(self, start_ns: int, district: str) -> ToolResult:
        svc_result = await self._service.get_current(district)
        current = svc_result.data if hasattr(svc_result, "data") else svc_result
        suitable, reason, reason_tamil = self._assess_spray_conditions(current)
        data = {
            "suitable": suitable,
            "reason": reason,
            "reason_tamil": reason_tamil,
            "humidity_pct": current.humidity_pct,
            "rain_mm": current.rain_mm,
            "facts": [reason],
        }
        return self._timed_result("weather.spray_suitability", start_ns, True, data=data, confidence=0.88)

    # ── Agricultural reasoning ────────────────────────────────────────────────

    def _needs_irrigation(self, weather: WeatherData) -> bool | None:
        """Basic irrigation need assessment; None when rain or humidity is not available."""
        if weather.rain_mm is None or weather.humidity_pct is None:
            return None
        return weather.rain_mm < 5.0 and weather.humidity_pct < 70.0

    def _compute_irrigation_advice(
        self,
        current: WeatherData,
        forecast: list[WeatherData],
        crop: str | None,
        stage: str | None,
    ) -> dict[str, Any]:
        """
        Tamil Nadu crop water requirement reasoning.
        Rules sourced from TNAU Crop Production Guide (crop-specific ETc values).
        FP-015: never computes from a missing value — rain/crop/stage unknown → irrigate=None.
        """
        rain_today = current.rain_mm
        tomorrow = current.date + timedelta(days=1)
        rain_tomorrow = next((d.rain_mm for d in forecast if d.date == tomorrow), None)
        facts = f"Rain today: {_v(rain_today, ' mm')}; forecast rain tomorrow ({tomorrow}): {_v(rain_tomorrow, ' mm')} (Open-Meteo)."

        # If significant rain today: skip irrigation
        if rain_today is not None and rain_today >= 10.0:
            return {
                "irrigate": False,
                "reason": f"Rainfall today ({rain_today}mm) is sufficient. Skip irrigation. {facts}",
                "advice_tamil": f"இன்று {rain_today}மிமீ மழை பெய்தது. நீர்ப்பாசனம் தேவையில்லை.",
                "quantity_mm": 0,
            }

        # If heavy rain forecast tomorrow: skip today
        if rain_tomorrow is not None and rain_tomorrow >= 15.0:
            return {
                "irrigate": False,
                "reason": f"Heavy rain forecast tomorrow ({rain_tomorrow}mm). Hold irrigation. {facts}",
                "advice_tamil": f"நாளை {rain_tomorrow}மிமீ மழை எதிர்பார்க்கப்படுகிறது. நீர்ப்பாசனம் நிறுத்தவும்.",
                "quantity_mm": 0,
            }

        crop_water_mm = self._crop_daily_water_need(crop, stage)
        if rain_today is None or crop_water_mm is None:
            missing = []
            if rain_today is None:
                missing.append("today's rainfall")
            if crop_water_mm is None:
                missing.append("the crop and crop stage" if not (crop and stage) else f"a TNAU water need for {crop} at {stage}")
            return {
                "irrigate": None,
                "reason": f"Irrigation need cannot be calculated: {' and '.join(missing)} not available. {facts}",
                "advice_tamil": "நீர்ப்பாசன தேவையை கணக்கிட தேவையான தகவல் கிடைக்கவில்லை.",
                "quantity_mm": None,
            }

        effective_rain = min(rain_today, crop_water_mm)
        deficit_mm = max(0, crop_water_mm - effective_rain)

        if deficit_mm <= 2.0:
            return {
                "irrigate": False,
                "reason": f"Water deficit ({deficit_mm:.1f}mm) is within tolerance. No irrigation needed. {facts}",
                "advice_tamil": f"நீர் தேவை ({deficit_mm:.1f}மிமீ) குறைவாக உள்ளது. நீர்ப்பாசனம் தேவையில்லை.",
                "quantity_mm": 0,
            }

        return {
            "irrigate": True,
            "reason": f"Apply {deficit_mm:.0f}mm irrigation for {crop} in {stage} stage. {facts}",
            "advice_tamil": f"{crop} ({stage}) பயிருக்கு {deficit_mm:.0f}மிமீ நீர்ப்பாசனம் செய்யவும்.",
            "quantity_mm": round(deficit_mm, 1),
        }

    def _crop_daily_water_need(self, crop: str | None, stage: str | None) -> float | None:
        """
        Reference ETc values for major Tamil Nadu crops.
        Source: TNAU Crop Production Guide (irrigated conditions).
        FP-015: unknown crop or stage → None (no generic 4 mm default).
        """
        _water_needs: dict[str, dict[str, float]] = {
            "paddy": {"seedling": 5.0, "vegetative": 7.0, "tillering": 8.0, "flowering": 6.0, "grain_fill": 4.0, "harvest": 2.0},
            "rice": {"seedling": 5.0, "vegetative": 7.0, "tillering": 8.0, "flowering": 6.0, "grain_fill": 4.0, "harvest": 2.0},
            "cotton": {"vegetative": 4.0, "flowering": 6.0, "grain_fill": 5.0},
            "banana": {"vegetative": 5.0, "flowering": 6.5, "harvest": 4.0},
            "sugarcane": {"vegetative": 5.0, "tillering": 6.0, "grand_growth": 7.0, "harvest": 4.0},
            "groundnut": {"vegetative": 3.5, "flowering": 5.0, "grain_fill": 4.0},
            "maize": {"vegetative": 4.0, "flowering": 5.5, "grain_fill": 4.5},
            "tomato": {"vegetative": 3.0, "flowering": 4.5, "fruit_development": 4.0},
        }
        if not crop or not stage:
            return None
        return _water_needs.get(crop.lower(), {}).get(stage.lower())

    def _assess_spray_conditions(self, weather: WeatherData) -> tuple[bool | None, str, str]:
        """
        Pesticide spray suitability based on TNAU spray guidelines.
        Avoid spraying: humidity >80%, rain forecast, wind >15km/h.
        """
        if weather.rain_mm is not None and weather.rain_mm > 0:
            return False, "Rain today — spray will be washed off.", "இன்று மழை உள்ளது — மருந்து கழுவப்படும். தெளிக்க வேண்டாம்."
        if weather.humidity_pct is not None and weather.humidity_pct > 80.0:
            return False, f"Humidity too high ({weather.humidity_pct}%) — poor spray effectiveness.", f"ஈரப்பதம் அதிகம் ({weather.humidity_pct}%) — மருந்து பலனற்றதாகும்."
        if weather.rain_mm is None or weather.humidity_pct is None:
            return (None, "Spray suitability cannot be assessed: current rain or humidity is not available.",
                    "மழை அல்லது ஈரப்பதம் தகவல் கிடைக்கவில்லை; தெளிப்பு நிலையை மதிப்பிட முடியாது.")
        return True, "Good conditions for spraying. Apply early morning (before 9 AM).", "தெளிப்பதற்கு நல்ல நிலை. காலை 9 மணிக்கு முன் தெளிக்கவும்."

    def _rain_alert_message_tamil(self, heavy_days: list[WeatherData], district: str, data_missing: bool = False) -> str:
        if not heavy_days and data_missing:
            return f"{district}-க்கான மழை முன்னறிவிப்பு தகவல் முழுமையாக கிடைக்கவில்லை."
        if not heavy_days:
            return f"{district}-ல் அடுத்த 48 மணி நேரத்தில் கனமழை எதிர்பார்க்கப்படவில்லை."
        day = heavy_days[0]
        return f"{district}-ல் {day.date} அன்று {day.rain_mm:.0f}மிமீ மழை எதிர்பார்க்கப்படுகிறது. நீர்ப்பாசனம் நிறுத்தவும்."

    async def health(self) -> bool:
        return await self._service.health()


def _v(value: Any, unit: str) -> str:
    """Render a provider value; a missing value is stated as not available (never defaulted)."""
    return "not available" if value is None else f"{value}{unit}"
