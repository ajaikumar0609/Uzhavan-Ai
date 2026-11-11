"""FP-010 weather (contract §4): mocked Open-Meteo via httpx.MockTransport. No network."""
import httpx
import pytest

from backend.knowledge.weather.advisories import evaluate, load_rules
from backend.knowledge.weather.open_meteo import PointWeatherClient, wmo_condition
from tests.helpers import bearer, login

CURRENT = {"current": {"time": "2026-09-25T10:30", "temperature_2m": 31.2, "apparent_temperature": 36.0,
                       "relative_humidity_2m": 70, "precipitation": 0.0, "wind_speed_10m": 12.5,
                       "wind_direction_10m": 90, "weather_code": 3, "is_day": 1}}


def daily(precip):
    n = len(precip)
    return {"daily": {"time": [f"2026-09-{25 + i}" for i in range(n)],
                      "temperature_2m_max": [33.0] * n, "temperature_2m_min": [25.0] * n,
                      "precipitation_sum": precip, "precipitation_probability_max": [None] * n,
                      "wind_speed_10m_max": [15.0] * n, "weather_code": [61] * n}}


class Provider:
    def __init__(self, daily_precip=(0.0,) * 7, fail=None):
        self.calls = []
        self.daily_precip = list(daily_precip)
        self.fail = fail

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(dict(request.url.params))
        if self.fail == "connect":
            raise httpx.ConnectError("down", request=request)
        if self.fail == "500":
            return httpx.Response(500, json={"error": True})
        if "current" in request.url.params:
            return httpx.Response(200, json=CURRENT)
        days = int(request.url.params["forecast_days"])
        return httpx.Response(200, json=daily(self.daily_precip[:days]))


@pytest.fixture
def provider():
    return Provider()


@pytest.fixture
async def wx(api_client, provider, fake_redis):
    from backend.conversation.main import app
    from backend.conversation.routes.weather import get_weather_client

    def _client():
        return PointWeatherClient(
            redis_client=fake_redis,
            http_client_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(provider.handler)))
    app.dependency_overrides[get_weather_client] = _client
    yield api_client


async def test_current_by_district(wx, provider):
    r = await wx.get("/api/weather/current?district_id=thanjavur")
    assert r.status_code == 200, r.text
    body = r.json()
    d, m = body["data"], body["meta"]
    assert d["temperature_c"] == 31.2 and d["humidity_pct"] == 70 and d["is_day"] is True
    assert d["condition"] == {"en": "Overcast", "ta": None}
    assert m["source"] == "Open-Meteo" and m["source_url"] == "https://open-meteo.com" and m["kind"] == "current"
    assert m["observed_at"] == "2026-09-25T10:30:00Z" and m["retrieved_at"].endswith("Z")
    assert m["location"]["name"] == "Thanjavur" and m["location"]["resolved_from"] == "district_hq"
    assert any("IMD warnings are not integrated" in n["en"] for n in m["notes"])
    assert provider.calls[0]["latitude"] == "10.787" or provider.calls[0]["latitude"].startswith("10.")


async def test_current_is_cached(wx, provider):
    await wx.get("/api/weather/current?district_id=thanjavur")
    r = await wx.get("/api/weather/current?district_id=thanjavur")
    assert r.status_code == 200 and len(provider.calls) == 1


async def test_forecast_days_and_nulls(wx, provider):
    r = await wx.get("/api/weather/forecast?lat=10.5&lon=79.0&days=3")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["data"]["daily"]) == 3 and body["meta"]["kind"] == "forecast"
    day = body["data"]["daily"][0]
    assert day["precipitation_probability_pct"] is None           # provider null stays null
    assert day["condition"]["en"] == "Slight rain" and day["condition"]["ta"] is None
    assert body["meta"]["observed_at"] is None
    assert body["meta"]["location"]["resolved_from"] == "point"


@pytest.mark.parametrize("fail", ["connect", "500"])
async def test_provider_failure_is_503(wx, provider, fail):
    provider.fail = fail
    for path in ("/api/weather/current", "/api/weather/forecast", "/api/weather/advisories"):
        r = await wx.get(path + "?district_id=madurai")
        assert r.status_code == 503, path
        assert r.json()["detail"]["code"] == "service_unavailable"
        assert "data" not in r.json()


