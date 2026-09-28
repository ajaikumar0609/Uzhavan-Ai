# UZHAVAN AI — SICKLE Dataset Integration Report

**Role:** Chief Technology Officer, UZHAVAN AI  
**Document Type:** Strategic AI Architecture & Integration Design  
**Report Date:** June 30, 2026  
**Dataset:** SICKLE (Satellite Images and Crop observations for the Kaveri delta Landscape Encompassing region)

---

## Executive Summary

The SICKLE dataset is the most valuable existing labeled satellite dataset for Tamil Nadu precision agriculture. It provides pre-trained models, ground truth labels, and temporal satellite imagery for five agricultural prediction tasks. This report defines exactly which UZHAVAN AI modules the dataset powers directly, which require augmentation, and how to build an end-to-end AI architecture around it.

**Bottom line:** SICKLE can power 6 of 10 planned UZHAVAN AI modules today. The remaining 4 require additional data acquisition or API partnerships. The full system should be operational within 18 months if data collection begins immediately.

---

## 1. UZHAVAN AI Modules Powered by SICKLE

### ✅ Module 1: Crop Detection & Mapping

**What SICKLE provides:**
- Binary paddy/non-paddy classification (907 paddy + 1,257 non-paddy labels)
- 21 crop type labels
- Pre-trained UNet3D model achieving F1=0.839 with multi-satellite fusion
- Farm boundary masks at 10m, 30m, and 3m resolution

**UZHAVAN AI feature:**
Satellite-based crop map updated weekly. Farmer opens app → sees their field automatically identified as "Paddy — Samba Season" without manual input.

**Deployment plan:**
1. Fine-tune pre-trained `[S2,L8,S1]_unet3d` checkpoint on any new Tamil Nadu data
2. Run weekly inference on new S1/S2 acquisitions from Copernicus API
3. Display crop identification on farmer dashboard with confidence score

**Confidence:** High — best-in-class performance confirmed on SICKLE test set

---

### ✅ Module 2: Yield Forecast Engine

**What SICKLE provides:**
- 319 paddy yield labels (kg/ha) with satellite imagery context
- Pre-trained regression models (best: UTAE_season with S2+L8+S1, RMSE=749 kg/ha)
- Season-aware model variants (`_season` suffix)

**UZHAVAN AI feature:**
Yield forecast displayed 4–6 weeks before expected harvest. Farmers can plan sales, storage, and transportation. Banks can assess crop loan collateral.

**Limitation:** Only paddy yield — no banana, coconut, or sugarcane yield models  
**Gap to fill:** Collect 500+ yield data points for banana and sugarcane

**Deployment:** FastAPI microservice exposing `/predict/yield` endpoint

---

### ✅ Module 3: Harvest Calendar

**What SICKLE provides:**
- Harvesting day labels for all paddy records
- Pre-trained models with MAE ~8.6 days (UNet3D, L8 satellite)
- Historical harvest date patterns by season and river basin

**UZHAVAN AI feature:**
Predicted harvest date displayed in farmer app calendar. Integration with:
- Mandis (agricultural markets) for price timing
- Transport services for logistics booking
- FPO (Farmer Producer Organizations) for aggregation planning

**Confidence:** High — 8.6-day MAE is actionable for logistics planning

---

### ✅ Module 4: Sowing Advisory

**What SICKLE provides:**
- Sowing day labels for paddy
- Pre-trained models with MAE ~2.4 days (UNet3D, S2+L8+S1)

**UZHAVAN AI feature:**
Optimal sowing date recommendation based on satellite phenology patterns of neighboring fields. Farmer receives push notification: "Based on rainfall patterns and field conditions in your basin, optimal sowing window is July 15–18."

**Enhancement needed:** Integrate weather API for rainfall forecast-based recommendations

---

### ✅ Module 5: Transplanting Advisory

**What SICKLE provides:**
- Transplanting day labels (paddy-specific)
- Pre-trained models with MAE ~4.4 days

**UZHAVAN AI feature:**
Transplanting crew scheduling. Integration with labor marketplace apps.

