"""Contract §9: with a token and farm_id, /conversation takes district/crop/stage/area from the farm."""
import pytest
from fastapi import HTTPException

from backend.conversation.routes.conversation import ConversationRequest, _apply_farm


async def _setup(repo):
    farmer, _ = await repo.upsert_farmer_by_phone("9000000009")
    farm = await repo.create_farm(farmer["farmer_id"], {
        "name": "F", "district_id": "thanjavur", "crop_id": "black_gram",
        "crop_stage_id": "flowering", "area_ha": 1.5,
    })
    return farmer["farmer_id"], farm["farm_id"]


async def test_farm_values_override_client_values(memory_repo):
    fid, farm_id = await _setup(memory_repo)

    async def factory():
        return memory_repo

    req = ConversationRequest(question="q", farm_id=farm_id, district="Chennai", crop="banana", area_ha=99)
    await _apply_farm(req, fid, factory)
    assert (req.district, req.crop, req.crop_stage, req.area_ha) == ("Thanjavur", "black gram", "flowering", 1.5)


async def test_other_farmers_farm_rejected(memory_repo):
    _, farm_id = await _setup(memory_repo)

    async def factory():
        return memory_repo

    with pytest.raises(HTTPException) as e:
        await _apply_farm(ConversationRequest(question="q", farm_id=farm_id), "someone-else", factory)
    assert e.value.status_code == 404


async def test_anonymous_farm_id_ignored(memory_repo):
    async def factory():
        raise AssertionError("must not touch the DB for anonymous requests")

    req = ConversationRequest(question="q", farm_id="x", district="Madurai")
    await _apply_farm(req, "anonymous", factory)
    assert req.farm_id is None and req.district == "Madurai"
