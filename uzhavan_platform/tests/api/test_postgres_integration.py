"""PostgresRepository against the real local Postgres (skipped only if it is unreachable).

Uses random phone numbers in the 6xxxxxxxxx range and deletes everything it created.
"""
import secrets
from datetime import datetime, timedelta, timezone

import pytest

from backend.auth.otp import hash_otp, otp_expiry
from backend.auth.repository import PostgresRepository
from backend.auth.tokens import new_refresh_token

DSN = "postgresql://ajaikumarn@127.0.0.1:5432/uzhavan_dev"


@pytest.fixture
async def pg_repo():
    asyncpg = pytest.importorskip("asyncpg")
    try:
        pool = await asyncpg.create_pool(DSN, min_size=1, max_size=2, timeout=3)
    except Exception:
        pytest.skip("local Postgres not reachable")
    has_farms = await pool.fetchval("SELECT to_regclass('public.farms') IS NOT NULL")
    if not has_farms:
        await pool.close()
        pytest.skip("migration 004 not applied")
    phone = "6" + "".join(secrets.choice("0123456789") for _ in range(9))
    yield PostgresRepository(pool), phone
    await pool.execute("DELETE FROM farmers WHERE phone = $1", phone)  # cascades to tokens + farms
    await pool.execute("DELETE FROM otp_requests WHERE phone = $1", phone)
    await pool.close()


async def test_postgres_roundtrip(pg_repo):
    repo, phone = pg_repo
    await repo.save_otp(phone, hash_otp("123456", phone), otp_expiry())
    rec = await repo.get_latest_otp(phone)
    assert rec and rec["attempts"] == 0
    assert await repo.consume_otp_attempt(rec["id"]) == 1
    await repo.mark_otp_verified(rec["id"])
    assert await repo.get_latest_otp(phone) is None

    farmer, is_new = await repo.upsert_farmer_by_phone(phone)
    assert is_new and farmer["name"] is None
    again, is_new2 = await repo.upsert_farmer_by_phone(phone)
    assert not is_new2 and again["farmer_id"] == farmer["farmer_id"]
    fid = farmer["farmer_id"]

    upd = await repo.update_farmer(fid, {"name": "Test Farmer", "district_id": "thanjavur",
                                         "_district_name": "Thanjavur", "preferred_language": "en"})
    assert upd["district_id"] == "thanjavur" and upd["preferred_language"] == "en"

    raw, h = new_refresh_token()
    await repo.save_refresh_token(fid, h, datetime.now(timezone.utc) + timedelta(days=30), "pytest", "127.0.0.1")
    raw2, h2 = new_refresh_token()
    status, f = await repo.rotate_refresh_token(h, h2, datetime.now(timezone.utc) + timedelta(days=30), None, None)
    assert status == "ok" and f["farmer_id"] == fid
    status, _ = await repo.rotate_refresh_token(h, "x" * 64, datetime.now(timezone.utc), None, None)
    assert status == "reused"
    status, _ = await repo.rotate_refresh_token(h2, "y" * 64, datetime.now(timezone.utc), None, None)
    assert status == "reused"  # reuse revoked the whole family

    farm = await repo.create_farm(fid, {"name": "F1", "district_id": "thanjavur", "latitude": 10.7,
                                        "longitude": 79.1, "area_ha": 0.5, "crop_id": "paddy",
                                        "boundary_geojson": {"type": "Polygon", "coordinates": []}})
    assert farm["latitude"] == 10.7 and farm["boundary_geojson"]["type"] == "Polygon"
    assert await repo.count_farms(fid) == 1
    farm2 = await repo.update_farm(farm["farm_id"], {"crop_stage_id": "harvest"})
    assert farm2["crop_stage_id"] == "harvest"
    await repo.delete_farm(farm["farm_id"])
    assert await repo.list_farms(fid) == []


async def test_postgres_bbox_check_constraint(pg_repo):
    import asyncpg
    repo, phone = pg_repo
    farmer, _ = await repo.upsert_farmer_by_phone(phone)
    with pytest.raises(asyncpg.CheckViolationError):
        await repo.create_farm(farmer["farmer_id"], {"name": "Bad", "district_id": "thanjavur",
                                                     "latitude": 20.0, "longitude": 79.0})
