# TNAU Agritech Portal — Crawl Report
**Site:** https://agritech.tnau.ac.in  
**Date:** July 1, 2026  
**Output:** `tnau_crawler/knowledge_base/`

---

## Summary

| Metric | Value |
|--------|-------|
| Total files downloaded | **1,608** |
| HTML pages | 368 |
| PDFs | 1,240 |
| Table CSVs extracted | 1,185 |
| Index entries | 1,627 |
| Total disk size | **1.1 GB** |
| Total words (HTML) | 165,883 |
| Total tables (HTML) | 1,183 |

---

## Storage Breakdown

| Folder | Size | Contents |
|--------|------|----------|
| `pdfs/` | 1,091 MB | 1,240 downloaded PDFs |
| `tables/` | 10 MB | 1,185 CSV table extracts |
| `html/` | 7.1 MB | 368 raw HTML pages |
| `metadata/` | 6.3 MB | 1,606 per-page JSON files |
| `markdown/` | 2.8 MB | 368 converted Markdown files |

> 99% of disk space is PDFs. The 1,048 DMI (Dynamic Market Information) archive PDFs from 2014 dominate storage.

---

## HTML Pages — Site Section Coverage

| Section | Pages | Description |
|---------|-------|-------------|
| `agriculture` | 74 | Crop production guides — paddy, maize, pulses, oilseeds |
| `root` | 47 | Homepage, portals, indexes |
| `horticulture` | 38 | Vegetables, fruits, spices, flowers |
| `farm_innovations` | 22 | Innovation case studies |
| `success_stories` | 18 | Farmer success case studies |
| `farm_association` | 15 | Farmer group resources |
| `postharvest` | 11 | Storage, grading, value addition |
| `sericulture` | 7 | Silk and mulberry cultivation |
| `crop_protection` | 6 | Pest and disease management |
| `org_farm` | 6 | Organic farming |
| `banking` | 6 | Agricultural credit and finance |
| `environment` | 6 | Environmental management |
| `fishery` | 5 | Inland and coastal fisheries |
| `govt_schemes_services` | 5 | Government schemes (PM Kisan, NABARD) |
| `ngo_shg` | 5 | NGO and self-help group resources |
| `agricultural_marketing` | 5 | Market linkages |
| `animal_husbandry` | 4 | Livestock and dairy |
| `agricultural_engineering` | 4 | Farm machinery |
| `export_import` | 6 | Export/import guidelines |
| Other sections (30+) | 42 | Patents, ITK, women in agri, etc. |
| **Total** | **368** | |

---

## PDF Archive Breakdown

| Section | Count | Description |
|---------|-------|-------------|
| `dmi/` | **1,048** | Dynamic Market Information — daily mandi arrivals & prices (2014) |
| `pdf/` | 85 | General publications, manuals, monthly magazines |
| `farm_innovations/` | 21 | Innovation technology PDFs |
| `success_stories/` | 21 | Farmer success story PDFs |
| `agriculture/` | 9 | Crop-specific technical bulletins |
| `tnaupressnotes/` | 7 | TNAU press releases |
| `farm_association/` | 7 | Farmer association documents |
| Other | 42 | Horticulture, govt, organic, forestry, etc. |
| **Total** | **1,240** | |

---

## Content Analysis

### Categories (Auto-detected)

| Category | Pages+PDFs |
|----------|-----------|
| Research & Technology | 1,417 |
| Crop Production | 76 |
| Horticulture | 42 |
| Soil Management | 17 |
| Plant Protection | 16 |
| Schemes & Subsidies | 15 |
| Animal Husbandry | 12 |
| Farm Machinery | 10 |
| Agro Forestry | 8 |
| Sericulture | 7 |
| Fisheries | 6 |
| Post Harvest | 1 |

> The high "Research & Technology" count is because the DMI PDFs are auto-tagged with that fallback category. Filtering to HTML pages only gives much cleaner distribution.

### Languages

| Language | Count |
|----------|-------|
| English | 386 pages |
| Tamil | 1 page |
| Unknown | 1,240 (PDFs — text not extracted) |

