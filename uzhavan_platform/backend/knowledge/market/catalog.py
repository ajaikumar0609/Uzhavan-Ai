"""Commodities in the AGMARKNET snapshot (uzhavan_data/08_market, qc_summary.json).

Tamil names are standard common words only (several also appear in the former React app
data or in backend/meta CROPS: நெல், தக்காளி, வெங்காயம், வாழை, நிலக்கடலை, உளுந்து,
பாசிப்பயறு, மக்காச்சோளம், பருத்தி, மஞ்சள்). No other translation is invented.
"""
from __future__ import annotations

from typing import Any, Optional

PRICE_UNIT = "Rs/quintal"
COCONUT_UNIT_NOTE = "unit unverified (per quintal vs per 1000 nuts)"

_COMMODITIES: list[tuple[str, str, Optional[str]]] = [
    ("paddy", "Paddy", "நெல்"),
    ("rice", "Rice", "அரிசி"),
    ("banana", "Banana", "வாழை"),
    ("coconut", "Coconut", "தேங்காய்"),
    ("copra", "Copra", "கொப்பரை"),
    ("groundnut", "Groundnut", "நிலக்கடலை"),
    ("black_gram", "Black gram", "உளுந்து"),
    ("green_gram", "Green gram", "பாசிப்பயறு"),
    ("maize", "Maize", "மக்காச்சோளம்"),
    ("cotton", "Cotton", "பருத்தி"),
    ("turmeric", "Turmeric", "மஞ்சள்"),
    ("onion", "Onion", "வெங்காயம்"),
    ("tomato", "Tomato", "தக்காளி"),
    ("brinjal", "Brinjal", "கத்தரிக்காய்"),
]
COMMODITY_INDEX: dict[str, dict[str, Any]] = {
    cid: {"id": cid, "name": {"en": en, "ta": ta}, "unit": PRICE_UNIT,
          "unit_note": COCONUT_UNIT_NOTE if cid == "coconut" else None}
    for cid, en, ta in _COMMODITIES
}


def commodity(cid: str) -> dict[str, Any]:
    """Known commodity, or a record with the id as the English name and no Tamil."""
    return COMMODITY_INDEX.get(cid) or {"id": cid, "name": {"en": cid.replace("_", " ").capitalize(), "ta": None},
                                        "unit": PRICE_UNIT, "unit_note": None}
