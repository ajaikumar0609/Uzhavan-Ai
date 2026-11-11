"""FP-009: profile PUT/GET, farm CRUD, TN bbox validation, ownership, farm limit."""

import pytest

from tests.helpers import bearer, login

A = "9000000001"
B = "9000000002"
FARM = {
    "name": "North field", "district_id": "thanjavur", "village": "Vallam",
    "latitude": 10.787, "longitude": 79.138, "area_ha": 0.8,
    "crop_id": "paddy", "crop_stage_id": "vegetative", "season_id": "samba", "irrigation_type_id": "canal",
}


@pytest.fixture
async def tok_a(api_client, sms_capture):
    return (await login(api_client, sms_capture, A))["access_token"]


@pytest.fixture
async def tok_b(api_client, sms_capture):
    return (await login(api_client, sms_capture, B))["access_token"]


async def test_profile_put_then_get(api_client, sms_capture, fake_redis, tok_a):
    h = bearer(tok_a)
    r = await api_client.put("/api/farmer/profile", json={"name": "Murugan"}, headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["profile_complete"] is False  # district still missing
    r = await api_client.put("/api/farmer/profile",
                             json={"district_id": "thanjavur", "village": "Vallam", "preferred_language": "en"},
                             headers=h)
    assert r.status_code == 200
    r = await api_client.get("/api/farmer/profile", headers=h)
    d = r.json()["data"]
    assert d["name"] == "Murugan" and d["district_id"] == "thanjavur" and d["village"] == "Vallam"
    assert d["preferred_language"] == "en" and d["profile_complete"] is True
    assert d["phone"] == A and d["created_at"].endswith("Z")
    # A later login reports profile_complete=true and is_new_farmer=false.
    await fake_redis.delete(f"otp:cooldown:{A}")
    again = await login(api_client, sms_capture, A)
    assert again["is_new_farmer"] is False and again["profile_complete"] is True


@pytest.mark.parametrize("body,code", [
    ({"name": "M"}, "invalid_name"),
    ({"name": "x" * 101}, "invalid_name"),
    ({"district_id": "atlantis"}, "invalid_district"),
    ({"preferred_language": "fr"}, "invalid_language"),
])
async def test_profile_validation(api_client, tok_a, body, code):
    r = await api_client.put("/api/farmer/profile", json=body, headers=bearer(tok_a))
    assert r.status_code == 400 and r.json()["detail"]["code"] == code


async def test_profile_requires_auth(api_client):
    assert (await api_client.put("/api/farmer/profile", json={"name": "Abc"})).status_code == 401


async def test_farm_crud(api_client, tok_a):
    h = bearer(tok_a)
    r = await api_client.post("/api/farms", json=FARM, headers=h)
    assert r.status_code == 201, r.text
    farm = r.json()
    assert farm["area_ha"] == 0.8 and farm["crop_id"] == "paddy" and farm["latitude"] == 10.787
    fid = farm["farm_id"]

    r = await api_client.get("/api/farms", headers=h)
    assert [f["farm_id"] for f in r.json()["data"]] == [fid]

    r = await api_client.put(f"/api/farms/{fid}", json={"crop_stage_id": "flowering", "area_ha": 1.2}, headers=h)
    assert r.status_code == 200
    assert r.json()["crop_stage_id"] == "flowering" and r.json()["name"] == "North field"

    r = await api_client.delete(f"/api/farms/{fid}", headers=h)
    assert r.status_code == 204
    assert (await api_client.get("/api/farms", headers=h)).json()["data"] == []


@pytest.mark.parametrize("patch,code", [
    ({"latitude": 7.9, "longitude": 79.0}, "location_outside_tamil_nadu"),
    ({"latitude": 13.7, "longitude": 79.0}, "location_outside_tamil_nadu"),
    ({"latitude": 10.0, "longitude": 76.1}, "location_outside_tamil_nadu"),
    ({"latitude": 10.0, "longitude": 80.5}, "location_outside_tamil_nadu"),
    ({"latitude": 10.0, "longitude": None}, "invalid_location"),
    ({"area_ha": 0}, "invalid_area"),
    ({"district_id": "bengaluru"}, "invalid_district"),
    ({"crop_id": "wheat"}, "invalid_crop"),
    ({"season_id": "monsoon"}, "invalid_season"),
    ({"name": ""}, "invalid_name"),
])
async def test_farm_validation(api_client, tok_a, patch, code):
    r = await api_client.post("/api/farms", json={**FARM, **patch}, headers=bearer(tok_a))
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == code


async def test_farm_bbox_edges_accepted(api_client, tok_a):
    r = await api_client.post("/api/farms", json={**FARM, "latitude": 8.0, "longitude": 80.4}, headers=bearer(tok_a))
    assert r.status_code == 201


async def test_farm_without_location_ok(api_client, tok_a):
    body = {"name": "Plot 2", "district_id": "madurai"}
    r = await api_client.post("/api/farms", json=body, headers=bearer(tok_a))
    assert r.status_code == 201
    assert r.json()["latitude"] is None and r.json()["crop_id"] is None


async def test_other_farmers_farm_is_not_found(api_client, tok_a, tok_b):
    fid = (await api_client.post("/api/farms", json=FARM, headers=bearer(tok_a))).json()["farm_id"]
    hb = bearer(tok_b)
    assert (await api_client.put(f"/api/farms/{fid}", json={"name": "Mine"}, headers=hb)).status_code == 404
    assert (await api_client.delete(f"/api/farms/{fid}", headers=hb)).status_code == 404
    assert (await api_client.get("/api/farms", headers=hb)).json()["data"] == []
    # Still intact for the owner.
    assert len((await api_client.get("/api/farms", headers=bearer(tok_a))).json()["data"]) == 1


async def test_unknown_farm_id_is_404(api_client, tok_a):
    r = await api_client.delete("/api/farms/not-a-uuid", headers=bearer(tok_a))
    assert r.status_code == 404 and r.json()["detail"]["code"] == "not_found"


async def test_max_five_farms(api_client, tok_a):
    h = bearer(tok_a)
    for i in range(5):
        assert (await api_client.post("/api/farms", json={**FARM, "name": f"F{i}"}, headers=h)).status_code == 201
    r = await api_client.post("/api/farms", json={**FARM, "name": "F6"}, headers=h)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "farm_limit_reached"


async def test_farms_require_auth(api_client):
    assert (await api_client.get("/api/farms")).status_code == 401
    assert (await api_client.post("/api/farms", json=FARM)).status_code == 401
