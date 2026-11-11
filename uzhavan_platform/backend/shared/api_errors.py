"""Contract error format (API_CONTRACT_M06 §0):
{ "detail": { "code": "snake_case_code", "message": {"en": "...", "ta": "..." | null} } }

`ta` is null unless a verified translation exists; the client then shows `en`.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException


def bilingual(en: str, ta: Optional[str] = None) -> dict[str, Optional[str]]:
    return {"en": en, "ta": ta}


def api_error(
    status_code: int,
    code: str,
    en: str,
    ta: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": bilingual(en, ta)},
        headers=headers,
    )


def unauthenticated(en: str = "Authentication required") -> HTTPException:
    return api_error(401, "unauthenticated", en, headers={"WWW-Authenticate": "Bearer"})


def not_found(en: str = "Not found") -> HTTPException:
    return api_error(404, "not_found", en)


def service_unavailable(en: str = "Service temporarily unavailable") -> HTTPException:
    return api_error(503, "service_unavailable", en)
