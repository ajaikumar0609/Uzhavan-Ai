# UZHAVAN AI — Agricultural AI Operating System for Tamil Nadu

AI platform for Tamil Nadu farmers: TNAU knowledge RAG + plant disease detection + satellite crop monitoring.

## Architecture

```
Farmer (Tamil/English)
        │
        ▼
  Advisory Service  ←──── RAG chunks (ChromaDB / BAAI/bge-m3)
  (LLM Router)      ←──── TNAU knowledge (368 HTML + 1240 PDFs)
        │
        ├── Knowledge Tool  →  ChromaDB RAG over TNAU/ICAR
        ├── Disease Tool    →  Plant Disease Detection (MobileNetV2)
        ├── Weather Tool    →  Open-Meteo API
        ├── Market Tool     →  AGMARKNET mandi prices
        └── Satellite Tool  →  SICKLE dataset (future)
                │
                ▼
        PostgreSQL + PostGIS  (21 tables, farm boundaries, NDVI)
```

**LLM principle:** The LLM never guesses. It routes to a tool, gets real data, then generates a response.

---

## Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL + PostGIS | 5432 | Main database — 21 tables |
| Redis | 6379 | Cache + task queue |
| Disease Detection | 8001 | MobileNetV2 — 14 crops, 38 disease labels |
| Advisory RAG | 8002 | TNAU knowledge Q&A — Tamil + English |

---

## Quick Start

### 1. Environment setup

```bash
cd uzhavan_platform
cp .env.example .env
# Edit .env — set DB_PASSWORD and ANTHROPIC_API_KEY (or OLLAMA_MODEL)
```

### 2. Start database

```bash
docker compose -f docker/docker-compose.yml up -d db redis
# Wait ~10 seconds for PostGIS to initialise
```

### 3. Seed the database

```bash
psql -h localhost -U uzhavan -d uzhavan -f database/migrations/001_initial_schema.sql
psql -h localhost -U uzhavan -d uzhavan -f database/migrations/002_seed_data.sql
```

### 4. Run the TNAU normalizer (produces RAG chunks)

```bash
pip install tqdm
python data_pipeline/normalize_tnau.py \
  --knowledge-base ../tnau_crawler/knowledge_base \
  --output-dir database/data \
  --export-parquet
# Produces: rag/chunks/chunks.jsonl  (one line per chunk)
```

### 5. Embed chunks into ChromaDB

```bash
pip install chromadb sentence-transformers
python data_pipeline/embed_chunks.py
# Downloads BAAI/bge-m3 (~1.1 GB) on first run
# Re-run at any time — only new chunks are embedded (incremental)
```

### 6. Start the advisory service

```bash
cd api/advisory
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### 7. Start disease detection

```bash
cd api/disease_detection
pip install -r requirements.txt
# Copy model_loader.py, predict.py, utils.py from plant-disease-repo/backend/
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 8. Or run everything via Docker

```bash
docker compose -f docker/docker-compose.yml up
```

---

## API Reference

### Advisory Service (port 8002)

**Ask a question:**
```bash
curl -X POST http://localhost:8002/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What fertilizer should I apply for Samba rice at 30 days?",
    "language": "English",
    "crop": "Rice"
  }'
```

**Tamil query:**
```bash
curl -X POST http://localhost:8002/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "சாம்பா நெல்லுக்கு 30 நாட்களில் என்ன உரம் போட வேண்டும்?",
    "language": "Tamil",
    "crop": "Rice"
  }'
```

**Semantic search (no LLM):**
```bash
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{"query": "blast disease management paddy", "top_k": 5}'
```

### Disease Detection (port 8001)

**Single image:**
```bash
curl -X POST http://localhost:8001/predict \
  -F "file=@tomato_leaf.jpg"
```

**Batch (up to 10 images):**
```bash
curl -X POST http://localhost:8001/batch_predict \
  -F "files=@image1.jpg" -F "files=@image2.jpg"
```

