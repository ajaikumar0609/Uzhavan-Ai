#!/usr/bin/env python3
"""
UZHAVAN AI — TNAU Knowledge Normalizer
=======================================
Reads all crawled TNAU content (HTML/Markdown/CSV) and produces:
  - crops.csv, fertilizers.csv, diseases.csv, pests.csv
  - crop_calendar.csv, soil_types.csv, government_schemes.csv
  - farm_machinery.csv, district_profiles.csv
  - rag_chunks/ (RAG-ready Markdown chunks)
  - output.json (complete normalized JSON)
  - output.parquet (columnar format for analytics)
  - seeds.sql (PostgreSQL INSERT statements)

Usage:
  python normalize_tnau.py
  python normalize_tnau.py --knowledge-base ../tnau_crawler/knowledge_base
  python normalize_tnau.py --output-dir ../database/data --export-parquet
"""

import argparse
import csv
import json
import re
import hashlib
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("normalize")

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

KNOWLEDGE_BASE = Path("../tnau_crawler/knowledge_base")
OUTPUT_DIR     = Path("../database/data")
RAG_DIR        = Path("../rag/chunks")

CROP_ALIASES: Dict[str, str] = {
    "paddy": "Rice", "oryza sativa": "Rice", "நெல்": "Rice",
    "jowar": "Sorghum", "சோளம்": "Sorghum",
    "cumbu": "Pearl Millet", "கம்பு": "Pearl Millet",
    "ragi": "Finger Millet", "கேழ்வரகு": "Finger Millet",
    "redgram": "Pigeonpea", "tur": "Pigeonpea", "arhar": "Pigeonpea",
    "blackgram": "Urad", "urad": "Urad", "உளுந்து": "Urad",
    "greengram": "Moong", "moong": "Moong",
    "bengalgram": "Chickpea", "chickpea": "Chickpea", "gram": "Chickpea",
    "gingelly": "Sesame", "til": "Sesame",
    "groundnut": "Groundnut", "peanut": "Groundnut",
    "bhendi": "Okra", "ladyfinger": "Okra", "வெண்டை": "Okra",
    "drumstick": "Moringa", "moringa": "Moringa",
    "brinjal": "Eggplant", "eggplant": "Eggplant",
    "cumbu napier": "Napier Grass",
    "maize": "Maize", "corn": "Maize", "மக்காசோளம்": "Maize",
}

FERTILIZER_ALIASES: Dict[str, str] = {
    "dap": "DAP (Diammonium Phosphate)",
    "diammonium phosphate": "DAP (Diammonium Phosphate)",
    "mop": "MOP (Muriate of Potash)",
    "muriate of potash": "MOP (Muriate of Potash)",
    "potassium chloride": "MOP (Muriate of Potash)",
    "ssp": "SSP (Single Super Phosphate)",
    "single super phosphate": "SSP (Single Super Phosphate)",
    "fym": "FYM (Farm Yard Manure)",
    "farm yard manure": "FYM (Farm Yard Manure)",
    "znso4": "Zinc Sulphate (ZnSO4)",
    "zinc sulphate": "Zinc Sulphate (ZnSO4)",
    "psb": "Phosphobacteria (PSB)",
    "phospho bacteria": "Phosphobacteria (PSB)",
    "kmb": "Potassium Mobilizing Bacteria (KMB)",
    "vam": "VAM (Vesicular Arbuscular Mycorrhizae)",
}

UNIT_NORMALIZER: Dict[str, str] = {
    "kg / ha": "kg/ha", "kg per ha": "kg/ha", "kg per hectare": "kg/ha",
    "g / l": "g/L", "ml / l": "mL/L", "ml per litre": "mL/L",
    "t / ha": "t/ha", "tonnes / ha": "t/ha",
    "quintal": "100 kg", "quintals": "100 kg",
}

# ─────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────

@dataclass
class KnowledgeChunk:
    chunk_id:   str
    source_url: str
    source_file: str
    title:      str
    content:    str
    category:   str
    crop:       str
    language:   str
    chunk_index: int
    word_count: int

@dataclass
class ExtractedFertilizerSchedule:
    crop:       str
    stage:      str
    fertilizer: str
    dose:       str
    method:     str
    source_url: str