---

### ✅ Module 6: Satellite Farm Intelligence Dashboard

**What SICKLE provides:**
- Complete spatial-temporal satellite coverage of Cauvery delta
- 3 satellite sources (optical + SAR) for comprehensive monitoring
- River basin segmentation (5 sub-basins)

**UZHAVAN AI feature:**
Regional agri-intelligence dashboard for agriculture department officers, FPOs, and agri-input dealers. Shows crop maps, yield forecasts, and phenology calendars for entire river basin.

---

## 2. Modules That Cannot Use SICKLE Directly

### ❌ Module 7: Weather Advisory

**Gap:** No meteorological data in SICKLE  
**What's needed:** IMD API, OpenWeatherMap, or ECMWF ERA5 integration  
**Alternative path:** Use satellite-derived proxies (LST from L8-ST_B10, NDWI from S2) as weather proxies

---

### ❌ Module 8: Soil Health Monitor

**Gap:** No soil N/P/K/pH/organic carbon data in SICKLE  
**What's needed:** ICAR soil surveys, state soil testing lab integration, or Sentinel-2-based soil indices (BSI, NDSI)  
**Alternative path:** Landsat-8 B4+B5+B6 ratios approximate bare soil composition when NDVI is low

---

### ❌ Module 9: Market Price Intelligence

**Gap:** No price data in SICKLE  
**What's needed:** AGMARKNET API, e-NAM API for mandi prices  
**Integration:** Combine SICKLE yield forecasts with AGMARKNET price trends for price × yield opportunity alerts

---

### ❌ Module 10: Crop Loan & Insurance Scoring

**Gap:** No financial data in SICKLE  
**What's needed:** Bank/NABARD loan data, PMFBY (insurance) claim history  
**Integration:** Use SICKLE yield predictions as one signal in a credit scoring or loss assessment model

---

## 3. Recommended Machine Learning Models

### 3.1 Satellite-Based Deep Learning (SICKLE-native)

| Task | Recommended Model | Satellite Input | Training Data |
|------|------------------|----------------|--------------|
| Crop classification | UNet3D (F1=0.839) | S2+L8+S1 | SICKLE + augmentation |
| Yield regression | UTAE_season (RMSE=749) | S2+L8+S1 | SICKLE paddy only |
| Harvest date | UNet3D (MAE=8.6d) | L8 | SICKLE paddy |
| Sowing date | UNet3D (MAE=2.4d) | S2+L8+S1 | SICKLE paddy |
| Transplanting date | UNet3D (MAE=4.4d) | S2+L8+S1 | SICKLE paddy |

### 3.2 Traditional ML (Tabular + Engineered Features)

| Task | Recommended Model | Features | Training Data |
|------|------------------|---------|--------------|
| Yield prediction (baseline) | XGBoost / LightGBM | Area, season, year, basin, NDVI mean | SICKLE CSV |
| Season classification | Random Forest | NDVI temporal curve shape | SICKLE |
| Anomaly detection | Isolation Forest | NDVI deviation from historical | SICKLE + IMD |
| Price forecasting | ARIMA / Prophet | AGMARKNET time series | External |
| Credit scoring | Logistic Regression + XGBoost | Yield history, area, crop type | External |

### 3.3 Deep Learning Models to Build

| Model | Purpose | Architecture | Status |
|-------|---------|-------------|--------|
| SICKLE-Paddy-Yield v2 | Yield with weather fusion | UTAE + weather MLP | Build |
| SICKLE-Crop-21class | Full 21-crop classification | UNet3D + focal loss | Build |
| NDVI-LSTM | NDVI time series forecasting | LSTM (no spatial) | Build |
| SAR-Flood-Detector | Monsoon flood mapping | Change detection on S1 | Build |
| Farm-Boundary-Delineator | Auto-detect field boundaries | ResNet + Watershed | Build |

---

## 4. APIs to Replace Static SICKLE Data