**Supported crops and diseases:**
```bash
curl http://localhost:8001/supported_crops
curl http://localhost:8001/supported_diseases?crop=Tomato
curl http://localhost:8001/disease/Tomato%20With%20Early%20Blight
```

---

## Data Platform

### Seed CSVs (`database/data/`)

| File | Records | Description |
|------|---------|-------------|
| crops.csv | 50 | All major TN crops — Tamil names, yield, water, pH |
| fertilizers.csv | 25 | Chemical + organic + biofertilizers + NPK values |
| diseases.csv | 18 | Diseases — pathogen, symptoms, chemical + bio + cultural management |
| pests.csv | 15 | Pests — ETL thresholds, biocontrol agents |
| soil_types.csv | 10 | TN soil classifications + districts + management |
| crop_calendar.csv | 18 | Seasonal planting guide — all 6 rice seasons |
| government_schemes.csv | 15 | PM-KISAN, PMFBY, KCC, SMAM, PMKSY etc. |
| farm_machinery.csv | 20 | Equipment — subsidy info, capacity, manufacturers |
| district_profiles.csv | 38 | All 38 TN districts — agro-climatic zone + PostGIS centroids |

### Database (`database/migrations/`)

- `001_initial_schema.sql` — 21 tables, PostGIS, GIN + trgm indexes
- `002_seed_data.sql` — crops, fertilizers, soil_types, district_profiles

### ETL Pipeline (`data_pipeline/`)

- `normalize_tnau.py` — TNAU crawler KB → normalized CSVs + RAG chunks + Parquet
- `embed_chunks.py` — RAG chunks → ChromaDB (incremental, batch 64)

### Documentation (`docs/`)

- `er_diagram.md` — Mermaid ER diagram (21 tables)
- `data_dictionary.md` — Column-level documentation

---

## LLM Configuration

### Option A — Claude API (recommended for production)

```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-6
```

### Option B — Ollama + Qwen3 (free, local, Tamil support)

```bash
# Install Ollama first: https://ollama.com
ollama pull qwen3:8b
ollama serve
```

```env
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
```

---

## Folder Structure

```
uzhavan_platform/
├── api/
│   ├── advisory/              # RAG + LLM advisory service (port 8002)
│   │   ├── main.py
│   │   ├── rag_engine.py      # ChromaDB retrieval
│   │   ├── llm_client.py      # Claude / Ollama client
│   │   └── requirements.txt
│   ├── disease_detection/     # Plant disease API (port 8001)
│   │   ├── main.py            # Enhanced with batch + TNAU guidance
│   │   ├── tnau_guidance.py   # Treatment DB — 38 disease labels
│   │   └── requirements.txt
│   └── satellite/             # (future) SICKLE integration
├── data_pipeline/
│   ├── normalize_tnau.py      # TNAU KB → CSV + RAG chunks + Parquet
│   └── embed_chunks.py        # chunks.jsonl → ChromaDB
├── database/
│   ├── data/                  # 9 seed CSVs
│   └── migrations/            # 001_schema.sql + 002_seeds.sql
├── rag/
│   ├── chunks/                # chunks.jsonl (output of normalize_tnau.py)
│   └── chroma/                # ChromaDB persistence (output of embed_chunks.py)
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.disease
│   ├── Dockerfile.advisory
│   └── Dockerfile.pipeline
├── docs/
│   ├── er_diagram.md
│   └── data_dictionary.md
└── .env.example
```

---

## Data Sources

| Source | Type | Content |
|--------|------|---------|
| TNAU Agritech Portal | Web crawl | 368 HTML + 1,240 PDFs + 1.1 GB |
| SICKLE Dataset | Research dataset | 2,164 farm records, 3 satellites |
| AGMARKNET | Live API | Daily mandi prices |
| Open-Meteo | Live API | 7-day weather forecast |
| PlantVillage (via HuggingFace) | ML model | 38-class disease detection |
