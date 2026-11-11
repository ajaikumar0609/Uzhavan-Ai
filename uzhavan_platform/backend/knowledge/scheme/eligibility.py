"""Scheme eligibility from backend/knowledge/scheme/eligibility_rules.yaml (API contract §6).

Statuses: eligible_known_criteria | not_eligible_known_criteria | more_information_required
| cannot_determine. Only criteria stated in the official source text are checked, only on
fields the app collects; nothing is assumed. See the YAML header for the policy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml

from backend.meta.catalog import CROP_IDS, crop_name_en, district_id_from_name, get_district

RULES_PATH = Path(__file__).resolve().parent / "eligibility_rules.yaml"
ALLOWED_FIELDS = {"district_id", "crop_id", "area_ha"}
UNSPECIFIC_CROPS = {"other"}   # "Other" does not tell us which crop → treated as unknown

NOTE_KNOWN_ONLY = {"en": "Only the criteria stated in the official source were checked. Documents, "
                         "selection and other conditions still apply; confirm with the agriculture office.",
                   "ta": None}


class RuleError(ValueError):
    pass


def _map_districts(names: list[str], scheme_id: str) -> set[str]:
    ids = set()
    for n in names:
        did = district_id_from_name(n)
        if did is None:
            raise RuleError(f"{scheme_id}: district name {n!r} does not map to a meta district id")
        ids.add(did)
    return ids


@lru_cache(maxsize=4)
def load_rules(path: str = str(RULES_PATH)) -> dict[str, dict[str, Any]]:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    out: dict[str, dict[str, Any]] = {}
    for r in doc.get("rules") or []:
        sid = r["scheme_id"]
        if not r.get("criteria_source_url") or not r.get("criteria_text"):
            raise RuleError(f"{sid}: criteria_source_url and criteria_text are required")
        conds = []
        for c in r.get("conditions") or []:
            if c["field"] not in ALLOWED_FIELDS:
                raise RuleError(f"{sid}: field {c['field']!r} is not collected by the app")
            cc = dict(c)
            if "in_districts" in c:
                cc["in_ids"] = _map_districts(c["in_districts"], sid)
            if "not_in_districts" in c:
                cc["not_in_ids"] = _map_districts(c["not_in_districts"], sid)
            if "in" in c and c["field"] == "crop_id":
                unknown = set(c["in"]) - CROP_IDS
                if unknown:
                    raise RuleError(f"{sid}: unknown crop ids {unknown}")
            conds.append(cc)
        if sid in out:
            raise RuleError(f"duplicate rule for {sid}")
        out[sid] = {**r, "conditions": conds, "requires": list(r.get("requires") or [])}
    return out


@dataclass
class _Outcome:
    status: str
    reasons: list[dict] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    label: Optional[str] = None


def _dname(did: Optional[str]) -> str:
    d = get_district(did or "")
    return d["name"]["en"] if d else str(did)


def _check(cond: dict[str, Any], ctx: dict[str, Any]) -> tuple[Optional[bool], str]:
    """(True|False|None=unknown, English reason)."""
    f = cond["field"]
    v = ctx.get(f)
    if f == "crop_id" and v in UNSPECIFIC_CROPS:
        v = None
    if v is None:
        return None, f"{f} not set"
    if "in_ids" in cond:
        ok = v in cond["in_ids"]
        return ok, f"district {_dname(v)} is {'in' if ok else 'not in'} the districts listed by the source"
    if "not_in_ids" in cond:
        ok = v not in cond["not_in_ids"]
        return ok, f"district {_dname(v)} is {'not ' if ok else ''}excluded by the source"
    if "in" in cond:
        ok = v in cond["in"]
        name = crop_name_en(v) or v
        return ok, f"crop {name} is {'' if ok else 'not '}covered ({', '.join(crop_name_en(c) or c for c in cond['in'])})"
    if "max" in cond:
        ok = float(v) <= float(cond["max"])
        return ok, f"{f} {v} {'<=' if ok else '>'} {cond['max']}"
    if "min" in cond:
        ok = float(v) >= float(cond["min"])
        return ok, f"{f} {v} {'>=' if ok else '<'} {cond['min']}"
    raise RuleError(f"condition without an operator: {cond}")


def _evaluate_ctx(rule: dict[str, Any], ctx: dict[str, Any]) -> _Outcome:
    failed, passed, missing = [], [], []
    for c in rule["conditions"]:
        ok, why = _check(c, ctx)
        if ok is None:
            missing.append(c["field"])
        elif ok:
            passed.append(why)
        else:
            failed.append(why)
    label = ctx.get("_label")
    prefix = f"{label}: " if label else ""
    if failed:
        return _Outcome("not_eligible_known_criteria",
                        [{"en": prefix + "Does not meet a stated criterion: " + "; ".join(failed) + ".", "ta": None}],
                        label=label)
    if missing or rule["requires"]:
        miss = missing + rule["requires"]
        reasons = [{"en": prefix + "More information is needed: " + ", ".join(miss) + ".", "ta": None}]
        if passed:
            reasons.append({"en": prefix + "Met so far: " + "; ".join(passed) + ".", "ta": None})
        return _Outcome("more_information_required", reasons, miss, label)
    return _Outcome("eligible_known_criteria",
                    [{"en": prefix + "Meets the stated criteria: " + "; ".join(passed) + ".", "ta": None}],
                    label=label)


def contexts(profile: Optional[dict[str, Any]], farms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One context per farm (farm district, else profile district); a profile-only context if no farms."""
    pdist = (profile or {}).get("district_id")
    if farms:
        return [{"district_id": f.get("district_id") or pdist, "crop_id": f.get("crop_id"),
                 "area_ha": f.get("area_ha"), "_label": f"Farm '{f.get('name')}'"} for f in farms]
    return [{"district_id": pdist, "crop_id": None, "area_ha": None, "_label": None}]


def evaluate(scheme: dict[str, Any], ctxs: list[dict[str, Any]],
             rules: Optional[dict[str, dict[str, Any]]] = None) -> dict[str, Any]:
    rules = load_rules() if rules is None else rules
    rule = rules.get(scheme["scheme_id"])
    extra = []
    if scheme.get("active") is False:
        extra.append({"en": "The official source marks this scheme as not active.", "ta": None})
    if rule is None:
        return {"status": "cannot_determine",
                "reasons": [{"en": "No verified eligibility rule for this scheme; read the official "
                                   "eligibility text or ask the agriculture office.", "ta": None}] + extra,
                "missing_fields": [], "criteria_source_url": scheme.get("official_url")}
    outcomes = [_evaluate_ctx(rule, c) for c in ctxs]
    for status in ("eligible_known_criteria", "more_information_required", "not_eligible_known_criteria"):
        chosen = [o for o in outcomes if o.status == status]
        if chosen:
            break
    missing: list[str] = []
    for o in chosen:
        for m in o.missing:
            if m not in missing:
                missing.append(m)
    reasons = [r for o in chosen for r in o.reasons]
    if rule.get("scope_note"):
        reasons.append({"en": rule["scope_note"], "ta": None})
    reasons += extra + [NOTE_KNOWN_ONLY]
    return {"status": status, "reasons": reasons, "missing_fields": missing,
            "criteria_source_url": rule["criteria_source_url"]}
