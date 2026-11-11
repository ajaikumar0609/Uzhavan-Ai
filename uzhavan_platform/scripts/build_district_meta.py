"""Build backend/meta/data/tn_districts.json from project data (read-only inputs).

Inputs:
  uzhavan_data/03_weather/processed/tn_district_hq_points.csv   (38 districts, HQ lat/lon; GeoNames CC BY 4.0)
  uzhavan_data/04_soil/soil_health_card/raw/tn_mannvalam/districts.json  (Tamil names, TN Agri Dept Mannvalam portal)

A Tamil name is set only when it is found in the Mannvalam list; otherwise it is null.
Run:  python scripts/build_district_meta.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "uzhavan_data"
HQ_CSV = DATA / "03_weather/processed/tn_district_hq_points.csv"
MANNVALAM = DATA / "04_soil/soil_health_card/raw/tn_mannvalam/districts.json"
OUT = ROOT / "backend/meta/data/tn_districts.json"

# Spelling differences between the HQ list (tn.gov.in) and the Mannvalam list (same districts).
ALIASES = {
    "kancheepuram": "kanchipuram",
    "thoothukudi": "tuticorin",
    "tiruvallur": "thiruvallur",
    "tiruvarur": "thiruvarur",
    "viluppuram": "villupuram",
}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def main() -> None:
    mannvalam = json.loads(MANNVALAM.read_text(encoding="utf-8"))
    tamil = {slug(r["District_Name_English"]): r["District_Name_tamil"].strip() for r in mannvalam}
    rows = list(csv.DictReader(HQ_CSV.open(encoding="utf-8")))
    out = []
    for r in rows:
        did = slug(r["district"])
        ta = tamil.get(did) or tamil.get(ALIASES.get(did, ""))
        out.append({
            "id": did,
            "name": {"en": r["district"], "ta": ta or None},
            "lat": round(float(r["lat"]), 5),
            "lon": round(float(r["lon"]), 5),
            "hq_town": r["hq_town"],
        })
    assert len(out) == 38, len(out)
    doc = {
        "source": {
            "coordinates": "GeoNames India extract via uzhavan_data/03_weather/processed/tn_district_hq_points.csv (CC BY 4.0)",
            "coordinates_url": "https://download.geonames.org/export/dump/IN.zip",
            "district_list_url": "https://www.tn.gov.in/district_list.php",
            "tamil_names": "Tamil Mannvalam portal, TN Dept of Agriculture - Farmers Welfare (uzhavan_data/04_soil/soil_health_card/raw/tn_mannvalam/districts.json)",
            "tamil_names_url": "https://www.tnagrisnet.tn.gov.in/mannvalam/welcome/index/en",
        },
        "districts": out,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    missing = [d["id"] for d in out if d["name"]["ta"] is None]
    print(f"wrote {OUT} ({len(out)} districts; tamil missing: {missing})")


if __name__ == "__main__":
    main()
