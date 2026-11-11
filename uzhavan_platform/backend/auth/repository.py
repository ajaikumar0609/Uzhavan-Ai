"""Persistence for auth, profile and farms (FP-008 / FP-009).

`Repository` is the interface the routes use. `PostgresRepository` is the production
implementation (asyncpg). Tests may substitute an in-memory implementation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

from backend.auth.otp import OTP_MAX_ATTEMPTS

FARM_COLUMNS = (
    "name", "district_id", "village", "latitude", "longitude", "boundary_geojson", "area_ha",
    "crop_id", "crop_stage_id", "season_id", "irrigation_type_id",
)
FARMER_UPDATABLE = ("name", "district_id", "village", "preferred_language")


class Repository(Protocol):
    # OTP
    async def save_otp(self, phone: str, otp_hash: str, expires_at: datetime) -> None: ...
    async def get_latest_otp(self, phone: str) -> Optional[dict[str, Any]]: ...
    async def consume_otp_attempt(self, otp_id: int) -> Optional[int]: ...
    async def mark_otp_verified(self, otp_id: int) -> None: ...
    # Farmers
    async def upsert_farmer_by_phone(self, phone: str) -> tuple[dict[str, Any], bool]: ...
    async def get_farmer(self, farmer_id: str) -> Optional[dict[str, Any]]: ...
    async def update_farmer(self, farmer_id: str, fields: dict[str, Any]) -> Optional[dict[str, Any]]: ...
    # Refresh tokens
    async def save_refresh_token(self, farmer_id: str, token_hash: str, expires_at: datetime,
                                 user_agent: Optional[str], ip: Optional[str]) -> None: ...
    async def rotate_refresh_token(self, old_hash: str, new_hash: str, new_expires_at: datetime,
                                   user_agent: Optional[str], ip: Optional[str]) -> tuple[str, Optional[dict[str, Any]]]: ...
    async def revoke_refresh_token(self, farmer_id: str, token_hash: str) -> None: ...
    # Farms
    async def list_farms(self, farmer_id: str) -> list[dict[str, Any]]: ...
    async def count_farms(self, farmer_id: str) -> int: ...
    async def get_farm(self, farm_id: str) -> Optional[dict[str, Any]]: ...
    async def create_farm(self, farmer_id: str, fields: dict[str, Any]) -> dict[str, Any]: ...
    async def update_farm(self, farm_id: str, fields: dict[str, Any]) -> Optional[dict[str, Any]]: ...
    async def delete_farm(self, farm_id: str) -> None: ...


def _uuid_or_none(value: str):
    import uuid
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def _row(row) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    d = dict(row)
    for k in ("farmer_id", "farm_id"):
        if k in d and d[k] is not None:
            d[k] = str(d[k])
    if isinstance(d.get("boundary_geojson"), str):
        d["boundary_geojson"] = json.loads(d["boundary_geojson"])
    return d


_FARMER_SELECT = """
    SELECT farmer_id, phone, name, district_id, village, preferred_language, created_at, updated_at
    FROM farmers