| Current Static Data | Live API Replacement | Update Frequency |
|--------------------|--------------------|-----------------|
| SICKLE satellite images (2018–2020) | Copernicus DIAS API (S1, S2) | Every 5-6 days |
| No weather data | IMD Agrimet API / ECMWF ERA5 | Daily |
| No market prices | AGMARKNET API / e-NAM | Daily |
| No soil data | ICAR NBSS soil API | Monthly |
| No water levels | CWC Cauvery gauge API | Daily |
| No advisory content | iKisan / KVK API | Weekly |

---

## 5. Features Using Satellite Imagery

All satellite-derived features come from the SICKLE pipeline extended to live Copernicus data:

| Feature | Satellite Source | Derived From | UZHAVAN AI Module |
|---------|-----------------|-------------|------------------|
| Crop type identification | S2 + S1 | UNet3D classifier | Dashboard, Advisory |
| Yield forecast | S2 + L8 + S1 | UTAE regressor | Yield Module |
| Harvest date prediction | L8 | UNet3D regressor | Calendar |
| NDVI time series | S2 B4, B8 | Band math | Crop Health Monitor |
| Field water status (NDWI) | S2 B3, B8 | Band math | Water Management |
| Land Surface Temperature | L8 ST_B10 | Radiometric conversion | Heat Stress Alert |
| SAR vegetation index (RVI) | S1 VV, VH | Band math | Monsoon Monitoring |
| Farm boundary | All satellites | Mask model | Farm Registration |
| Flood mapping | S1 VV | Change detection | Disaster Alert |

---

## 6. Features Using RAG (Retrieval-Augmented Generation)

RAG combines LLM reasoning with retrieved knowledge bases:

| Feature | RAG Knowledge Base | Use Case |
|---------|------------------|---------|
| Crop disease diagnosis | TNAU disease bulletins + farmer photos | "My paddy leaves are yellow" → diagnosis |
| Pesticide dosage advisor | CIBRC approved pesticide database | Safe dosage recommendations |
| Scheme advisor | PM Kisan, PMFBY scheme documents | "Which subsidy am I eligible for?" |
| Market intelligence | AGMARKNET, APMC price archives | "When is the best time to sell?" |
| Weather interpretation | IMD forecast bulletins | "What does the red alert mean for my crop?" |
| Legal advisory | TNAU extension circulars | Land rights, crop insurance queries |
| Fertilizer recommendation | State fertilizer recommendation tables | NPK schedules by crop and soil zone |

**Implementation:** LangChain + Chroma vector DB + Claude API for Tamil/English bilingual Q&A

---

## 7. Features Using Traditional ML

| Feature | Algorithm | Data Source | Output |
|---------|----------|------------|--------|
| Yield baseline (no satellite) | XGBoost | CSV: area, season, basin, crop | kg/ha estimate |
| Season classification | Random Forest | NDVI curve descriptors | Season type |
| Anomaly detection | Isolation Forest | NDVI z-score series | Alert flag |
| Price trend | ARIMA/Prophet | AGMARKNET 5-year series | Price forecast |
| Clustering farms | K-Means | Area, yield, crop, basin | Farm segments |
| Churn prediction | Logistic Regression | App usage features | At-risk users |
| Soil classification | SVM | Landsat spectral ratios | Soil texture class |

---

## 8. Features Using LLMs

| Feature | LLM Role | Model | Language |
|---------|---------|-------|---------|
| Crop advisory chatbot | Generate tailored advice | Claude / Llama | Tamil + English |
| Daily farm bulletin | Summarize forecasts in plain language | Claude | Tamil |
| Scheme eligibility checker | Classify and explain government schemes | Claude | Tamil |
| Pest outbreak alert text | Generate SMS/WhatsApp alerts | Claude | Tamil |
| Yield report generation | Auto-generate farm performance reports | Claude | English/Tamil |
| Voice query handler | Answer spoken Tamil questions | Whisper + Claude | Tamil |
| UZHAVAN AI customer support | Route and answer support queries | Claude | Tamil/English |

