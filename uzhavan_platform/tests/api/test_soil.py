"""FP-014 soil (contract §7): reference sections from a small CSV fixture (and the real project
files when present), soil test POST/GET with range validation and ownership, and the Postgres
round-trip for soil_tests and diary_entries (throwaway farmer, deleted afterwards)."""
import secrets
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest

from backend.knowledge.soil.service import SoilReference
from tests.helpers import bearer, login

REAL_SOIL_DIR = Path(__file__).resolve().parents[3] / "uzhavan_data/04_soil/processed"

MANNVALAM = """id,District_Name,district_geoboundaries,zone_id,zone,zone_tamil,soils,soils_tamil,status
17,Thanjavur,Thanjavur,4,Cauvery delta,காவேரி டெல்டா மண்டலம்,"Red Loamy , Alluvium","செம்மண், வண்டல் மண்",1
9,Salem,Salem,2,North Western Zone,வடமேற்கு மண்டலம்,"Non Calcareous Red, Calcareous Black",செம்மண்,1
32,Chennai,Chennai,,,,,,
"""
SHC_HEAD = "level,state,district_shc,district_geoboundaries,district_shc_code,block_shc,cycle,scheme,shc_updated_at,parameter,category,n_samples,param_total,pct\n"


def shc_rows(cycle, scheme, total, low):
    return "".join([
        f"district,TN,THANJAVUR,Thanjavur,586,,{cycle},{scheme},2026-09-23T00:00:00Z,N,Low,{low},{total},{round(100*low/total,2)}\n",
        f"district,TN,THANJAVUR,Thanjavur,586,,{cycle},{scheme},2026-09-23T00:00:00Z,N,Medium,{total-low},{total},{round(100*(total-low)/total,2)}\n",
        f"district,TN,THANJAVUR,Thanjavur,586,,{cycle},{scheme},2026-09-23T00:00:00Z,N,High,0,{total},0.0\n",
        f"district,TN,THANJAVUR,Thanjavur,586,,{cycle},{scheme},2026-09-23T00:00:00Z,Zn,Deficient,{low},{total},{round(100*low/total,2)}\n",
        f"district,TN,THANJAVUR,Thanjavur,586,,{cycle},{scheme},2026-09-23T00:00:00Z,Zn,Sufficient,{total-low},{total},{round(100*(total-low)/total,2)}\n",
    ])


SUMMARY = """district,phh2o_0-30cm_wmean,soc_0-30cm_wmean,nitrogen_0-30cm_wmean,cec_0-30cm_wmean,clay_0-30cm_wmean,sand_0-30cm_wmean,silt_0-30cm_wmean,bdod_0-30cm_wmean,qc_flag
Thanjavur,7.02,21.356,1.86,26.56,37.91,31.61,30.47,1.42,ok
Chennai,6.57,26.27,2.11,24.83,34.51,36.17,29.31,1.35,LOW_COVERAGE_urban_or_water_mask
"""


@pytest.fixture
def soil_dir(tmp_path):
    (tmp_path / "tn_mannvalam_district_major_soil_types.csv").write_text(MANNVALAM, encoding="utf-8")
    (tmp_path / "tn_shc_district_nutrient_status_long.csv").write_text(
        SHC_HEAD + shc_rows("2025-26", "Soil Health Card RKVY", 5000, 4990)
        + shc_rows("2026-27", "Soil Health Card RKVY", 1, 1)       # too few samples → ignored
        + shc_rows("2026-27", "NMEO Oilseed", 230, 200), encoding="utf-8")
    (tmp_path / "tn_district_soil_summary.csv").write_text(SUMMARY, encoding="utf-8")
    return tmp_path


def test_reference_sections(soil_dir):
    ref = SoilReference(soil_dir)
    reg = ref.regional("thanjavur")
    assert [s["name"] for s in reg["soil_types"]] == [{"en": "Red Loamy", "ta": "செம்மண்"},
                                                        {"en": "Alluvium", "ta": "வண்டல் மண்"}]
    assert all(s["name"]["ta"] is None for s in ref.regional("salem")["soil_types"])  # counts differ → no pairing
    assert ref.regional("chennai") is None and ref.regional("madurai") is None
    ns = ref.nutrient_status("thanjavur")
    assert (ns["cycle"], ns["scheme"]) == ("2026-27", "NMEO Oilseed")
    n = next(p for p in ns["parameters"] if p["param"] == "N")
    assert n["samples"] == 230 and n["low_pct"] == pytest.approx(86.96) and n["high_pct"] == 0.0
    zn = next(p for p in ns["parameters"] if p["param"] == "Zn")
    assert zn["low_pct"] is None and zn["medium_pct"] is None      # Deficient is not relabelled Low
    assert {c["category"] for c in zn["categories"]} == {"Deficient", "Sufficient"}
    est = ref.estimated("thanjavur")
    assert est["kind"] == "estimated" and est["depth"] == "0-30cm" and est["values"]["soc_g_kg"] == 21.36
    assert any("use a soil test" in c["en"] for c in est["caveats"])
    assert any("implausible" in c["en"] for c in est["caveats"])
    assert len(ref.estimated("chennai")["caveats"]) == 3            # low-coverage caveat added
    assert ref.estimated("madurai") is None


