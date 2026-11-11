"""FP-011 market (contract §5): endpoints on a fake store, the loader on a small parquet fixture
(isolated Postgres schema), and the real PostgresMarketStore read-only if the snapshot is loaded."""
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

DSN = "postgresql://ajaikumarn@127.0.0.1:5432/uzhavan_dev"
TODAY = datetime.now(timezone.utc).date()


class FakeMarketStore:
    def __init__(self, loaded=True):
        self.loaded = loaded
        self.rows = [
            {"commodity": "paddy", "variety": "Common", "market": "Thanjavur APMC", "district_id": "thanjavur",
             "modal_price_inr": 2300.0, "min_price_inr": 2200.0, "max_price_inr": None, "arrivals_tonnes": 5.0,
             "price_unit": "Rs/quintal", "price_date": TODAY - timedelta(days=1)},
            {"commodity": "coconut", "variety": "Other", "market": "Old APMC", "district_id": None,
             "modal_price_inr": 1500.0, "min_price_inr": None, "max_price_inr": None, "arrivals_tonnes": None,
             "price_unit": "Rs/quintal", "price_date": TODAY - timedelta(days=30)},
        ]
        self.last_latest_args = None

    async def commodities(self):
        return ["coconut", "paddy", "mystery_crop"]

    async def markets(self, district_id):
        ms = [{"market": "Thanjavur APMC", "district_id": "thanjavur", "market_type": "apmc"},
              {"market": "Old APMC", "district_id": None, "market_type": "apmc"}]
        return [m for m in ms if district_id is None or m["district_id"] == district_id]

    async def latest(self, commodity, district_id, market, limit):
        self.last_latest_args = (commodity, district_id, market, limit)
        return [r for r in self.rows if commodity in (None, r["commodity"])][:limit]

    async def trend(self, commodity, market, since, variety):
        return [{"price_date": TODAY - timedelta(days=2), "variety": "A", "modal_price_inr": 2000.0},
                {"price_date": TODAY - timedelta(days=2), "variety": "B", "modal_price_inr": 2100.0}]

    async def snapshot(self):
        return {"snapshot_date": date(2026, 9, 24), "row_count": 2} if self.loaded else None


@pytest.fixture
def market_store():
    return FakeMarketStore()


@pytest.fixture
async def mk(api_client, market_store):
    from backend.conversation.main import app
    from backend.knowledge.market.store import get_market_store

    async def _s():
        return market_store
    app.dependency_overrides[get_market_store] = _s
    yield api_client


async def test_commodities(mk):
    r = await mk.get("/api/market/commodities")
    assert r.status_code == 200
    body = r.json()
    by = {c["id"]: c for c in body["data"]}
    assert by["coconut"]["unit_note"] == "unit unverified (per quintal vs per 1000 nuts)"
    assert by["paddy"]["name"] == {"en": "Paddy", "ta": "நெல்"} and by["paddy"]["unit_note"] is None
    assert by["mystery_crop"]["name"]["ta"] is None           # no invented translation
    assert any("2026-09-24" in n["en"] for n in body["meta"]["notes"])


async def test_markets_filter_and_validation(mk):
    r = await mk.get("/api/market/markets?district_id=thanjavur")
    assert [m["market"] for m in r.json()["data"]] == ["Thanjavur APMC"]
    r = await mk.get("/api/market/markets?district_id=atlantis")
    assert r.status_code == 400 and r.json()["detail"]["code"] == "invalid_district"


