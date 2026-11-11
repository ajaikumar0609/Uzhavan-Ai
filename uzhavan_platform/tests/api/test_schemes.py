"""FP-012 schemes (contract §6): endpoints (fake store), eligibility API (in-memory repo),
one unit test per eligibility rule, rule fidelity against the source file, and the loader."""
import json
import re
import sys
from pathlib import Path

import pytest

from backend.knowledge.scheme.eligibility import contexts, evaluate, load_rules
from tests.helpers import bearer, login

SCHEMES_FILE = Path(__file__).resolve().parents[3] / "uzhavan_data/09_government_schemes/processed/schemes.jsonl"
TN = "https://www.tnagrisnet.tn.gov.in/home/schemes/"


def scheme(sid, **kw):
    base = {"scheme_id": sid, "name": f"Scheme {sid}", "tamil_name": None, "authority": "Dept", "level": "state",
            "state": "Tamil Nadu", "active": True, "crops": None, "crop_applicability": None, "description": None,
            "description_ta": None, "eligibility": None, "eligibility_ta": None, "benefit": "b",
            "application_method": None, "documents_required": None, "required_documents_ta": None,
            "official_url": TN, "source_documents": ["x.json"], "date_checked": None,
            "last_updated_on_source": None, "source_catalogue": "c", "source_go_file": None, "components": None}
    return base | kw


class FakeSchemeStore:
    def __init__(self):
        self.items = {
            "tn_agrisnet_A_38": scheme("tn_agrisnet_A_38", name="Sustainable Cotton Cultivation Mission",
                                       tamil_name="நிலையான பருத்தி சாகுபடி திட்டம்", active=False),
            "central_pm_kisan": scheme("central_pm_kisan", level="central", official_url="https://pmkisan.gov.in/"),
            "no_rule_scheme": scheme("no_rule_scheme", crops=["paddy"]),
        }
        self.last = None

    async def list(self, q, level, crop_id, active):
        self.last = (q, level, crop_id, active)
        return list(self.items.values())

    async def get(self, sid):
        return self.items.get(sid)


@pytest.fixture
async def sc(api_client):
    from backend.conversation.main import app
    from backend.knowledge.scheme.store import get_scheme_store
    store = FakeSchemeStore()

    async def _s():
        return store
    app.dependency_overrides[get_scheme_store] = _s
    api_client.store = store
    yield api_client


async def test_list_and_filters(sc):
    r = await sc.get("/api/schemes?q=cotton&level=state&crop_id=paddy&active=true")
    assert r.status_code == 200
    assert sc.store.last == ("cotton", "state", "paddy", True)
    item = r.json()["data"][0]
    assert set(item) == {"scheme_id", "name", "authority", "level", "active", "crops", "official_url"}
    assert item["name"]["ta"] == "நிலையான பருத்தி சாகுபடி திட்டம்"
    assert (await sc.get("/api/schemes?level=district")).json()["detail"]["code"] == "invalid_level"
    assert (await sc.get("/api/schemes?crop_id=rose")).json()["detail"]["code"] == "invalid_crop"


async def test_detail_nulls_stay_null(sc):
    r = await sc.get("/api/schemes/central_pm_kisan")
    d = r.json()["data"]
    assert d["application_method"] is None and d["required_documents"] is None and d["description"] is None
    assert d["benefits"] == {"en": "b", "ta": None}
    assert (await sc.get("/api/schemes/nope")).status_code == 404


async def test_eligibility_requires_auth(sc):
    r = await sc.get("/api/schemes/tn_agrisnet_A_38/eligibility")
    assert r.status_code == 401


