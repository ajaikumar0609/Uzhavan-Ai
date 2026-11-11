"""In-memory test doubles for the auth/profile/farm Repository and the SMS provider."""
from __future__ import annotations

import copy
import itertools
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from backend.auth.otp import OTP_MAX_ATTEMPTS
from backend.auth.repository import FARM_COLUMNS, FARMER_UPDATABLE


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryRepository:
    def __init__(self) -> None:
        self.otps: list[dict[str, Any]] = []
        self.farmers: dict[str, dict[str, Any]] = {}
        self.refresh: dict[str, dict[str, Any]] = {}
        self.farms: dict[str, dict[str, Any]] = {}
        self._ids = itertools.count(1)

    # OTP
    async def save_otp(self, phone, otp_hash, expires_at):
        self.otps.append({"id": next(self._ids), "phone": phone, "otp_hash": otp_hash,
                          "expires_at": expires_at, "attempts": 0, "verified": False})

    async def get_latest_otp(self, phone):
        for rec in reversed(self.otps):
            if rec["phone"] == phone and not rec["verified"]:
                return dict(rec)
        return None

    def _otp(self, otp_id):
        return next(r for r in self.otps if r["id"] == otp_id)

    async def consume_otp_attempt(self, otp_id):
        rec = self._otp(otp_id)
        if rec["attempts"] >= OTP_MAX_ATTEMPTS:
            return None
        rec["attempts"] += 1
        return rec["attempts"]

    async def mark_otp_verified(self, otp_id):
        self._otp(otp_id)["verified"] = True

    # Farmers
    async def upsert_farmer_by_phone(self, phone):
        for f in self.farmers.values():
            if f["phone"] == phone:
                return dict(f), False
        fid = str(uuid.uuid4())
        f = {"farmer_id": fid, "phone": phone, "name": None, "district_id": None, "village": None,
             "preferred_language": "ta", "created_at": _now(), "updated_at": _now()}
        self.farmers[fid] = f
        return dict(f), True

    async def get_farmer(self, farmer_id):
        f = self.farmers.get(farmer_id)
        return dict(f) if f else None

    async def update_farmer(self, farmer_id, fields):
        f = self.farmers.get(farmer_id)
        if f is None:
            return None
        for k in FARMER_UPDATABLE:
            if k in fields:
                f[k] = fields[k]
        f["updated_at"] = _now()
        return dict(f)

    # Refresh tokens
    async def save_refresh_token(self, farmer_id, token_hash, expires_at, user_agent, ip):
        self.refresh[token_hash] = {"farmer_id": farmer_id, "expires_at": expires_at, "revoked": False}

    async def rotate_refresh_token(self, old_hash, new_hash, new_expires_at, user_agent, ip):
        rec = self.refresh.get(old_hash)
        if rec is None:
            return "not_found", None
        if rec["revoked"]:
            for r in self.refresh.values():
                if r["farmer_id"] == rec["farmer_id"]:
                    r["revoked"] = True
            return "reused", None
        rec["revoked"] = True
        if rec["expires_at"] <= _now():
            return "expired", None
        await self.save_refresh_token(rec["farmer_id"], new_hash, new_expires_at, user_agent, ip)
        return "ok", dict(self.farmers[rec["farmer_id"]])

    async def revoke_refresh_token(self, farmer_id, token_hash):
        rec = self.refresh.get(token_hash)
        if rec and rec["farmer_id"] == farmer_id:
            rec["revoked"] = True

    # Farms
    async def list_farms(self, farmer_id):
        return [copy.deepcopy(f) for f in self.farms.values() if f["farmer_id"] == farmer_id]

    async def count_farms(self, farmer_id):
        return len(await self.list_farms(farmer_id))

    async def get_farm(self, farm_id):
        f = self.farms.get(farm_id)
        return copy.deepcopy(f) if f else None

    async def create_farm(self, farmer_id, fields):
        fid = str(uuid.uuid4())
        f = {"farm_id": fid, "farmer_id": farmer_id, **{c: fields.get(c) for c in FARM_COLUMNS},
             "created_at": _now(), "updated_at": _now()}
        self.farms[fid] = f
        return copy.deepcopy(f)

    async def update_farm(self, farm_id, fields):
        f = self.farms.get(farm_id)
        if f is None:
            return None
        for c in FARM_COLUMNS:
            if c in fields:
                f[c] = fields[c]
        f["updated_at"] = _now()
        return copy.deepcopy(f)

    async def delete_farm(self, farm_id):
        self.farms.pop(farm_id, None)


class CapturingSmsProvider:
    """Test-only provider: records the OTP so tests can complete the flow (never logs)."""
    name = "capture"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_otp(self, phone: str, otp: str) -> None:
        self.sent.append((phone, otp))

    def last_for(self, phone: str) -> Optional[str]:
        for p, o in reversed(self.sent):
            if p == phone:
                return o
        return None


class InMemoryDiaryStore:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    async def add(self, farmer_id, kind, text, *, farm_id=None, amount_inr=None, entry_date=None, ref=None):
        from datetime import date as _date
        e = {"entry_id": str(uuid.uuid4()), "farmer_id": farmer_id, "farm_id": farm_id, "kind": kind,
             "text": text[:1000], "amount_inr": amount_inr, "entry_date": entry_date or _date.today(),
             "ref": ref, "created_at": _now()}
        self.entries.append(e)
        return dict(e)

    async def list(self, farmer_id, limit):
        rows = [dict(e) for e in self.entries if e["farmer_id"] == farmer_id]
        rows.sort(key=lambda e: (e["entry_date"], e["created_at"]), reverse=True)
        return rows[:limit]
