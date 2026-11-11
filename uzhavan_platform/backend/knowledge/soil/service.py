"""District soil reference data from the project's processed soil outputs (FP-014, contract §7).

Reads (read-only) uzhavan_data/04_soil/processed/:
- tn_mannvalam_district_major_soil_types.csv → `regional` (TN Agriculture Dept, Tamil Mannvalam)
- tn_shc_district_nutrient_status_long.csv   → `nutrient_status` (Soil Health Card dashboard shares)
- tn_district_soil_summary.csv               → `estimated` (ISRIC SoilGrids 2.0, 0-30 cm district means)
Nothing is labelled measured here; farmer-entered lab results live in `soil_tests`.
A missing file or district → that section is null.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from backend.meta.catalog import district_id_from_name

MANNVALAM_URL = "https://www.tnagrisnet.tn.gov.in/mannvalam/welcome/index/en"
SHC_URL = "https://soilhealth.dac.gov.in/"
SOILGRIDS_URL = "https://soilgrids.org"
SHC_MIN_SAMPLES = 100   # selection rule for the district's "latest" SHC record (see _pick_shc)

ESTIMATE_CAVEATS = [
    {"en": "Modelled estimate (ISRIC SoilGrids 250 m, averaged over the district); may differ strongly "
           "from field measurements; use a soil test.", "ta": None},
    {"en": "Project data audit: SoilGrids topsoil organic carbon (SOC) is far higher than Soil Health Card "
           "results (about 92% of Tamil Nadu samples are rated Low OC), and texture comes out as clay loam in "
           "every district although Tamil Nadu is mainly red soils. SOC and texture look implausible for "
           "Tamil Nadu; use them for relative patterns only.", "ta": None},
]
LOW_COVERAGE_CAVEAT = {"en": "Most of this district is masked (urban or water) in SoilGrids, so this estimate "
                             "rests on very few pixels.", "ta": None}

ESTIMATE_FIELDS = {  # contract key → (summary column, unit)
    "ph": ("phh2o_0-30cm_wmean", "pH (H2O)"),
    "soc_g_kg": ("soc_0-30cm_wmean", "g/kg"),
    "clay_pct": ("clay_0-30cm_wmean", "%"),
    "sand_pct": ("sand_0-30cm_wmean", "%"),
    "silt_pct": ("silt_0-30cm_wmean", "%"),
    "cec": ("cec_0-30cm_wmean", "cmol(c)/kg"),
    "bdod": ("bdod_0-30cm_wmean", "kg/dm3"),
    "nitrogen": ("nitrogen_0-30cm_wmean", "g/kg"),
}


def _read(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _num(v: Optional[str]) -> Optional[float]:
    if v is None or str(v).strip() == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _split_list(text: str) -> list[str]:
    return [p.strip().rstrip(".").strip() for p in (text or "").split(",") if p.strip().rstrip(".").strip()]


class SoilReference:
    def __init__(self, data_dir: Path) -> None:
        self.dir = Path(data_dir)
        self._regional = self._load_regional()
        self._shc = self._load_shc()
        self._est = self._load_estimates()

    # ── loaders ───────────────────────────────────────────────────────────────
    def _load_regional(self) -> dict[str, dict[str, Any]]:
        out = {}
        for r in _read(self.dir / "tn_mannvalam_district_major_soil_types.csv"):
            did = district_id_from_name(r.get("District_Name")) or district_id_from_name(r.get("district_geoboundaries"))
            en = _split_list(r.get("soils", ""))
            if not did or not en:
                continue
            ta = _split_list(r.get("soils_tamil", ""))
            paired = len(ta) == len(en)   # Tamil only when the source lists match one-to-one
            out[did] = {
                "soil_types": [{"name": {"en": e, "ta": ta[i] if paired else None}} for i, e in enumerate(en)],
                "zone": {"en": (r.get("zone") or "").strip() or None, "ta": (r.get("zone_tamil") or "").strip() or None},
                "source": "TN Agriculture Dept (Tamil Mannvalam)",
                "source_url": MANNVALAM_URL,
                "kind": "reference",
            }
        return out

    def _load_shc(self) -> dict[str, list[dict[str, Any]]]:
        recs: dict[tuple, dict[str, Any]] = {}
        for r in _read(self.dir / "tn_shc_district_nutrient_status_long.csv"):
            did = district_id_from_name(r.get("district_geoboundaries")) or district_id_from_name(r.get("district_shc"))
            if not did:
                continue
            key = (did, r["cycle"], r["scheme"])
            rec = recs.setdefault(key, {"district_id": did, "cycle": r["cycle"], "scheme": r["scheme"],
                                        "updated_at": r.get("shc_updated_at"), "params": defaultdict(dict),
                                        "totals": {}})
            p = r["parameter"]
            rec["params"][p][r["category"]] = (_num(r.get("pct")), _num(r.get("n_samples")))
            rec["totals"][p] = _num(r.get("param_total"))
        by_district: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for rec in recs.values():
            by_district[rec["district_id"]].append(rec)
        return by_district

    def _load_estimates(self) -> dict[str, dict[str, str]]:
        return {did: r for r in _read(self.dir / "tn_district_soil_summary.csv")
                if (did := district_id_from_name(r.get("district")))}

    # ── public ────────────────────────────────────────────────────────────────
    def regional(self, district_id: str) -> Optional[dict[str, Any]]:
        return self._regional.get(district_id)

    def _pick_shc(self, district_id: str) -> Optional[dict[str, Any]]:
        """Most recent cycle whose record has >= SHC_MIN_SAMPLES N samples; within it, the largest record."""
        recs = [r for r in self._shc.get(district_id, []) if (r["totals"].get("N") or 0) >= SHC_MIN_SAMPLES]
        if not recs:
            return None
        return max(recs, key=lambda r: (r["cycle"], r["totals"].get("N") or 0))

    def nutrient_status(self, district_id: str) -> Optional[dict[str, Any]]:
        rec = self._pick_shc(district_id)
        if rec is None:
            return None
        params = []
        for p, cats in rec["params"].items():
            def pct(c):
                return cats[c][0] if c in cats else None
            params.append({
                "param": p,
                "low_pct": pct("Low"), "medium_pct": pct("Medium"), "high_pct": pct("High"),
                "samples": int(rec["totals"][p]) if rec["totals"].get(p) is not None else None,
                "categories": [{"category": c, "pct": v[0], "samples": int(v[1]) if v[1] is not None else None}
                               for c, v in cats.items()],
            })
        return {"cycle": rec["cycle"], "scheme": rec["scheme"], "updated_at": rec["updated_at"],
                "parameters": params, "source": "Soil Health Card dashboard", "source_url": SHC_URL,
                "kind": "reference",
                "notes": [{"en": "Share of soil samples in each category for the whole district, not your field. "
                                 "Parameters without Low/Medium/High use the categories list "
                                 "(e.g. Deficient/Sufficient).", "ta": None}]}

    def estimated(self, district_id: str) -> Optional[dict[str, Any]]:
        r = self._est.get(district_id)
        if r is None:
            return None
        values = {k: (round(v, 2) if (v := _num(r.get(col))) is not None else None)
                  for k, (col, _u) in ESTIMATE_FIELDS.items()}
        caveats = list(ESTIMATE_CAVEATS)
        if (r.get("qc_flag") or "ok") != "ok":
            caveats.append(LOW_COVERAGE_CAVEAT)
        return {"depth": "0-30cm", "values": values, "units": {k: u for k, (_c, u) in ESTIMATE_FIELDS.items()},
                "source": "ISRIC SoilGrids 2.0", "source_url": SOILGRIDS_URL, "kind": "estimated",
                "caveats": caveats, "qc_flag": r.get("qc_flag")}


@lru_cache(maxsize=4)
def soil_reference(data_dir: str) -> SoilReference:
    return SoilReference(Path(data_dir))
