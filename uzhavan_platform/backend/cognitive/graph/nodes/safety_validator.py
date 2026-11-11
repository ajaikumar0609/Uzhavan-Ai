"""
Safety Validator Node

Input:  raw_llm_response, context (language), evidence
Output: safety_passed, safety_failures

One job: post-generation quality gate.
Five deterministic checks — no LLM.
If safety fails → formatter outputs Tamil fallback.
"""
from __future__ import annotations

import re
from typing import Any

from backend.cognitive.models.node_context import EvidenceBundle
from backend.cognitive.observability import observe

_BANNED_PHRASES = [
    "as an ai", "i am an ai", "i'm an ai",
    "i don't know", "i cannot help", "i'm not sure",
    "consult a doctor", "i cannot provide", "i'm unable to",
    "sorry, i", "நான் ஒரு AI", "என்னால் முடியாது",
]

_MIN_RESPONSE_LENGTH = 10
_MAX_RESPONSE_LENGTH = 3000


def _has_tamil_content(text: str) -> bool:
    return any(0x0B80 <= ord(c) <= 0x0BFF for c in text)


def _check_response_exists(response: str) -> str | None:
    if not response or len(response.strip()) < _MIN_RESPONSE_LENGTH:
        return "empty_response: Response is too short or empty"
    if len(response) > _MAX_RESPONSE_LENGTH:
        return f"response_too_long: Response exceeds {_MAX_RESPONSE_LENGTH} chars"
    return None


def _check_language(response: str, required_language: str) -> str | None:
    if required_language.lower() == "tamil" and not _has_tamil_content(response):
        return "language_mismatch: Tamil response expected but no Tamil characters found"
    return None


def _check_banned_phrases(response: str) -> str | None:
    response_lower = response.lower()
    for phrase in _BANNED_PHRASES:
        if phrase.lower() in response_lower:
            return f"banned_phrase: Response contains disallowed phrase: '{phrase}'"
    return None


# ── FP-015 numeric grounding ─────────────────────────────────────────────────
# Only numbers that carry a price / temperature / percentage / rainfall / weight unit are
# checked (conservative: plain counts, dates, phone numbers and step numbers are ignored).
_NUM = r"(\d[\d,]*(?:\.\d+)?)"
_RANGE = _NUM + r"(?:\s*(?:-|–|to|முதல்)\s*" + _NUM + r")?"
_UNIT_AFTER = (
    r"(?:°\s*[CF]?|degrees?\b|டிகிரி|செல்சியஸ்"                     # temperature
    r"|%|percent\b|per\s*cent\b|சதவீத\w*|சதவிகித\w*"                # percentage
    r"|mm\b|மிமீ|மி\.மீ|millimet\w*"                                 # rainfall
    r"|kg\b|kgs\b|கிலோ|kilogram\w*"                                  # quantities / soil
    r"|rupees?\b|rs\b\.?|inr\b|ரூபாய்\w*|ரூ\b|/-)"                  # price after the number
)
_CURRENCY_BEFORE = r"(?:₹|rs\.?|inr|ரூ\.?|rupees?)\s*"
_CHECKED_PATTERNS = [
    re.compile(_RANGE + r"\s*" + _UNIT_AFTER, re.IGNORECASE),
    re.compile(_CURRENCY_BEFORE + _RANGE, re.IGNORECASE),
]
_ANY_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _to_float(token: str) -> float | None:
    try:
        return float(token.replace(",", ""))
    except ValueError:
        return None


def checked_numbers(text: str) -> list[float]:
    """Unit-bearing numbers in an answer (prices, °C, %, mm, kg)."""
    found: list[float] = []
    for pattern in _CHECKED_PATTERNS:
        for m in pattern.finditer(text or ""):
            for g in m.groups():
                v = _to_float(g) if g else None
                if v is not None:
                    found.append(v)
    return found


def allowed_numbers(*texts: str) -> set[float]:
    """Every number that appears anywhere in the evidence payload / question."""
    out: set[float] = set()
    for t in texts:
        for tok in _ANY_NUMBER.findall(t or ""):
            v = _to_float(tok)
            if v is not None:
                out.add(v)
    return out


