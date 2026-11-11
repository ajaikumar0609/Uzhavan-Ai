"""
Phase D Milestone Integration Test
===================================
Validates the core query WITHOUT any LLM call:

  "Will tomorrow's rain affect my paddy irrigation in Thanjavur?"

Pipeline exercised:
  MockWeatherService → WeatherAgent.irrigation_advice()
  CropKnowledgeService → WeatherAgent._crop_daily_water_need()
  ToolResult → verifiable, structured output

This test proves domain services work independently before being connected to LangGraph.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timezone
from typing import Any

import pytest

from backend.knowledge.crop.service import CropKnowledgeService
from backend.shared.models import (
    ConversationContext,
    FarmContext,
    FarmerContext,
    SystemContext,
    WeatherData,
    ServiceMetadata,
    ServiceResult,
)
from backend.tools.agents.weather_agent import WeatherAgent


# ── Mock weather service (no internet required) ─────────────────────────────

class MockWeatherService:
    """
    Deterministic weather service for testing.
    Simulates: no rain today, 18mm rain forecast tomorrow for Thanjavur.
    This is the scenario where WeatherAgent should advise: skip irrigation today.
    Returns ServiceResult[T] to match real WeatherService interface.
    """

    def __init__(self, current_rain_mm: float = 0.0, forecast_rain_mm: float = 18.0) -> None:
        self._current_rain = current_rain_mm
        self._forecast_rain = forecast_rain_mm

    async def get_current(self, district: str) -> ServiceResult[WeatherData]:
        data = WeatherData(
            district=district,
            date=date.today(),
            temp_max_c=32.0,
            temp_min_c=24.0,
            humidity_pct=72.0,
            rain_mm=self._current_rain,
            description="Partly cloudy",
            description_tamil="பகுதியளவு மேக மூட்டம்",
        )
        return ServiceResult(data=data, metadata=ServiceMetadata(source="mock", cache_hit=False))

    async def get_forecast(self, district: str, days: int = 3) -> ServiceResult[list[WeatherData]]:
        from datetime import timedelta
        forecast = [
            WeatherData(
                district=district,
                date=date.today() + timedelta(days=i + 1),
                temp_max_c=30.0 - i,
                temp_min_c=22.0,
                humidity_pct=80.0 + i * 2,
                rain_mm=self._forecast_rain if i == 0 else 2.0,
                precipitation_probability_pct=90.0 if i == 0 else 30.0,
                description="Heavy rain" if i == 0 else "Partly cloudy",
                description_tamil="கனமழை" if i == 0 else "பகுதியளவு மேக மூட்டம்",
            )
            for i in range(min(days, 3))
        ]
        return ServiceResult(data=forecast, metadata=ServiceMetadata(source="mock", cache_hit=False))

    async def health(self) -> bool:
        return True


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def murugan_ctx() -> ConversationContext:
    """Murugan: 42, Thanjavur, 1.8ha paddy, tillering stage."""
    return ConversationContext(
        system=SystemContext(
            trace_id=str(uuid.uuid4()),
            session_id="test-session-murugan",
            request_id="test-req-001",
            timestamp=datetime.now(timezone.utc),
        ),
        farmer=FarmerContext(farmer_id="murugan-001", district="Thanjavur", language="Tamil"),
        farm=FarmContext(
            farm_id="murugan-farm-001",
            farmer_id="murugan-001",
            crop="paddy",
            crop_stage="tillering",
            area_ha=1.8,
            district="Thanjavur",
        ),
        current_question="நாளை மழை வருமா? என் நெல் நீர்ப்பாசனம் செய்ய வேண்டுமா?",
    )


@pytest.fixture
def weather_agent() -> WeatherAgent:
    return WeatherAgent(service=MockWeatherService(current_rain_mm=0.0, forecast_rain_mm=18.0))


@pytest.fixture
def crop_service() -> CropKnowledgeService:
    return CropKnowledgeService()


# ── Phase D milestone tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_irrigation_advice_with_heavy_rain_forecast(weather_agent, murugan_ctx):
    """
    Core milestone: 18mm rain tomorrow → agent advises skip irrigation.
    No LLM involved. Pure agricultural reasoning.
    """
    result = await weather_agent.execute(
        "weather.irrigation_advice",
        murugan_ctx,
        {"crop": "paddy", "crop_stage": "tillering"},
    )

    assert result.success, f"Irrigation advice failed: {result.error}"
    assert result.data["irrigate_today"] is False, "Should advise no irrigation when heavy rain forecast"
    assert "நீர்ப்பாசனம்" in result.data["advice_tamil"], "Advice must be in Tamil"
    assert result.data["quantity_mm"] == 0
    assert result.confidence > 0.7
    assert len(result.citations) > 0


@pytest.mark.asyncio
async def test_irrigation_advice_dry_conditions(murugan_ctx):
    """Dry conditions (no rain today, light rain tomorrow) → agent advises irrigate."""
    dry_agent = WeatherAgent(service=MockWeatherService(current_rain_mm=0.0, forecast_rain_mm=3.0))
    result = await dry_agent.execute(
        "weather.irrigation_advice",
        murugan_ctx,
        {"crop": "paddy", "crop_stage": "tillering"},
    )
    assert result.success
    assert result.data["irrigate_today"] is True, "Should irrigate when conditions are dry"
    assert result.data["quantity_mm"] > 0


@pytest.mark.asyncio
async def test_rain_alert_triggered(weather_agent, murugan_ctx):
    """18mm tomorrow > 10mm threshold → rain alert fires."""
    result = await weather_agent.execute("weather.rain_alert", murugan_ctx, {"threshold_mm": 10.0})
    assert result.success
    assert result.data["alert"] is True
    assert result.data["district"] == "Thanjavur"
    assert len(result.data["heavy_rain_days"]) > 0
    assert "தஞ்சாவூர்" in result.data["message_tamil"] or "Thanjavur" in result.data["message_tamil"]


@pytest.mark.asyncio
async def test_rain_alert_not_triggered_below_threshold(murugan_ctx):
    """5mm rain < 10mm threshold → no alert."""
    light_agent = WeatherAgent(service=MockWeatherService(forecast_rain_mm=5.0))
    result = await light_agent.execute("weather.rain_alert", murugan_ctx, {"threshold_mm": 10.0})
    assert result.success
    assert result.data["alert"] is False


@pytest.mark.asyncio
async def test_spray_suitability_high_humidity(weather_agent, murugan_ctx):
    """MockWeatherService returns humidity=72% → spray suitable."""
    result = await weather_agent.execute("weather.spray_suitability", murugan_ctx, {})
    assert result.success
    # 72% humidity is under 80% threshold — spray should be suitable
    assert result.data["suitable"] is True


@pytest.mark.asyncio
async def test_spray_suitability_blocked_by_rain(murugan_ctx):
    """Rain today → agent blocks spraying."""
    rainy_agent = WeatherAgent(service=MockWeatherService(current_rain_mm=5.0))
    result = await rainy_agent.execute("weather.spray_suitability", murugan_ctx, {})
    assert result.success
    assert result.data["suitable"] is False
    assert "மழை" in result.data["reason_tamil"]


@pytest.mark.asyncio
async def test_crop_water_requirement_paddy_tillering(crop_service):
    """CropKnowledgeService returns correct ETc for paddy tillering."""
    req = await crop_service.get_water_requirement("paddy", "tillering")
    assert req == 8.0  # TNAU: paddy tillering needs 8mm/day


@pytest.mark.asyncio
async def test_tool_result_has_required_fields(weather_agent, murugan_ctx):
    """Every ToolResult must have execution_id, agent_version, execution_time_ms."""
    result = await weather_agent.execute("weather.rain_alert", murugan_ctx, {})
    assert result.execution_id  # UUID, not empty
    assert result.agent_version == "1.0"
    assert result.execution_time_ms >= 0
    assert result.retry_count == 0


@pytest.mark.asyncio
async def test_full_pipeline_no_llm(weather_agent, crop_service, murugan_ctx):
    """
    Full Phase D milestone: Murugan's irrigation question answered without LLM.
    WeatherAgent calls MockWeatherService + CropKnowledgeService reasoning.
    This is the system working as an agricultural intelligence engine.
    """
    # Step 1: WeatherService → forecast
    forecast_result = await weather_agent.execute("weather.forecast", murugan_ctx, {"days": 2})
    assert forecast_result.success
    assert len(forecast_result.data.forecast) > 0

    tomorrow_rain = forecast_result.data.forecast[0].rain_mm
    assert tomorrow_rain == 18.0  # MockWeatherService fixture

    # Step 2: CropKnowledgeService → water requirement
    water_req = await crop_service.get_water_requirement("paddy", "tillering")
    assert water_req == 8.0

    # Step 3: WeatherAgent → irrigation reasoning
    irrigation_result = await weather_agent.execute(
        "weather.irrigation_advice", murugan_ctx, {"crop": "paddy", "crop_stage": "tillering"}
    )
    assert irrigation_result.success
    assert not irrigation_result.data["irrigate_today"]  # heavy rain forecast → skip

    # Step 4: Verify ToolResult contract
    assert irrigation_result.has_data
    assert irrigation_result.confidence > 0.7
    assert len(irrigation_result.citations) >= 1
    assert "TNAU" in irrigation_result.citations[0].source or "Open-Meteo" in irrigation_result.citations[0].source

    # Step 5: Tamil advice present
    advice_tamil = irrigation_result.data["advice_tamil"]
    assert advice_tamil
    assert len(advice_tamil) > 20

    print(f"\n✓ Phase D Milestone Passed")
    print(f"  Tomorrow rain: {tomorrow_rain}mm")
    print(f"  Paddy water need: {water_req}mm/day")
    print(f"  Irrigation advised: {irrigation_result.data['irrigate_today']}")
    print(f"  Tamil advice: {advice_tamil}")
    print(f"  Confidence: {irrigation_result.confidence:.0%}")
    print(f"  Execution time: {irrigation_result.execution_time_ms}ms")