async def test_eligibility_api_flow(sc, sms_capture, memory_repo):
    tok = (await login(sc, sms_capture))["access_token"]
    fid = next(iter(memory_repo.farmers))
    # no farm, no district → more information required
    d = (await sc.get("/api/schemes/tn_agrisnet_A_38/eligibility", headers=bearer(tok))).json()["data"]
    assert d["status"] == "more_information_required" and set(d["missing_fields"]) == {"crop_id", "district_id"}
    assert any("not active" in r["en"] for r in d["reasons"])
    await memory_repo.create_farm(fid, {"name": "Paddy plot", "district_id": "thanjavur", "crop_id": "paddy"})
    farm = await memory_repo.create_farm(fid, {"name": "Cotton plot", "district_id": "salem", "crop_id": "cotton"})
    d = (await sc.get("/api/schemes/tn_agrisnet_A_38/eligibility", headers=bearer(tok))).json()["data"]
    assert d["status"] == "eligible_known_criteria" and d["criteria_source_url"] == TN
    d = (await sc.get("/api/schemes/no_rule_scheme/eligibility", headers=bearer(tok))).json()["data"]
    assert d["status"] == "cannot_determine" and d["missing_fields"] == []
    d = (await sc.get("/api/schemes/central_pm_kisan/eligibility", headers=bearer(tok))).json()["data"]
    assert d["status"] == "more_information_required"
    assert d["missing_fields"] == ["land_records_ownership", "family_exclusion_status_cl_4_1"]
    r = await sc.get(f"/api/schemes/tn_agrisnet_A_38/eligibility?farm_id={farm['farm_id']}", headers=bearer(tok))
    assert r.json()["data"]["status"] == "eligible_known_criteria"
    r = await sc.get("/api/schemes/tn_agrisnet_A_38/eligibility?farm_id=not-mine", headers=bearer(tok))
    assert r.status_code == 404


# ── One test per rule ─────────────────────────────────────────────────────────
def run(sid, district=None, crop=None, area=None, farms=True):
    farm_list = [{"name": "F", "district_id": district, "crop_id": crop, "area_ha": area}] if farms else []
    return evaluate(scheme(sid), contexts({"district_id": district}, farm_list))


E, N, M = "eligible_known_criteria", "not_eligible_known_criteria", "more_information_required"

RULE_CASES = {
    "tn_agrisnet_A_38": [({"district": "salem", "crop": "cotton"}, E), ({"district": "chennai", "crop": "cotton"}, N),
                         ({"district": "salem", "crop": "paddy"}, N), ({"district": "salem", "crop": None}, M)],
    "tn_agrisnet_A_43": [({"district": "thanjavur", "crop": "paddy"}, E), ({"district": "the_nilgiris", "crop": "paddy"}, N),
                         ({"district": "thanjavur", "crop": "banana"}, N)],
    "tn_agrisnet_A_98": [({"district": "madurai", "crop": "black_gram"}, E), ({"district": "chennai", "crop": "green_gram"}, N),
                         ({"district": "madurai", "crop": "other"}, M)],
    "tn_agrisnet_A_126": [({"district": "mayiladuthurai", "crop": "green_gram"}, E), ({"district": "salem", "crop": "black_gram"}, N)],
    "tn_agrisnet_A_148": [({"district": "tenkasi"}, E), ({"district": "thanjavur"}, N), ({"district": None}, M)],
    "tn_agrisnet_H_155": [({"district": "the_nilgiris"}, E), ({"district": "chennai"}, N)],
    "tn_agrisnet_H_156": [({"district": "karur"}, E), ({"district": "the_nilgiris"}, N)],
    "tn_agrisnet_H_158": [({"district": "karur"}, E), ({"district": "chennai"}, N)],
    "tn_agrisnet_H_160": [({"district": "the_nilgiris"}, E), ({"district": "chennai"}, N)],
    "tn_agrisnet_H_161": [({"district": "thanjavur"}, E), ({"district": "tiruppur"}, N), ({"district": "kanniyakumari"}, N)],
    "tn_agrisnet_S_61": [({"district": "erode", "crop": "sugarcane"}, E), ({"district": "erode", "crop": "banana"}, N)],
    "tn_aed_smam": [({"district": "vellore"}, E), ({"district": "chennai"}, N)],
    "tn_agrisnet_E_71": [({"district": "vellore", "area": 1.0}, M)],
    "central_pm_kisan": [({"district": "vellore", "crop": "paddy"}, M)],
    "central_pmfby": [({"district": "vellore", "crop": "paddy"}, M)],
    "central_pm_kusum": [({"district": "vellore"}, M)],
}


def test_every_rule_has_cases():
    assert set(RULE_CASES) == set(load_rules())


@pytest.mark.parametrize("sid,kw,expected",
                         [(sid, kw, exp) for sid, cases in RULE_CASES.items() for kw, exp in cases])
def test_rule(sid, kw, expected):
    res = run(sid, **kw)
    assert res["status"] == expected, res
    assert res["criteria_source_url"] == load_rules()[sid]["criteria_source_url"]
    if expected == M:
        assert res["missing_fields"]


