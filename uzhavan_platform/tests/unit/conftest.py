"""Make the repo-root ``scripts`` package importable from the platform test run.

``scripts`` is a namespace package (no __init__.py) that exists in two places:
``<repo>/scripts`` (ingest_sentinel2.py) and ``uzhavan_platform/scripts`` (loaders).
When pytest runs from ``uzhavan_platform/`` only the latter is on sys.path, so
``from scripts.ingest_sentinel2 import ...`` failed at collection. Appending (never
prepending) the repo root lets the namespace package span both directories without
shadowing any platform module.
"""
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT not in sys.path:
    sys.path.append(_REPO_ROOT)