async def test_latest_shape_stale_and_no_advice(mk, market_store):
    r = await mk.get("/api/market/latest?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["kind"] == "latest_observed"
    fresh, old = body["data"]
    assert fresh["commodity_name"] == {"en": "Paddy", "ta": "நெல்"} and fresh["unit"] == "Rs/quintal"
    assert fresh["stale"] is False and fresh["max_price"] is None
    assert old["stale"] is True and old["district_id"] is None
    for row in body["data"]:
        assert not {"advice", "forecast", "recommendation", "predicted_price"} & set(row)
    r = await mk.get("/api/market/latest?commodity=paddy&market=Thanjavur%20APMC&limit=3")
    assert market_store.last_latest_args == ("paddy", None, "Thanjavur APMC", 3)
    assert (await mk.get("/api/market/latest?limit=0")).status_code == 422


async def test_trend(mk):
    r = await mk.get("/api/market/trend?commodity=paddy&market=Thanjavur%20APMC&days=30")
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["kind"] == "historical"
    assert [p["modal_price"] for p in body["data"]["points"]] == [2000.0, 2100.0]
    assert any("not averaged" in n["en"] for n in body["meta"]["notes"])
    assert (await mk.get("/api/market/trend?commodity=paddy")).status_code == 422


async def test_unloaded_is_503(api_client):
    from backend.conversation.main import app
    from backend.knowledge.market.store import get_market_store

    async def _s():
        return FakeMarketStore(loaded=False)
    app.dependency_overrides[get_market_store] = _s
    r = await api_client.get("/api/market/latest?commodity=paddy")
    assert r.status_code == 503 and r.json()["detail"]["code"] == "service_unavailable"


# ── Loader on a small fixture, isolated schema ───────────────────────────────
def _write_fixture(path: Path):
    pa = pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq
    rows = {
        "date": [datetime(2026, 9, 20), datetime(2026, 9, 21), datetime(2026, 9, 22)],
        "state": ["Tamil Nadu"] * 3,
        "district": ["Thiruvellore", None, "Thanjavur"],
        "market": ["Ponneri", "Chengeri", "Thanjavur"],
        "market_type": ["apmc", "apmc", "uzhavar_sandhai"],
        "market_raw": ["Ponneri APMC", "Chengeri APMC", "Thanjavur Uzhavar Sandhai"],
        "commodity": ["paddy", "paddy", "tomato"],
        "commodity_id": [2, 2, 78],
        "commodity_source_name": ["Paddy(Common)", "Paddy(Common)", "Tomato"],
        "variety": ["Common", "Common", "Local"],
        "arrivals_tonnes": [1.0, 2.0, 0.5],
        "min_price": [2000.0, 2100.0, 1000.0],
        "max_price": [2300.0, 2400.0, 1200.0],
        "modal_price": [2200.0, 2200.0, 99999.0],
        "price_unit": ["Rs/quintal"] * 3,
        "qc_flags": ["", "district_unmatched", "price_outlier_10x_median"],
        "qc_pass": [True, True, False],
        "source_file": ["f1", "f2", "f3"],
    }
    pq.write_table(pa.table(rows), path)


async def test_loader_qc_pass_only_and_idempotent(temp_schema, tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import load_mandi_prices as loader
    schema, conn = temp_schema
    f = tmp_path / "mini.parquet"
    _write_fixture(f)
    dsn = f"{DSN}?search_path={schema}"
    for _ in range(2):  # twice → same result (truncate + load in one transaction)
        res = await loader.load(dsn, f, date(2026, 9, 24))
        assert res["file_rows"] == 3 and res["qc_pass_rows"] == 2 and res["loaded"] == 2
    rows = await conn.fetch(f"SELECT market, district, district_id, modal_price_inr FROM {schema}.mandi_prices ORDER BY market")
    assert [(r["market"], r["district_id"]) for r in rows] == [("Chengeri APMC", None), ("Ponneri APMC", "tiruvallur")]
    ds = await conn.fetch(f"SELECT snapshot_date, row_count, file_sha256 FROM {schema}.data_sources")
    assert len(ds) == 1 and ds[0]["row_count"] == 2 and ds[0]["snapshot_date"] == date(2026, 9, 24)
    assert ds[0]["file_sha256"] == loader.sha256_file(f)


# ── Real store, read-only (skips unless the snapshot is loaded) ──────────────
async def test_postgres_market_store_real_snapshot():
    asyncpg = pytest.importorskip("asyncpg")
    from backend.knowledge.market.store import PostgresMarketStore
    try:
        pool = await asyncpg.create_pool(DSN, min_size=1, max_size=2, timeout=3)
    except Exception:
        pytest.skip("local Postgres not reachable")
    try:
        store = PostgresMarketStore(pool)
        if not await store.snapshot():
            pytest.skip("mandi snapshot not loaded")
        assert "paddy" in await store.commodities()
        rows = await store.latest("paddy", "thanjavur", None, 5)
        assert rows and all(r["commodity"] == "paddy" and r["district_id"] == "thanjavur" for r in rows)
        pts = await store.trend("paddy", rows[0]["market"], rows[0]["price_date"] - timedelta(days=90), None)
        assert pts and pts[-1]["price_date"] <= rows[0]["price_date"]
    finally:
        await pool.close()