@dataclass
class ExtractedVariety:
    crop:       str
    variety:    str
    season:     str
    zone:       str
    districts:  List[str]
    duration:   str
    source_url: str

# ─────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────

def normalize_crop_name(raw: str) -> str:
    cleaned = raw.strip().lower()
    for alias, canonical in CROP_ALIASES.items():
        if alias in cleaned:
            return canonical
    return raw.strip().title()

def normalize_fertilizer_name(raw: str) -> str:
    cleaned = raw.strip().lower()
    for alias, canonical in FERTILIZER_ALIASES.items():
        if alias in cleaned:
            return canonical
    return raw.strip()

def normalize_units(text: str) -> str:
    for raw, norm in UNIT_NORMALIZER.items():
        text = re.sub(re.escape(raw), norm, text, flags=re.IGNORECASE)
    return text

def chunk_id(url: str, idx: int) -> str:
    return hashlib.md5(f"{url}:{idx}".encode()).hexdigest()[:12]

def strip_markdown_boilerplate(text: str) -> str:
    lines = text.splitlines()
    out = []
    for line in lines:
        if re.match(r"\|\s*\|\s*\|", line):     continue   # empty table rows
        if "© TNAU" in line:                     continue
        if line.strip().startswith("| ---"):     continue
        if len(line.strip()) < 2:
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(line)
    return "\n".join(out).strip()

def detect_category(text: str, url: str) -> str:
    url_l, text_l = url.lower(), text.lower()
    rules = [
        (["crop_protection", "ipm", "disease", "pest", "pesticide", "insect"],    "Plant Protection"),
        (["nutrient", "fertilizer", "fertilizer", "manure", "organic"],            "Nutrient Management"),
        (["irrigation", "water management", "drip", "sprinkler"],                  "Irrigation"),
        (["horticulture", "vegetable", "fruit", "flower", "spice"],                "Horticulture"),
        (["post.?harvest", "storage", "processing", "value addition"],             "Post Harvest"),
        (["variety", "varieties", "season", "sowing"],                             "Seed & Varieties"),
        (["scheme", "subsidy", "government", "policy", "nabard"],                  "Govt Schemes"),
        (["machinery", "mechanization", "tractor", "sprayer"],                     "Farm Machinery"),
        (["organic", "biofertilizer", "vermicompost", "green manure"],             "Organic Farming"),
        (["soil", "salinity", "reclamation", "drainage"],                          "Soil Management"),
        (["animal husbandry", "cattle", "poultry", "dairy", "goat"],               "Animal Husbandry"),
        (["fishery", "aquaculture", "fish", "shrimp", "prawn"],                    "Fisheries"),
        (["sericulture", "silk", "mulberry"],                                       "Sericulture"),
        (["crop production", "cultivation", "agronomy", "agriculture"],             "Crop Production"),
    ]
    combined = url_l + " " + text_l[:3000]
    for keywords, cat in rules:
        if any(re.search(kw, combined) for kw in keywords):
            return cat
    return "General Agriculture"

def detect_crop(text: str) -> str:
    crop_patterns = [
        "rice", "paddy", "maize", "sorghum", "jowar", "ragi", "cumbu", "wheat",
        "blackgram", "greengram", "redgram", "pigeonpea", "soybean", "groundnut",
        "sunflower", "sesame", "cotton", "sugarcane", "banana", "coconut",
        "mango", "tomato", "chilli", "onion", "okra", "bhendi", "brinjal",
        "turmeric", "ginger", "garlic", "jasmine", "marigold", "arecanut",
        "cashew", "tapioca", "cassava", "moringa", "drumstick", "guava", "papaya",
    ]
    text_l = text.lower()[:5000]
    counts = {crop: len(re.findall(r'\b' + crop + r'\b', text_l)) for crop in crop_patterns}
    winner = max(counts, key=counts.get)
    return normalize_crop_name(winner) if counts[winner] > 0 else "General"

# ─────────────────────────────────────────────────────────────
# EXTRACTORS
# ─────────────────────────────────────────────────────────────