def test_requires_never_become_eligible():
    for sid, rule in load_rules().items():
        if rule["requires"]:
            assert run(sid, district="thanjavur", crop="paddy", area=1.0)["status"] == M


def test_no_farms_uses_profile_district():
    res = evaluate(scheme("tn_agrisnet_H_160"), contexts({"district_id": "salem"}, []))
    assert res["status"] == E


# ── Rule fidelity against the stored source text ──────────────────────────────
def _norm(t):
    return re.sub(r"\s+", " ", t).strip().lower()


@pytest.mark.skipif(not SCHEMES_FILE.exists(), reason="schemes.jsonl not available")
def test_rules_quote_source_and_url():
    src = {json.loads(line)["scheme_id"]: json.loads(line) for line in SCHEMES_FILE.read_text().splitlines()}
    for sid, rule in load_rules().items():
        assert sid in src, sid
        assert src[sid]["eligibility"], f"{sid}: source has no eligibility text"
        assert rule["criteria_source_url"] == src[sid]["official_url"], sid
        head = _norm(rule["criteria_text"])[:40]
        assert head in _norm(src[sid]["eligibility"]), sid


# ── Loader ─────────────────────────────────────────────────────────────────────
async def test_scheme_loader_idempotent(temp_schema, tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import load_schemes as loader
    schema, conn = temp_schema
    recs = [
        {"scheme_id": "a", "scheme_name": "A", "scheme_name_ta": "அ", "authority": "X", "level": "state",
         "state": "Tamil Nadu", "eligibility": None, "benefits": "b", "application_method": None,
         "required_documents": None, "official_url": "u", "source_documents": ["d"], "date_checked": "2026-09-24",
         "crop_applicability": "Paddy (Kuruvai)", "last_updated_on_source": None, "source_catalogue": "c",
         "source_active_flag": "no"},
        {"scheme_id": "b", "scheme_name": "B", "scheme_name_ta": None, "authority": "Y", "level": "central",
         "state": None, "eligibility": "e", "benefits": None, "application_method": None,
         "required_documents": None, "official_url": "v", "source_documents": [], "date_checked": "2026-09-24",
         "crop_applicability": "Notified crops", "last_updated_on_source": None, "source_catalogue": "c"},
    ]
    f = tmp_path / "s.jsonl"
    f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs))
    dsn = f"postgresql://ajaikumarn@127.0.0.1:5432/uzhavan_dev?search_path={schema}"
    for _ in range(2):
        assert (await loader.load(dsn, f))["loaded"] == 2
    rows = {r["scheme_key"]: r for r in await conn.fetch(f"SELECT * FROM {schema}.government_schemes")}
    assert rows["a"]["crops"] == ["paddy"] and rows["a"]["active"] is False and rows["a"]["tamil_name"] == "அ"
    assert rows["b"]["crops"] is None and rows["b"]["active"] is None and rows["b"]["benefit"] is None
    f.write_text(json.dumps(recs[0], ensure_ascii=False))
    assert (await loader.load(dsn, f))["loaded"] == 1          # removed from source → removed from table


async def test_postgres_scheme_store_real():
    asyncpg = pytest.importorskip("asyncpg")
    from backend.knowledge.scheme.store import PostgresSchemeStore
    try:
        pool = await asyncpg.create_pool("postgresql://ajaikumarn@127.0.0.1:5432/uzhavan_dev", min_size=1, max_size=2, timeout=3)
    except Exception:
        pytest.skip("local Postgres not reachable")
    try:
        store = PostgresSchemeStore(pool)
        all_ = await store.list(None, None, None, None)
        if not all_:
            pytest.skip("schemes not loaded")
        assert len(all_) == 136
        assert {s["scheme_id"] for s in await store.list(None, None, "paddy", None)} >= {"tn_kuruvai_package_2026"}
        assert all(s["level"] == "central" for s in await store.list(None, "central", None, None))
        assert all(s["active"] is True for s in await store.list(None, None, None, True))
        assert await store.list("Kisan Samman", None, None, None)
        d = await store.get("central_pm_kisan")
        assert d["official_url"] == "https://pmkisan.gov.in/" and isinstance(d["source_documents"], list)
    finally:
        await pool.close()
