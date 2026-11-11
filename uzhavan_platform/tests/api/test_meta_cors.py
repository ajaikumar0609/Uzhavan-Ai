"""Meta endpoints (contract §1), CORS preflight (FP-007 AC-6), /health and /health/config."""


async def test_districts(api_client):
    r = await api_client.get("/api/meta/districts")
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["kind"] == "reference"
    data = body["data"]
    assert len(data) == 38
    assert len({d["id"] for d in data}) == 38
    tj = next(d for d in data if d["id"] == "thanjavur")
    assert tj["name"] == {"en": "Thanjavur", "ta": "தஞ்சாவூர்"}
    assert round(tj["lat"], 2) == 10.79 and round(tj["lon"], 2) == 79.14
    for d in data:
        assert 8.0 <= d["lat"] <= 13.6 and 76.2 <= d["lon"] <= 80.4


async def test_crops(api_client):
    r = await api_client.get("/api/meta/crops")
    ids = [c["id"] for c in r.json()["data"]]
    assert ids[0] == "paddy" and "other" in ids and len(ids) == 13
    assert r.json()["data"][0]["name"] == {"en": "Paddy", "ta": "நெல்"}


async def test_enums(api_client):
    data = (await api_client.get("/api/meta/enums")).json()["data"]
    assert set(data) == {"crop_stages", "seasons", "irrigation_types", "diary_kinds"}
    assert {d["id"] for d in data["diary_kinds"]} == {"note", "observation", "expense", "income", "question", "scan"}
    for items in data.values():
        for it in items:
            assert set(it) == {"id", "name"} and set(it["name"]) == {"en", "ta"}


async def test_cors_preflight_put_from_capacitor_origin(api_client):
    r = await api_client.options("/api/farmer/profile", headers={
        "Origin": "https://localhost",
        "Access-Control-Request-Method": "PUT",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "https://localhost"
    assert "PUT" in r.headers["access-control-allow-methods"]


async def test_cors_preflight_rejects_unknown_origin(api_client):
    r = await api_client.options("/api/farmer/profile", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "PUT",
    })
    assert "access-control-allow-origin" not in r.headers


async def test_health(api_client):
    r = await api_client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


async def test_health_config_booleans_only(api_client):
    r = await api_client.get("/health/config")
    assert r.status_code == 200
    body = r.json()
    assert body["env"] == "test"
    for k in ("llm_provider_set", "database_reachable", "redis_reachable", "chroma_present", "disease_service_url_set"):
        assert isinstance(body[k], bool)
    from backend.shared.db import close_all
    await close_all()  # don't leak a pool bound to this test's event loop