def _is_allowed(value: float, allowed: set[float]) -> bool:
    if value in allowed:
        return True
    # Quoting a value with less precision is fine (29.7 → 30, 2345.5 → 2345.5 / 2346).
    return any(round(a) == value or round(a, 1) == value for a in allowed)


def evidence_texts(state: dict[str, Any]) -> list[str]:
    """The evidence payload the LLM was given, plus the question and farm line."""
    texts: list[str] = [state.get("user_prompt", ""), state.get("user_message", "")]
    ctx = state.get("context")
    if ctx is not None:
        texts.append(ctx.current_question or "")
    ev: EvidenceBundle | None = state.get("evidence")
    if ev is not None:
        texts += list(ev.facts) + list(ev.rag_excerpts)
        texts += [x for x in (ev.weather_summary, ev.crop_summary, ev.disease_summary,
                              ev.market_summary, ev.scheme_summary) if x]
        texts += [f"{c.title} {c.excerpt}" for c in ev.citations]
        texts += [c.excerpt for c in ev.retrieved_chunks]   # full retrieved TNAU chunk text
    for r in state.get("tool_results") or []:
        if r.tool.startswith("rag.") and isinstance(r.data, list):
            texts += [getattr(c, "excerpt", "") or "" for c in r.data]
    return texts


# Chemical / fertiliser application rates: "<n> ml|g|kg|cc" followed, in the same sentence, by a
# volume or area word ("per litre", "in 10 litres of water", "/ha", "per acre", "/tank" ...).
_DOSE_UNIT = r"(?:ml|grams?|gms|gm|g|kg|cc|மில்லி|மிலி|கிராம்|கிலோ)"
_DOSE_PER = (r"(?:litres?|liters?|lit|l|ha|hectares?|acres?|plants?|tanks?|pumps?|vines?|trees?|"
             r"லிட்டர்|லி|ஹெக்டேர்|ஏக்கர்|செடி)")
_DOSAGE_RE = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*(" + _DOSE_UNIT + r")(?![A-Za-z])[^.\n]{0,40}?(?<![A-Za-z])" + _DOSE_PER + r"(?![A-Za-z])",
    re.IGNORECASE,
)


_UNIT_FAMILY = {
    "ml": ("ml", "cc", "மில்லி", "மிலி"), "cc": ("ml", "cc", "மில்லி", "மிலி"),
    "மில்லி": ("ml", "cc", "மில்லி", "மிலி"), "மிலி": ("ml", "cc", "மில்லி", "மிலி"),
    "kg": ("kg", "கிலோ"), "கிலோ": ("kg", "கிலோ"),
}
_G_FAMILY = ("g", "gm", "gms", "gram", "grams", "கிராம்")


def _unit_alternation(unit: str) -> str:
    fam = _UNIT_FAMILY.get(unit.lower(), _UNIT_FAMILY.get(unit))
    if fam is None:
        fam = _G_FAMILY
    return "(?:" + "|".join(re.escape(u) for u in sorted(fam, key=len, reverse=True)) + ")"


def _dose_in_evidence(value: float, unit: str, evidence: str) -> bool:
    """True only if the evidence states this number WITH the same unit (e.g. "2.5 ml").
    A bare number match is meaningless: "2" appears in almost any text."""
    forms = {f"{value:g}", f"{value:.1f}", f"{value:.2f}".rstrip("0").rstrip(".")}
    num = "(?:" + "|".join(re.escape(f) for f in forms) + ")"
    pat = re.compile(r"(?<![\d.])" + num + r"\s*" + _unit_alternation(unit) + r"(?![A-Za-z])", re.IGNORECASE)
    return bool(pat.search(evidence))


_RATE_PER_HA = re.compile(r"(\d[\d.]*)\s*kg\s*(?:/|per)\s*(?:ha|hectare)", re.IGNORECASE)
_AREA_HA = re.compile(r"area\D{0,12}?(\d[\d.]*)\s*ha\b", re.IGNORECASE)
_AREA_ACRE = re.compile(r"(\d[\d.]*)\s*acres?\b", re.IGNORECASE)