@pytest.mark.skipif(not REAL_SOIL_DIR.exists(), reason="project soil data not present")
def test_real_project_files_cover_districts():
    from backend.meta.catalog import districts
    ref = SoilReference(REAL_SOIL_DIR)
    ids = [d["id"] for d in districts()]
    assert all(ref.estimated(i) for i in ids)                           # 38/38
    assert [i for i in ids if ref.regional(i) is None] == ["chennai"]
    assert [i for i in ids if ref.nutrient_status(i) is None] == ["chennai"]


class FakeSoilTests:
    def __init__(self):
        self.rows = []

    async def add(self, farmer_id, farm_id, fields):
        from datetime import datetime, timezone
        r = {"test_id": str(uuid.uuid4()), "farmer_id": farmer_id, "farm_id": farm_id,
             "created_at": datetime.now(timezone.utc), **fields}
        self.rows.append(r)
        return dict(r)

    async def list_for_farm(self, farm_id):
        return [dict(r) for r in self.rows if r["farm_id"] == farm_id]


@pytest.fixture
async def so(api_client, soil_dir, monkeypatch):
    from backend.conversation.main import app
    from backend.knowledge.soil.tests_store import get_soil_test_store, get_soil_test_store_factory
    monkeypatch.setenv("UZHAVAN_DATA_DIR", str(soil_dir.parent))
    monkeypatch.setattr("backend.conversation.routes.soil._data_dir", lambda s: str(soil_dir))
    store = FakeSoilTests()

    async def _s():
        return store
    app.dependency_overrides[get_soil_test_store] = _s
    app.dependency_overrides[get_soil_test_store_factory] = lambda: _s
    api_client.soil_store = store
    yield api_client


async def test_soil_by_district(so):
    r = await so.get("/api/soil?district_id=thanjavur")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["regional"]["kind"] == "reference" and d["nutrient_status"]["kind"] == "reference"
    assert d["estimated"]["kind"] == "estimated" and d["measured"] == []
    assert r.json()["meta"]["location"]["district_id"] == "thanjavur"
    r = await so.get("/api/soil?district_id=madurai")
    assert r.json()["data"]["regional"] is None and r.json()["data"]["estimated"] is None
    assert (await so.get("/api/soil")).json()["detail"]["code"] == "location_required"
    assert (await so.get("/api/soil?district_id=x")).json()["detail"]["code"] == "invalid_district"
    assert (await so.get("/api/soil?farm_id=abc")).status_code == 401


async def test_soil_tests_flow(so, sms_capture, memory_repo):
    tok = (await login(so, sms_capture))["access_token"]
    fid = next(iter(memory_repo.farmers))
    farm = await memory_repo.create_farm(fid, {"name": "F", "district_id": "thanjavur"})
    body = {"farm_id": farm["farm_id"], "sample_date": "2026-08-01", "lab_name": "STL Thanjavur",
            "ph": 7.8, "oc_pct": 0.42, "n_kg_ha": 210}
    r = await so.post("/api/soil/tests", headers=bearer(tok), json=body)
    assert r.status_code == 201, r.text
    t = r.json()["data"]
    assert t["kind"] == "measured" and t["ph"] == 7.8 and t["zn_ppm"] is None
    r = await so.get(f"/api/soil/tests?farm_id={farm['farm_id']}", headers=bearer(tok))
    assert [x["test_id"] for x in r.json()["data"]] == [t["test_id"]]
    r = await so.get(f"/api/soil?farm_id={farm['farm_id']}", headers=bearer(tok))
    assert r.json()["data"]["measured"][0]["test_id"] == t["test_id"]
    assert r.json()["data"]["estimated"]["kind"] == "estimated"     # estimate never relabelled