**Critical requirement:** Tamil language capability. Claude API and Llama 3.1 support Tamil. GPT-4 is also Tamil-capable.

---

## 9. Complete AI Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        UZHAVAN AI PLATFORM                       │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Mobile App  │  │  Web Dashboard│  │  WhatsApp/SMS Gateway │  │
│  │  (Tamil UI)  │  │  (Officer)   │  │  (Farmer Alerts)      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         └─────────────────┼──────────────────────┘              │
│                           │                                       │
│  ┌────────────────────────▼───────────────────────────────────┐ │
│  │                    API GATEWAY (FastAPI)                     │ │
│  │    /api/v1/crop  /api/v1/yield  /api/v1/calendar           │ │
│  │    /api/v1/advisory  /api/v1/chat  /api/v1/weather         │ │
│  └─────┬───────────┬─────────────┬──────────────┬────────────┘ │
│        │           │             │              │               │
│  ┌─────▼─────┐ ┌───▼────────┐ ┌─▼──────────┐ ┌▼────────────┐ │
│  │SATELLITE   │ │TABULAR ML  │ │RAG ENGINE  │ │LLM SERVICE  │ │
│  │AI MODELS   │ │ PIPELINE   │ │            │ │             │ │
│  │           │ │           │ │ LangChain  │ │ Claude API  │ │
│  │ UNet3D    │ │ XGBoost   │ │ +Chroma DB │ │ Tamil Mode  │ │
│  │ UTAE      │ │ Random F  │ │            │ │             │ │
│  │ ConvLSTM  │ │ Prophet   │ │            │ │             │ │
│  └─────┬─────┘ └───┬────────┘ └─┬──────────┘ └┬────────────┘ │
│        │           │             │              │               │
│  ┌─────▼───────────▼─────────────▼──────────────▼───────────┐  │
│  │                      DATA LAYER                             │  │
│  │                                                             │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│  │  │  Satellite  │  │  PostgreSQL  │  │  Vector Store    │  │  │
│  │  │  Image Store│  │  (Farm DB)   │  │  (RAG chunks)    │  │  │
│  │  │  (S3/GCS)   │  │  SICKLE CSV  │  │  Chroma/Pinecone │  │  │
│  │  └──────┬──────┘  └──────┬───────┘  └──────────────────┘  │  │
│  │         │                │                                   │  │
│  └─────────┼────────────────┼───────────────────────────────┘  │
│            │                │                                    │
│  ┌─────────▼────────┐  ┌────▼──────────────────────────────┐   │
│  │  INGESTION LAYER │  │        EXTERNAL DATA SOURCES        │   │
│  │                  │  │                                     │   │
│  │ Copernicus Hub   │  │ IMD Agrimet API  AGMARKNET API     │   │
│  │ (S1, S2 weekly) │  │ CWC River API    ICAR Soil API     │   │
│  │ USGS (L8 biweek) │  │ PMFBY Insurance  e-NAM Prices     │   │
│  └──────────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.1 Satellite AI Microservice

```
Service: satellite-ai
Language: Python (PyTorch + FastAPI)
GPU: NVIDIA T4 or A10 (inference)
Models loaded: 5 tasks × 3 model types = 15 model checkpoints
Input: S1 + S2 + L8 time series for a farm (from S3)
Output: crop_type, yield_kg_ha, harvest_date, sow_date, transplant_date
Latency: <2 seconds per farm
Scale: Batch 500 farms nightly, on-demand for single farm
```

### 9.2 Tabular ML Microservice

```
Service: agri-ml
Language: Python (scikit-learn + XGBoost + FastAPI)
Models: yield baseline, price forecast, anomaly detection
Input: CSV row features (area, season, basin, crop, NDVI)
Output: tabular predictions with confidence intervals
Latency: <100ms per farm
```

### 9.3 RAG Advisory Microservice