"""
_FARM_SELECT = "SELECT farm_id, farmer_id, " + ", ".join(FARM_COLUMNS) + ", created_at, updated_at FROM farms"


class PostgresRepository:
    def __init__(self, pool) -> None:
        self._pool = pool

    # ── OTP ───────────────────────────────────────────────────────────────────
    async def save_otp(self, phone: str, otp_hash: str, expires_at: datetime) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO otp_requests (phone, otp_hash, expires_at) VALUES ($1, $2, $3)",
                phone, otp_hash, expires_at,
            )

    async def get_latest_otp(self, phone: str) -> Optional[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT id, otp_hash, expires_at, attempts, verified FROM otp_requests
                   WHERE phone = $1 AND verified = FALSE ORDER BY created_at DESC, id DESC LIMIT 1""",
                phone,
            )
        return _row(row)

    async def consume_otp_attempt(self, otp_id: int) -> Optional[int]:
        """Atomically count one attempt; returns the new count, or None if the cap was already hit."""
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                "UPDATE otp_requests SET attempts = attempts + 1 WHERE id = $1 AND attempts < $2 RETURNING attempts",
                otp_id, OTP_MAX_ATTEMPTS,
            )

    async def mark_otp_verified(self, otp_id: int) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("UPDATE otp_requests SET verified = TRUE WHERE id = $1", otp_id)

    # ── Farmers ───────────────────────────────────────────────────────────────
    async def upsert_farmer_by_phone(self, phone: str) -> tuple[dict[str, Any], bool]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO farmers (phone, preferred_language) VALUES ($1, 'ta')
                   ON CONFLICT (phone) DO NOTHING
                   RETURNING farmer_id, phone, name, district_id, village, preferred_language, created_at, updated_at""",
                phone,
            )
            if row is not None:
                return _row(row), True
            row = await conn.fetchrow(_FARMER_SELECT + " WHERE phone = $1", phone)
            return _row(row), False

    async def get_farmer(self, farmer_id: str) -> Optional[dict[str, Any]]:
        fid = _uuid_or_none(farmer_id)
        if fid is None:
            return None
        async with self._pool.acquire() as conn:
            return _row(await conn.fetchrow(_FARMER_SELECT + " WHERE farmer_id = $1", fid))

    async def update_farmer(self, farmer_id: str, fields: dict[str, Any]) -> Optional[dict[str, Any]]:
        fid = _uuid_or_none(farmer_id)
        if fid is None:
            return None
        cols = [c for c in FARMER_UPDATABLE if c in fields]
        if not cols:
            return await self.get_farmer(farmer_id)
        sets = ", ".join(f"{c} = ${i + 2}" for i, c in enumerate(cols))
        # Keep the legacy free-text `district` column in step with district_id.
        extra = ""
        values = [fields[c] for c in cols]
        if "district_id" in fields:
            extra = f", district = ${len(cols) + 2}"
            values.append(fields.get("_district_name"))
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"UPDATE farmers SET {sets}{extra}, updated_at = NOW() WHERE farmer_id = $1 "
                "RETURNING farmer_id, phone, name, district_id, village, preferred_language, created_at, updated_at",
                fid, *values,
            )
        return _row(row)

    # ── Refresh tokens ────────────────────────────────────────────────────────
    async def save_refresh_token(self, farmer_id: str, token_hash: str, expires_at: datetime,
                                 user_agent: Optional[str], ip: Optional[str]) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO refresh_tokens (farmer_id, token_hash, expires_at, user_agent, ip_address)
                   VALUES ($1, $2, $3, $4, $5::inet)""",
                _uuid_or_none(farmer_id), token_hash, expires_at, user_agent, _safe_ip(ip),
            )

    async def rotate_refresh_token(self, old_hash: str, new_hash: str, new_expires_at: datetime,
                                   user_agent: Optional[str], ip: Optional[str]) -> tuple[str, Optional[dict[str, Any]]]:
        """Returns (status, farmer). status: ok | not_found | reused | expired.
        On reuse of a revoked token, all of that farmer's tokens are revoked."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """SELECT token_id, farmer_id, expires_at, revoked FROM refresh_tokens
                       WHERE token_hash = $1 FOR UPDATE""",
                    old_hash,
                )
                if row is None:
                    return "not_found", None
                if row["revoked"]:
                    await conn.execute(
                        """UPDATE refresh_tokens SET revoked = TRUE, revoked_at = COALESCE(revoked_at, NOW())
                           WHERE farmer_id = $1 AND revoked = FALSE""",
                        row["farmer_id"],
                    )
                    return "reused", None
                if row["expires_at"] <= datetime.now(timezone.utc):
                    await conn.execute(
                        "UPDATE refresh_tokens SET revoked = TRUE, revoked_at = NOW() WHERE token_id = $1",
                        row["token_id"],
                    )
                    return "expired", None
                await conn.execute(
                    "UPDATE refresh_tokens SET revoked = TRUE, revoked_at = NOW() WHERE token_id = $1",
                    row["token_id"],
                )
                await conn.execute(
                    """INSERT INTO refresh_tokens (farmer_id, token_hash, expires_at, user_agent, ip_address)
                       VALUES ($1, $2, $3, $4, $5::inet)""",
                    row["farmer_id"], new_hash, new_expires_at, user_agent, _safe_ip(ip),
                )
                farmer = await conn.fetchrow(_FARMER_SELECT + " WHERE farmer_id = $1", row["farmer_id"])
                return "ok", _row(farmer)

    async def revoke_refresh_token(self, farmer_id: str, token_hash: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """UPDATE refresh_tokens SET revoked = TRUE, revoked_at = COALESCE(revoked_at, NOW())
                   WHERE token_hash = $1 AND farmer_id = $2""",
                token_hash, _uuid_or_none(farmer_id),
            )

    # ── Farms ─────────────────────────────────────────────────────────────────
    async def list_farms(self, farmer_id: str) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(_FARM_SELECT + " WHERE farmer_id = $1 ORDER BY created_at", _uuid_or_none(farmer_id))
        return [_row(r) for r in rows]

    async def count_farms(self, farmer_id: str) -> int:
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM farms WHERE farmer_id = $1", _uuid_or_none(farmer_id))

    async def get_farm(self, farm_id: str) -> Optional[dict[str, Any]]:
        fid = _uuid_or_none(farm_id)
        if fid is None:
            return None
        async with self._pool.acquire() as conn:
            return _row(await conn.fetchrow(_FARM_SELECT + " WHERE farm_id = $1", fid))

    async def create_farm(self, farmer_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        cols = list(FARM_COLUMNS)
        values = [_db_value(c, fields.get(c)) for c in cols]
        placeholders = ", ".join(f"${i + 2}" + ("::jsonb" if c == "boundary_geojson" else "") for i, c in enumerate(cols))
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"INSERT INTO farms (farmer_id, {', '.join(cols)}) VALUES ($1, {placeholders}) RETURNING farm_id",
                _uuid_or_none(farmer_id), *values,
            )
        return await self.get_farm(str(row["farm_id"]))  # type: ignore[return-value]

    async def update_farm(self, farm_id: str, fields: dict[str, Any]) -> Optional[dict[str, Any]]:
        cols = [c for c in FARM_COLUMNS if c in fields]
        if cols:
            sets = ", ".join(
                f"{c} = ${i + 2}" + ("::jsonb" if c == "boundary_geojson" else "") for i, c in enumerate(cols)
            )
            async with self._pool.acquire() as conn:
                await conn.execute(
                    f"UPDATE farms SET {sets}, updated_at = NOW() WHERE farm_id = $1",
                    _uuid_or_none(farm_id), *[_db_value(c, fields[c]) for c in cols],
                )
        return await self.get_farm(farm_id)

    async def delete_farm(self, farm_id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM farms WHERE farm_id = $1", _uuid_or_none(farm_id))


def _db_value(col: str, value: Any) -> Any:
    if col == "boundary_geojson" and value is not None:
        return json.dumps(value)
    return value


def _safe_ip(ip: Optional[str]) -> Optional[str]:
    import ipaddress
    if not ip:
        return None
    try:
        return str(ipaddress.ip_address(ip))
    except ValueError:
        return None