### Top Crops Mentioned (HTML pages)

| Crop | Mentions | Crop | Mentions |
|------|----------|------|----------|
| Rice / Paddy | 36 | Maize | 10 |
| Banana | 11 | Coconut | 10 |
| Cotton | 11 | Jasmine | 5 |
| Fish | 11 | Mango | 5 |
| Cattle | 5 | Groundnut | 4 |

---

## Top HTML Pages by Content

| Words | Page Title |
|-------|-----------|
| 16,799 | Dynamic Market Information (DMI) 2014 index |
| 6,692 | Biotechnology |
| 4,974 | Seed Technology |
| 4,597 | Disaster Management / Blood Banks |
| 4,108 | Soil & Water Conservation / Micro Irrigation |
| 4,031 | Sustainable Agriculture |
| 3,761 | Agricultural Technology Management Agency (ATMA) |
| 3,369 | Horticulture — Plant Protection |
| 3,092 | NGO & Self-Help Groups |

---

## Largest PDFs Downloaded

| Size | Document |
|------|----------|
| 54 MB | Feb 2020 (farm magazine) |
| 39 MB | Liquid Gold (water management) |
| 36 MB | April UVV 2023 |
| 35 MB | Madathukulam (district contingency plan) |
| 31 MB | November 2011 (magazine) |
| 26 MB | NITI Aayog Working Paper on Indian Agriculture |

---

## Relevance to UZHAVAN AI

### High-value content for RAG chatbot

| Content Type | Files | Use in UZHAVAN AI |
|-------------|-------|-------------------|
| Crop production guides | ~74 HTML | Cultivation advice, sowing, fertilizer, pest control |
| Horticulture guides | ~38 HTML | Banana, coconut, vegetable advisory |
| Post-harvest tech | ~11 HTML | Storage, value addition tips |
| Success stories | 18 HTML + 21 PDF | Real Tamil Nadu farmer case studies |
| Farm innovations | 22 HTML + 21 PDF | Technology adoption examples |
| Govt schemes | 5 HTML | PM Kisan, crop insurance eligibility |
| DMI market data | 1,048 PDF | Historical price/arrival data (2014) |
| TNAU publications | 85 PDF | Technical bulletins, manuals |

### RAG Ingestion Priority

1. **Tier 1 (Immediate):** `agriculture/`, `horticulture/`, `postharvest/`, `crop_protection/` HTML + Markdown → Tamil advisory chatbot
2. **Tier 2 (High):** `success_stories/`, `farm_innovations/` PDFs → farmer-relatable examples
3. **Tier 3 (Background):** `pdf/` TNAU publications → deep technical reference
4. **Tier 4 (Archive):** `dmi/` PDFs → historical market price analysis (needs PDF text extraction)

---

## Output Files

```
knowledge_base/
├── html/           368 HTML files (URL hierarchy preserved)
├── markdown/       368 Markdown files (clean, boilerplate stripped)
├── pdfs/          1,240 PDF files
├── tables/        1,185 CSV table extracts (ready for structured queries)
├── metadata/      1,606 JSON files (title, category, crop, word count, etc.)
├── index.csv      1,627-row master index (Title, URL, Category, Crop, Language)
└── crawler.log    Full crawl log
```

---

## Next Steps

1. **PDF text extraction** — Run `pdfplumber` or `pypdf` on the 85 high-value PDFs in `pdf/` to unlock their text for RAG
2. **Chunk & embed** — Split Markdown files into 512-token chunks, embed with `text-embedding-3-small`, store in ChromaDB/Qdrant
3. **Tamil translation** — Translate key crop guides (paddy, banana, coconut) to Tamil for Tamil-first chatbot
4. **DMI price analysis** — Extract mandi arrival/price tables from the 1,048 DMI PDFs to build a 2014 price baseline for UZHAVAN market intelligence

---

*Generated: July 1, 2026 | Crawler: TNAU Agritech Portal Crawler v2.0*