@pytest.mark.parametrize("patch,code", [
    ({"ph": 15}, "value_out_of_range"),
    ({"ec_ds_m": -1}, "value_out_of_range"),
    ({"p_kg_ha": 501}, "value_out_of_range"),
    ({"sample_date": (date.today() + timedelta(days=3)).isoformat()}, "invalid_sample_date"),
    ({"sample_date": "1980-01-01"}, "invalid_sample_date"),
    ({"lab_name": "x" * 101}, "invalid_lab_name"),
    ({"ph": None}, "no_values"),
])
async def test_soil_test_validation(so, sms_capture, memory_repo, patch, code):
    tok = (await login(so, sms_capture))["access_token"]
    fid = next(iter(memory_repo.farmers))
    farm = await memory_repo.create_farm(fid, {"name": "F", "district_id": "thanjavur"})
    body = {"farm_id": farm["farm_id"], "sample_date": "2026-08-01", "ph": 7.0} | patch
    r = await so.post("/api/soil/tests", headers=bearer(tok), json=body)
    assert r.status_code == 400 and r.json()["detail"]["code"] == code


async def test_soil_tests_auth_and_ownership(so, sms_capture, memory_repo):
    assert (await so.get("/api/soil/tests?farm_id=x")).status_code == 401
    assert (await so.post("/api/soil/tests", json={"farm_id": "x", "sample_date": "2026-01-01", "ph": 7})).status_code == 401
    tok = (await login(so, sms_capture))["access_token"]
    other, _ = await memory_repo.upsert_farmer_by_phone("9333333333")
    farm = await memory_repo.create_farm(other["farmer_id"], {"name": "X", "district_id": "salem"})
    r = await so.post("/api/soil/tests", headers=bearer(tok), json={"farm_id": farm["farm_id"], "sample_date": "2026-01-01", "ph": 7})
    assert r.status_code == 404
    assert (await so.get(f"/api/soil/tests?farm_id={farm['farm_id']}", headers=bearer(tok))).status_code == 404


# ── Postgres round-trip (soil_tests + diary_entries), throwaway farmer ────────
async def test_postgres_soil_and_diary_roundtrip():
    asyncpg = pytest.importorskip("asyncpg")
    from backend.auth.repository import PostgresRepository
    from backend.diary.store import PostgresDiaryStore
    from backend.knowledge.soil.tests_store import PostgresSoilTestStore
    try:
        pool = await asyncpg.create_pool("postgresql://ajaikumarn@127.0.0.1:5432/uzhavan_dev", min_size=1, max_size=2, timeout=3)
    except Exception:
        pytest.skip("local Postgres not reachable")
    if not await pool.fetchval("SELECT to_regclass('public.soil_tests') IS NOT NULL AND to_regclass('public.diary_entries') IS NOT NULL"):
        await pool.close()
        pytest.skip("migrations 007/008 not applied")
    phone = "6" + "".join(secrets.choice("0123456789") for _ in range(9))
    try:
        repo = PostgresRepository(pool)
        farmer, _ = await repo.upsert_farmer_by_phone(phone)
        fid = farmer["farmer_id"]
        farm = await repo.create_farm(fid, {"name": "T", "district_id": "thanjavur"})
        st = PostgresSoilTestStore(pool)
        t = await st.add(fid, farm["farm_id"], {"sample_date": date(2026, 8, 1), "lab_name": None, "ph": 7.5})
        assert t["ph"] == 7.5 and t["zn_ppm"] is None
        assert [x["test_id"] for x in await st.list_for_farm(farm["farm_id"])] == [t["test_id"]]
        with pytest.raises(asyncpg.CheckViolationError):
            await st.add(fid, farm["farm_id"], {"sample_date": date(2026, 8, 1), "ph": 15})
        ds = PostgresDiaryStore(pool)
        e = await ds.add(fid, "question", "q?", farm_id=farm["farm_id"], ref={"a": 1})
        await ds.add(fid, "expense", "urea", amount_inr=600, entry_date=date(2026, 9, 1))
        rows = await ds.list(fid, 10)
        assert rows[0]["entry_id"] == e["entry_id"] and rows[0]["ref"] == {"a": 1}
        assert rows[1]["amount_inr"] == 600.0
        with pytest.raises(asyncpg.CheckViolationError):
            await ds.add(fid, "bogus", "x")
    finally:
        await pool.execute("DELETE FROM farmers WHERE phone = $1", phone)  # cascades
        await pool.close()
