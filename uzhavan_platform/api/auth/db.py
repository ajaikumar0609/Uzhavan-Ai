"""Deprecated shim: persistence lives in backend/auth/repository.py (FP-008/FP-009)."""
from backend.auth.repository import PostgresRepository, Repository  # noqa: F401
