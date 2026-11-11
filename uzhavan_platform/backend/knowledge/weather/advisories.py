"""Evaluate backend/knowledge/weather/advisory_rules.yaml against a daily forecast (contract §4).

Pure functions: no I/O besides reading the YAML once. A rule fires only when every
condition it declares is met by real values; a missing value never satisfies a condition.
"""
from __future__ import annotations

import operator
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml

RULES_PATH = Path(__file__).resolve().parent / "advisory_rules.yaml"
_OPS = {"gt": operator.gt, "gte": operator.ge, "lt": operator.lt, "lte": operator.le}


@lru_cache(maxsize=4)
def load_rules(path: str = str(RULES_PATH)) -> list[dict[str, Any]]:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    rules = doc.get("rules") or []
    for r in rules:
        src = r.get("rule_source") or {}
        if not (src.get("title") and src.get("page")):
            raise ValueError(f"advisory rule {r.get('rule_id')} has no citable source")
        if r.get("forecast", {}).get("op") not in _OPS:
            raise ValueError(f"advisory rule {r.get('rule_id')} has an unknown op")
    return rules


def evaluate(rules: list[dict[str, Any]], daily: list[dict[str, Any]],
             crop_id: Optional[str], crop_stage_id: Optional[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rules:
        if r.get("crops") and crop_id not in r["crops"]:
            continue
        if r.get("crop_stages") and crop_stage_id not in r["crop_stages"]:
            continue
        fc = r["forecast"]
        op = _OPS[fc["op"]]
        hits = [
            {"date": d.get("date"), fc["field"]: d.get(fc["field"])}
            for d in daily[: int(fc.get("days", 1))]
            if d.get(fc["field"]) is not None and op(d[fc["field"]], fc["value"])
        ]
        if not hits:
            continue
        out.append({
            "rule_id": r["rule_id"],
            "severity": r["severity"],
            "text": {"en": r["text"]["en"], "ta": r["text"].get("ta")},
            "evidence": {
                "crop_id": crop_id, "crop_stage_id": crop_stage_id,
                "condition": f"{fc['field']} {fc['op']} {fc['value']} within {fc.get('days', 1)} day(s)",
                "matched_days": hits,
            },
            "rule_source": r["rule_source"],
        })
    return out