```
Service: advisory-rag
Language: Python (LangChain + Chroma + FastAPI)
Knowledge base: TNAU bulletins, PMFBY docs, pesticide DB, scheme docs
Embedding model: text-embedding-3-small or IndicBERT
LLM: Claude claude-sonnet-4-6 (Tamil support)
Input: Farmer query (text or audio transcription)
Output: Tamil advisory with source citations
Latency: 2–5 seconds
```

### 9.4 Farm Database Schema

```sql
-- Core tables derived from SICKLE structure

CREATE TABLE farms (
    farm_id       SERIAL PRIMARY KEY,
    unique_id     INTEGER UNIQUE,     -- matches SICKLE UNIQUE_ID
    plot_id       INTEGER,
    farmer_phone  VARCHAR(15),
    area_ha       FLOAT,
    river_part    VARCHAR(50),
    geom          GEOMETRY(POLYGON, 4326)  -- PostGIS farm boundary
);

CREATE TABLE seasons (
    season_id   SERIAL PRIMARY KEY,
    farm_id     INTEGER REFERENCES farms,
    year        SMALLINT,
    season      VARCHAR(20),          -- e.g. 'aug-jan'
    crop        VARCHAR(50),
    paddy_bin   SMALLINT,
    variety     VARCHAR(50),
    sowing_day  FLOAT,
    transp_day  FLOAT,
    harvest_day FLOAT,
    yield_kg_ha FLOAT,
    split       VARCHAR(10)
);

CREATE TABLE satellite_predictions (
    pred_id           SERIAL PRIMARY KEY,
    farm_id           INTEGER REFERENCES farms,
    prediction_date   TIMESTAMP,
    model_version     VARCHAR(20),
    crop_type         VARCHAR(50),
    crop_confidence   FLOAT,
    yield_kg_ha       FLOAT,
    harvest_date_pred DATE,
    sowing_date_pred  DATE,
    s2_last_date      DATE,
    s1_last_date      DATE
);

CREATE TABLE ndvi_timeseries (
    id          SERIAL PRIMARY KEY,
    farm_id     INTEGER REFERENCES farms,
    obs_date    DATE,
    ndvi_mean   FLOAT,
    ndvi_std    FLOAT,
    cloud_pct   FLOAT
);
```

---

## 10. Limitations of SICKLE for UZHAVAN AI

### Critical Gaps

| Gap | Severity | Workaround |
|-----|---------|-----------|
| No weather data | HIGH | IMD API integration (mandatory) |
| No soil data | HIGH | ICAR API + satellite soil indices |
| Paddy-only yield | HIGH | Collect banana/sugarcane yield data |
| 3-year window | MEDIUM | Annual retraining with new SICKLE-format data |
| Cauvery delta only | HIGH | Collect ground truth for other TN regions |
| 21-class imbalance | MEDIUM | Focal loss + synthetic oversampling |
| No price data | MEDIUM | AGMARKNET API |
| No real-time acquisition | HIGH | Copernicus DIAS subscription |

### Model Performance Ceiling

The best SICKLE models achieve:
- Crop type: F1=0.839 (excellent)
- Yield: RMSE=749 kg/ha on mean yield of 1,836 (41% error — moderate)
- Harvest date: MAE=8.6 days (good for logistics)
- Sowing: MAE=2.4 days (excellent)

Yield prediction accuracy (41% RMSE) needs improvement before farmers trust it for financial decisions. Priority: add weather and soil features.

---

## 11. Data Collection Roadmap

To close the gaps identified above:

### Year 1 Priority Collections

| Data Type | Target Volume | Method | Cost |
|-----------|-------------|--------|------|
| Banana yield (kg/bunch) | 500 farmers | Field surveys | ₹2L |
| Sugarcane yield (t/acre) | 200 farmers | Mill weighbridge records | ₹0.5L |
| Soil test results | 1,000 plots | KVK soil testing program | ₹1L |
| Expansion to new basins | 500 farms | Drone + ground truth | ₹5L |
| Real-time IMD weather | Automated | API subscription | ₹0.2L/yr |

---

*End of UZHAVAN AI Integration Report*  
*Report Version 1.0 — June 2026*  
*Classification: Internal Strategy Document*