def extract_fertilizer_schedules(text: str, url: str) -> List[ExtractedFertilizerSchedule]:
    schedules = []
    crop = detect_crop(text)

    dose_pattern = re.compile(
        r'(?P<fertilizer>[A-Z][A-Za-z\s\(\)]+?)\s*@\s*(?P<dose>[\d\.\-]+\s*(?:kg|g|t|bags?)\s*/?\s*(?:ha|acre|tree)?)',
        re.IGNORECASE
    )
    for m in dose_pattern.finditer(text[:8000]):
        fert = normalize_fertilizer_name(m.group("fertilizer"))
        dose = normalize_units(m.group("dose"))
        schedules.append(ExtractedFertilizerSchedule(
            crop=crop, stage="General", fertilizer=fert,
            dose=dose, method="As per recommendation", source_url=url
        ))
    return schedules[:20]

def extract_varieties(text: str, url: str) -> List[ExtractedVariety]:
    varieties = []
    crop = detect_crop(text)

    variety_pattern = re.compile(
        r'\b(?:ADT|CO|TKM|MDU|VBN|TMV|VRI|TPS|TRY|ASD|CORH|PMK|Anna|CR|IR|TRY|KMR|VGD)\s*[\(\)RrHh\d]+\b'
    )
    season_blocks = re.split(r'(?:Kuruvai|Samba|Navarai|Sornavari|Thaladi|Kar|Rabi|Kharif)', text)

    for match in variety_pattern.finditer(text[:15000]):
        var = match.group().strip()
        varieties.append(ExtractedVariety(
            crop=crop, variety=var, season="",
            zone="Tamil Nadu", districts=[],
            duration="", source_url=url
        ))

    seen = set()
    unique = []
    for v in varieties:
        if v.variety not in seen:
            seen.add(v.variety)
            unique.append(v)
    return unique[:50]

def extract_diseases_from_text(text: str, url: str) -> List[Dict]:
    diseases = []
    crop = detect_crop(text)

    disease_patterns = [
        r'(?P<name>[A-Z][a-z]+(?:\s[A-Za-z]+)*\s+(?:Blight|Blast|Rot|Wilt|Smut|Mildew|Spot|Streak|Mosaic|Yellowing))',
        r'(?P<name>[A-Z][a-z]+\s+(?:Borer|Thrips|Mite|Aphid|Whitefly|Mealybug|Weevil|Caterpillar))',
    ]

    for pattern in disease_patterns:
        for m in re.finditer(pattern, text[:10000]):
            diseases.append({
                "name": m.group("name").strip(),
                "affected_crop": crop,
                "source_url": url,
                "extracted": True
            })
    return diseases[:10]

# ─────────────────────────────────────────────────────────────
# RAG CHUNKER
# ─────────────────────────────────────────────────────────────

def chunk_markdown(
    content: str,
    metadata: Dict,
    chunk_size: int = 512,
    overlap: int = 64
) -> List[KnowledgeChunk]:
    words = content.split()
    if len(words) == 0:
        return []

    chunks = []
    i = 0
    idx = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)

        chunks.append(KnowledgeChunk(
            chunk_id    = chunk_id(metadata.get("url", ""), idx),
            source_url  = metadata.get("url", ""),
            source_file = metadata.get("local_markdown", ""),
            title       = metadata.get("title", ""),
            content     = chunk_text,
            category    = metadata.get("category", detect_category(chunk_text, metadata.get("url",""))),
            crop        = metadata.get("crop", detect_crop(chunk_text)),
            language    = metadata.get("language", "English"),
            chunk_index = idx,
            word_count  = len(chunk_words),
        ))
        i += chunk_size - overlap
        idx += 1
    return chunks

# ─────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────