def _derived_field_totals(evidence: str) -> list[float]:
    """kg totals obtainable as (kg/ha rate stated in the evidence) x (farm area stated in the evidence)."""
    rates = [float(x) for x in _RATE_PER_HA.findall(evidence) if _to_float(x) is not None]
    areas = [float(x) for x in _AREA_HA.findall(evidence) if _to_float(x) is not None]
    areas += [float(x) * 0.404686 for x in _AREA_ACRE.findall(evidence) if _to_float(x) is not None]
    return [r * a for r in rates for a in areas]


def check_chemical_dosage_grounding(response: str, state: dict[str, Any]) -> str | None:
    """Zero-paid-API / safety policy: an exact chemical or fertiliser rate may only be stated if
    that number, with its unit, appears in the evidence given to the model (tool facts or
    retrieved TNAU text). Applies in EVERY grounding mode. The model's recollection of a dose is
    never accepted. (Limitation: this verifies the figure exists in the evidence, not that it
    belongs to the same chemical.)"""
    matches = list(_DOSAGE_RE.finditer(response or ""))
    if not matches:
        return None
    evidence = " ".join(evidence_texts(state)).replace(",", "")
    derived = _derived_field_totals(evidence)
    bad = []
    for m in matches:
        v = _to_float(m.group(1))
        if v is None:
            continue
        if _dose_in_evidence(v, m.group(2), evidence):
            continue
        # Verified derivation: "<rate> kg/ha" in the evidence x the recorded farm area. This only
        # accepts the arithmetic of a rate the evidence already states; invented doses still fail.
        if m.group(2).lower() in ("kg", "கிலோ") and any(abs(v - t) <= max(0.6, 0.01 * t) for t in derived):
            continue
        bad.append(m.group(0).strip())
    if bad:
        return "unverified_chemical_dosage: answer states a dose not present in the evidence (" + "; ".join(bad[:3]) + ")"
    return None


def check_numeric_grounding(response: str, state: dict[str, Any]) -> str | None:
    grounding_mode = state.get("grounding_mode", "grounded_verified")
    dosage_failure = check_chemical_dosage_grounding(response, state)
    if dosage_failure:
        return dosage_failure

    # In general guidance or casual conversation, conceptual numbers (e.g. NPK ratios, percentages, growth stages, days) are expected and permitted.
    # However, hallucinated chemical spray dosages (e.g. ml/L, g/L) MUST still be strictly blocked!
    if grounding_mode in ("general_guidance", "safety_critical_unverified"):
        chemical_dosage_pattern = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(?:ml\/l|g\/l|மில்லி\/லி|கிராம்\/லி)", re.IGNORECASE)
        match = chemical_dosage_pattern.search(response or "")
        if match and grounding_mode == "safety_critical_unverified":
            return f"unverified_chemical_dosage: answer suggests specific chemical dosage {match.group(0)} without verified source"
        return None

    allowed = allowed_numbers(*evidence_texts(state))
    ungrounded = sorted({v for v in checked_numbers(response) if not _is_allowed(v, allowed)})
    if ungrounded:
        shown = ", ".join(f"{v:g}" for v in ungrounded[:5])
        return f"ungrounded_number: answer states values not present in the evidence ({shown})"
    return None


def _check_has_content(response: str) -> str | None:
    if len(response.strip().split()) < 3:
        return "insufficient_content: Response lacks substantive content"
    return None


async def safety_validator(state: dict[str, Any]) -> dict[str, Any]:
    with observe("safety_validator", state):
        response: str = state.get("raw_llm_response", "")
        context = state["context"]
        is_fallback: bool = state.get("is_fallback", False)

        if is_fallback:
            output: dict[str, Any] = {"safety_passed": True, "safety_failures": []}
        else:
            language = context.system.language or context.farmer.language or "Tamil"
            failures: list[str] = []
            for check_fn in (
                lambda: _check_response_exists(response),
                lambda: _check_language(response, language),
                lambda: _check_banned_phrases(response),
                lambda: _check_has_content(response),
                lambda: check_numeric_grounding(response, state),
            ):
                failure = check_fn()
                if failure:
                    failures.append(failure)
            output = {
                "safety_passed": len(failures) == 0,
                "safety_failures": failures,
            }
    output["trace"] = state.get("trace", [])
    return output