@pytest.mark.parametrize("qs,status,code", [
    ("", 400, "location_required"),
    ("?district_id=atlantis", 400, "invalid_district"),
    ("?lat=10.5", 400, "invalid_location"),
    ("?lat=20.0&lon=79.0", 400, "location_outside_tamil_nadu"),
    ("?days=8&district_id=thanjavur", 422, None),
])
async def test_validation(wx, qs, status, code):
    r = await wx.get("/api/weather/forecast" + qs)
    assert r.status_code == status
    if code:
        assert r.json()["detail"]["code"] == code


async def test_farm_id_requires_auth_and_ownership(wx, sms_capture, memory_repo):
    r = await wx.get("/api/weather/current?farm_id=abc")
    assert r.status_code == 401
    tok = (await login(wx, sms_capture))["access_token"]
    other, _ = await memory_repo.upsert_farmer_by_phone("9222222222")
    farm = await memory_repo.create_farm(other["farmer_id"], {"name": "X", "district_id": "salem"})
    r = await wx.get(f"/api/weather/current?farm_id={farm['farm_id']}", headers=bearer(tok))
    assert r.status_code == 404


async def test_farm_location_used(wx, sms_capture, memory_repo, provider):
    body = await login(wx, sms_capture)
    fid = next(iter(memory_repo.farmers))
    farm = await memory_repo.create_farm(fid, {"name": "Home", "district_id": "thanjavur",
                                               "latitude": 10.9, "longitude": 79.3})
    r = await wx.get(f"/api/weather/current?farm_id={farm['farm_id']}", headers=bearer(body["access_token"]))
    assert r.status_code == 200
    assert r.json()["meta"]["location"] == {"name": "Home", "lat": 10.9, "lon": 79.3,
                                            "resolved_from": "farm", "district_id": "thanjavur"}


async def test_advisories_fire_only_with_farm_context(wx, sms_capture, memory_repo, provider):
    provider.daily_precip = [0.0, 12.0, 0, 0, 0, 0, 0]
    r = await wx.get("/api/weather/advisories?district_id=cuddalore")
    assert r.status_code == 200 and r.json()["data"] == []
    tok = (await login(wx, sms_capture))["access_token"]
    fid = next(iter(memory_repo.farmers))
    farm = await memory_repo.create_farm(fid, {"name": "G", "district_id": "cuddalore",
                                               "crop_id": "groundnut", "crop_stage_id": "harvest"})
    r = await wx.get(f"/api/weather/advisories?farm_id={farm['farm_id']}", headers=bearer(tok))
    adv = r.json()["data"]
    assert [a["rule_id"] for a in adv] == ["groundnut_harvest_rain_wet_heaps"]
    assert adv[0]["evidence"]["matched_days"] == [{"date": "2026-09-26", "precipitation_mm": 12.0}]
    assert "printed p.187" in adv[0]["rule_source"]["page"]


# ── Rules file ───────────────────────────────────────────────────────────────
def test_every_rule_is_cited():
    rules = load_rules()
    assert rules, "rules file loads"
    for r in rules:
        assert r["rule_source"]["title"] and r["rule_source"]["page"] and r["rule_source"]["quote"]
        assert r["severity"] in ("info", "caution")


def test_paddy_nursery_heavy_rain_threshold():
    rules = load_rules()
    base = [{"date": "d0", "precipitation_mm": 64.4}, {"date": "d1", "precipitation_mm": 10.0}]
    assert evaluate(rules, base, "paddy", "nursery") == []
    base[1]["precipitation_mm"] = 64.5
    assert [a["rule_id"] for a in evaluate(rules, base, "paddy", "nursery")] == ["paddy_sri_nursery_heavy_rain"]
    assert evaluate(rules, base, "paddy", "vegetative") == []
    assert evaluate(rules, [{"date": "d0", "precipitation_mm": None}], "paddy", "nursery") == []


def test_wmo_unknown_code_is_not_invented():
    assert wmo_condition(None) == {"en": None, "ta": None}
    assert wmo_condition(42)["en"] == "Unknown weather code 42"