class TNAUNormalizer:
    def __init__(self, kb_path: Path, output_dir: Path, rag_dir: Path):
        self.kb       = kb_path
        self.out      = output_dir
        self.rag_dir  = rag_dir
        self.out.mkdir(parents=True, exist_ok=True)
        self.rag_dir.mkdir(parents=True, exist_ok=True)

        self.all_chunks:     List[KnowledgeChunk] = []
        self.all_varieties:  List[ExtractedVariety] = []
        self.all_schedules:  List[ExtractedFertilizerSchedule] = []
        self.all_diseases:   List[Dict] = []

    # ── Load metadata ─────────────────────────────────────────

    def _load_metadata(self) -> List[Dict]:
        meta_dir = self.kb / "metadata"
        metas = []
        for f in meta_dir.rglob("*.json"):
            try:
                metas.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        log.info(f"Loaded {len(metas)} metadata files")
        return metas

    def _read_markdown(self, meta: Dict) -> Optional[str]:
        rel = meta.get("local_markdown", "")
        if not rel:
            return None
        path = self.kb / rel
        if not path.exists():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return None

    # ── Processing ────────────────────────────────────────────

    def process_all(self):
        metas = self._load_metadata()
        html_metas = [m for m in metas if m.get("file_type") == "HTML"]
        log.info(f"Processing {len(html_metas)} HTML pages...")

        stats = {"pages": 0, "chunks": 0, "varieties": 0, "schedules": 0, "diseases": 0}

        for meta in html_metas:
            md = self._read_markdown(meta)
            if not md:
                continue

            clean_md = strip_markdown_boilerplate(md)
            if len(clean_md.split()) < 20:
                continue

            # Chunk for RAG
            chunks = chunk_markdown(clean_md, meta)
            self.all_chunks.extend(chunks)
            stats["chunks"] += len(chunks)

            # Extract structured data
            url = meta.get("url", "")
            varieties = extract_varieties(clean_md, url)
            self.all_varieties.extend(varieties)
            stats["varieties"] += len(varieties)

            schedules = extract_fertilizer_schedules(clean_md, url)
            self.all_schedules.extend(schedules)
            stats["schedules"] += len(schedules)

            diseases = extract_diseases_from_text(clean_md, url)
            self.all_diseases.extend(diseases)
            stats["diseases"] += len(diseases)

            stats["pages"] += 1

        log.info(f"Processed: {stats}")
        return stats

    # ── Export ────────────────────────────────────────────────

    def export_rag_chunks(self):
        log.info(f"Exporting {len(self.all_chunks)} RAG chunks...")
        # Group by category for organized storage
        by_cat: Dict[str, List[KnowledgeChunk]] = {}
        for c in self.all_chunks:
            cat = re.sub(r'[^a-zA-Z0-9_]', '_', c.category.lower())
            by_cat.setdefault(cat, []).append(c)

        for cat, chunks in by_cat.items():
            cat_dir = self.rag_dir / cat
            cat_dir.mkdir(parents=True, exist_ok=True)
            for chunk in chunks:
                out_path = cat_dir / f"{chunk.chunk_id}.md"
                out_path.write_text(
                    f"---\n"
                    f"chunk_id: {chunk.chunk_id}\n"
                    f"source: {chunk.source_url}\n"
                    f"title: {chunk.title}\n"
                    f"category: {chunk.category}\n"
                    f"crop: {chunk.crop}\n"
                    f"language: {chunk.language}\n"
                    f"chunk_index: {chunk.chunk_index}\n"
                    f"words: {chunk.word_count}\n"
                    f"---\n\n"
                    f"{chunk.content}\n",
                    encoding="utf-8"
                )

        # Also write master JSONL for embedding pipeline
        master = self.rag_dir / "chunks.jsonl"
        with open(master, "w", encoding="utf-8") as fh:
            for c in self.all_chunks:
                fh.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

        log.info(f"RAG chunks exported to {self.rag_dir} + {master}")

    def export_varieties_csv(self):
        path = self.out / "crop_varieties.csv"
        seen: Set[str] = set()
        rows = []
        for v in self.all_varieties:
            key = f"{v.crop}|{v.variety}"
            if key not in seen:
                seen.add(key)
                rows.append({
                    "crop": v.crop,
                    "variety": v.variety,
                    "season": v.season,
                    "zone": v.zone,
                    "districts": "; ".join(v.districts),
                    "duration": v.duration,
                    "source_url": v.source_url,
                })
        _write_csv(path, rows)
        log.info(f"Exported {len(rows)} unique varieties → {path}")

    def export_fertilizer_schedules_csv(self):
        path = self.out / "fertilizer_schedules.csv"
        rows = [asdict(s) for s in self.all_schedules]
        _write_csv(path, rows)
        log.info(f"Exported {len(rows)} fertilizer schedules → {path}")

    def export_extracted_diseases_csv(self):
        path = self.out / "diseases_extracted.csv"
        seen: Set[str] = set()
        rows = []
        for d in self.all_diseases:
            key = d["name"].lower()
            if key not in seen:
                seen.add(key)
                rows.append(d)
        _write_csv(path, rows)
        log.info(f"Exported {len(rows)} unique extracted diseases → {path}")

    def export_json(self):
        path = self.out / "uzhavan_normalized.json"
        data = {
            "generated_at": datetime.utcnow().isoformat(),
            "source": "TNAU Agritech Portal",
            "stats": {
                "chunks": len(self.all_chunks),
                "varieties": len(self.all_varieties),
                "fertilizer_schedules": len(self.all_schedules),
                "diseases": len(self.all_diseases),
            },
            "chunks": [asdict(c) for c in self.all_chunks[:100]],  # sample
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info(f"JSON exported → {path}")

    def export_sql_seeds(self):
        path = self.out / "seeds_from_extraction.sql"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("-- Auto-generated seed SQL from TNAU extraction\n\n")

            # Varieties
            fh.write("-- Crop Varieties (from text extraction)\n")
            fh.write("CREATE TABLE IF NOT EXISTS crop_varieties (\n")
            fh.write("  variety_id SERIAL PRIMARY KEY,\n")
            fh.write("  crop VARCHAR(100),\n")
            fh.write("  variety VARCHAR(100),\n")
            fh.write("  season VARCHAR(100),\n")
            fh.write("  zone VARCHAR(100),\n")
            fh.write("  source_url TEXT\n")
            fh.write(");\n\n")

            seen = set()
            for v in self.all_varieties:
                key = f"{v.crop}|{v.variety}"
                if key not in seen:
                    seen.add(key)
                    crop = v.crop.replace("'", "''")
                    var  = v.variety.replace("'", "''")
                    fh.write(
                        f"INSERT INTO crop_varieties(crop, variety, season, zone, source_url) "
                        f"VALUES ('{crop}', '{var}', '{v.season}', '{v.zone}', '{v.source_url}') "
                        f"ON CONFLICT DO NOTHING;\n"
                    )

            fh.write(f"\n-- Total varieties: {len(seen)}\n")
        log.info(f"SQL seeds exported → {path}")

    def export_parquet(self):
        try:
            import pandas as pd
            chunks_df = pd.DataFrame([asdict(c) for c in self.all_chunks])
            path = self.out / "rag_chunks.parquet"
            chunks_df.to_parquet(path, index=False)
            log.info(f"Parquet exported → {path} ({len(chunks_df)} rows)")
        except ImportError:
            log.warning("pandas/pyarrow not installed — skipping Parquet export")
        except Exception as e:
            log.warning(f"Parquet export failed: {e}")

    def run(self, export_parquet: bool = False):
        log.info("=" * 60)
        log.info("UZHAVAN AI — TNAU Knowledge Normalization Pipeline")
        log.info("=" * 60)

        stats = self.process_all()

        self.export_rag_chunks()
        self.export_varieties_csv()
        self.export_fertilizer_schedules_csv()
        self.export_extracted_diseases_csv()
        self.export_json()
        self.export_sql_seeds()

        if export_parquet:
            self.export_parquet()

        log.info("=" * 60)
        log.info(f"Done. Outputs in: {self.out.resolve()}")
        log.info(f"RAG chunks in:   {self.rag_dir.resolve()}")
        return stats


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _write_csv(path: Path, rows: List[Dict]):
    if not rows:
        log.warning(f"No rows to write for {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="TNAU Knowledge Normalizer for UZHAVAN AI")
    parser.add_argument("--knowledge-base", default=str(KNOWLEDGE_BASE),
                        help="Path to knowledge_base/ directory")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR),
                        help="Directory to write CSV/JSON/SQL outputs")
    parser.add_argument("--rag-dir", default=str(RAG_DIR),
                        help="Directory to write RAG chunks")
    parser.add_argument("--export-parquet", action="store_true",
                        help="Also export chunks as Parquet (requires pandas + pyarrow)")
    args = parser.parse_args()

    normalizer = TNAUNormalizer(
        kb_path    = Path(args.knowledge_base),
        output_dir = Path(args.output_dir),
        rag_dir    = Path(args.rag_dir),
    )
    normalizer.run(export_parquet=args.export_parquet)


if __name__ == "__main__":
    main()
