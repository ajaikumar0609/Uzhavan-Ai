"""Data envelope for information endpoints (API contract M-06 §0).

{ "data": ..., "meta": { source, source_url, kind, retrieved_at, observed_at, location, notes } }
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

KINDS = {"current", "forecast", "historical", "latest_observed", "estimated", "measured", "reference"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso_utc(dt: Optional[datetime]) -> Optional[str]:
    """ISO-8601 UTC with a trailing Z; None stays None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_date(d: Optional[date]) -> Optional[str]:
    if d is None:
        return None
    if isinstance(d, datetime):
        d = d.date()
    return d.isoformat()


def note(en: str, ta: Optional[str] = None) -> dict[str, Optional[str]]:
    return {"en": en, "ta": ta}


def envelope(
    data: Any,
    *,
    source: str,
    source_url: Optional[str],
    kind: str,
    observed_at: Optional[str] = None,
    location: Optional[dict[str, Any]] = None,
    notes: Optional[list[dict[str, Optional[str]]]] = None,
    retrieved_at: Optional[str] = None,
) -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError(f"unknown meta.kind {kind!r}")
    return {
        "data": data,
        "meta": {
            "source": source,
            "source_url": source_url,
            "kind": kind,
            "retrieved_at": retrieved_at or iso_utc(utc_now()),
            "observed_at": observed_at,
            "location": location,
            "notes": notes or [],
        },
    }
