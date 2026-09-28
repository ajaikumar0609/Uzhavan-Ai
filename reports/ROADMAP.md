# UZHAVAN AI — Development Roadmap

**Based on:** SICKLE Dataset Analysis  
**Document Type:** Product & Engineering Roadmap  
**Date:** June 30, 2026  
**Horizon:** 18 months (MVP to Production)

---

## Roadmap Overview

```
Phase 1: Foundation     │ Phase 2: Core AI        │ Phase 3: Scale      │ Phase 4: Ecosystem
Months 1–4              │ Months 5–9               │ Months 10–13        │ Months 14–18
                        │                          │                     │
Data pipelines          │ Satellite AI models      │ Multi-region        │ API marketplace
Basic dashboards        │ Yield forecasting        │ Weather fusion      │ B2B integrations
Farm registration       │ Crop calendar            │ Soil integration    │ Financial products
SICKLE fine-tuning      │ Tamil language RAG       │ Mobile optimization │ Policy dashboards
```

---

## Phase 1: Foundation (Months 1–4)

**Theme:** "Get the data flowing and the farm registered"

### Goals
1. Set up satellite data ingestion pipeline from Copernicus DIAS
2. Fine-tune SICKLE models for live inference
3. Build farm registration and onboarding system
4. Deploy basic farmer-facing mobile app
5. Establish ground truth collection protocol

### Dataset Used
- **SICKLE full dataset** — as training/validation baseline
- **Copernicus Hub** — live S1 + S2 acquisition pipeline
- **USGS EarthExplorer** — live Landsat-8 acquisition

### Key Deliverables

| Deliverable | Dataset Dependency | Done When |
|-------------|-------------------|---------|
| Satellite ingestion pipeline | Copernicus API | S1/S2/L8 data auto-downloaded weekly |
| Farm registration app (Android) | None | Farmer can register farm with GPS boundary |
| Crop type detection v1 | SICKLE `[S2,L8,S1]_unet3d` checkpoint | Paddy/non-paddy auto-detected on farm |
| SICKLE fine-tuning notebook | SICKLE full dataset | Baseline accuracy reproduced |
| Ground truth collection app | None | KVK surveyors can record yield data |
| Basic farm dashboard | SICKLE CSV | Farmer sees crop type + season info |

### Infrastructure
```
- AWS/GCP cloud account
- PostGIS database (farm boundaries)
- S3/GCS for satellite image store
- Docker + Kubernetes for model serving
- FastAPI + React (web) + Flutter (mobile)
```

### Milestone Gate (End of Month 4)
- [ ] 500 farms registered in Cauvery delta
- [ ] Live S1/S2/L8 pipeline processing weekly acquisitions
- [ ] Crop type API live with >80% accuracy on test farms
- [ ] Mobile app released on Play Store (beta)

---

## Phase 2: Core AI (Months 5–9)

**Theme:** "Train, predict, advise"

### Goals
1. Deploy all five SICKLE prediction tasks as live APIs
2. Launch Tamil-language RAG advisory chatbot
3. Integrate IMD weather data
4. Collect first 200 new yield data points
5. Launch harvest calendar feature

### Dataset Used
- **SICKLE full dataset** — continued fine-tuning
- **IMD Agrimet API** — rainfall, temperature (daily)
- **AGMARKNET API** — mandi price data
- **Newly collected ground truth** — 200 farmer yield records from Phase 1 collection

### Key Deliverables

| Deliverable | Dataset Dependency | Technical Stack |
|-------------|-------------------|----------------|
| Yield Forecast API v1 | SICKLE paddy yield (319 records) | UTAE_season, FastAPI |
| Harvest Calendar API | SICKLE harvesting_date task | UNet3D, FastAPI |
| Sowing Advisory API | SICKLE sowing_date task | UNet3D, FastAPI |
| Weather-fused yield model | SICKLE + IMD API | UTAE + MLP weather head |
| Tamil RAG chatbot | TNAU bulletins + SICKLE metadata | LangChain + Claude API |
| Market price integration | AGMARKNET API | ARIMA + FastAPI |
| Push notification system | Harvest/sowing predictions | Firebase Cloud Messaging |

### AI Model Training Schedule

| Week | Model | Data | Target Metric |
|------|-------|------|--------------|
| 5–6 | Weather-fused yield | SICKLE + IMD | RMSE < 600 kg/ha |
| 7–8 | 5-class crop classifier | SICKLE | F1 > 0.85 |
| 9–10 | Banana yield baseline | 200 new records | MAE < 30% |
| 11 | NDVI-LSTM forecast | SICKLE temporal | MAE < 0.05 NDVI |
| 12 | SAR flood detector | S1 + NDWI | F1 > 0.90 |

### Milestone Gate (End of Month 9)
- [ ] 5,000 farms registered
- [ ] Yield forecast API live for paddy
- [ ] Tamil chatbot handles top 20 farmer questions
- [ ] Harvest calendar sends SMS 14 days before harvest
- [ ] 200 new yield records collected

---

## Phase 3: Scale (Months 10–13)

**Theme:** "Go beyond Cauvery delta, go beyond paddy"

### Goals
1. Expand geographic coverage to all Tamil Nadu districts
2. Add banana and sugarcane yield models
3. Integrate soil health data
4. Deploy mobile-optimized models (on-device inference)
5. Multi-language support (Telugu, Kannada)

### Dataset Used
- **SICKLE dataset** — continued baseline
- **New ground truth** — 1,000 farms outside Cauvery delta
- **ICAR soil data** — N/P/K/pH from state testing labs
- **Newly collected banana/sugarcane yield** — 500 records
- **IMD + CWC river data** — full API integration

### Key Deliverables

| Deliverable | Dataset Dependency | Impact |
|-------------|-------------------|--------|
| Tamil Nadu-wide crop map | New GT + SICKLE transfer learning | Full state coverage |
| Banana yield model | 500 banana yield records | 2nd crop yield forecast |
| Soil-fused yield model | SICKLE + ICAR soil API | RMSE < 400 kg/ha |
| Mobile TFLite models | Quantized SICKLE models | Offline inference capability |
| FPO dashboard | Aggregated farm data | Bulk marketing intelligence |
| Crop insurance AI | SICKLE yield + PMFBY data | Loss estimation automation |
| Telugu/Kannada chatbot | Multi-lingual LLM fine-tune | Border district farmers |

### Model Improvement Targets

| Model | Phase 2 Metric | Phase 3 Target | Method |
|-------|---------------|---------------|--------|
| Yield RMSE | 749 kg/ha | <450 kg/ha | Add weather + soil features |
| Crop F1 (21-class) | 0.839 (binary) | 0.75 (5-class) | Focal loss + new data |
| Harvest MAE | 8.6 days | <6 days | Weather fusion |
| Geographic coverage | Cauvery delta | All TN | Transfer learning |

### Milestone Gate (End of Month 13)
- [ ] 25,000 farms registered
- [ ] Coverage: 20+ Tamil Nadu districts
- [ ] Banana yield API live
- [ ] Soil data integrated
- [ ] FPO dashboard deployed
- [ ] Offline mobile inference working

---

## Phase 4: Ecosystem (Months 14–18)

**Theme:** "From farm tool to agri-finance platform"

### Goals
1. Open API marketplace for agri-input dealers and banks
2. Launch crop loan scoring service
3. Integrate with e-NAM (national agriculture market)
4. Build policy intelligence dashboard for government
5. Publish SICKLE-Tamil extension dataset as open research

### Dataset Used
- **SICKLE dataset** — published as research artifact + extended
- **Full live satellite pipeline** — S1 + S2 + L8 weekly
- **AGMARKNET + e-NAM** — real-time price data
- **PMFBY + crop insurance claims** — loss pattern data
- **2-year UZHAVAN ground truth** — now 10,000+ labeled farm records

### Key Deliverables

| Deliverable | Dataset Dependency | Business Impact |
|-------------|-------------------|----------------|
| Agri-credit scoring API | SICKLE yield + PMFBY + bank data | Rural credit democratization |
| e-NAM price optimization | SICKLE harvest dates + e-NAM prices | Farmer price realization +15% |
| Government crop map API | SICKLE + all TN live data | Official crop area estimation |
| Input dealer analytics | Crop type map + area | Targeted input supply chain |
| SICKLE-Tamil-Extended | 2 years UZHAVAN data | Open research contribution |
| Satellite-backed insurance | SICKLE models + PMFBY | Parametric crop insurance |
| Drone integration | SICKLE 3m masks | Sub-field precision advisory |

### Technology Maturity

| Component | Phase 1 | Phase 4 |
|-----------|---------|---------|
| Farm coverage | 500 | 100,000+ |
| Model accuracy | SICKLE baseline | SICKLE + 2yr fine-tuning |
| Latency | Batch (nightly) | Real-time (<2s) |
| Languages | Tamil | Tamil, Telugu, Kannada, Hindi |
| Data sources | 3 satellites | 3 satellites + weather + soil + prices |
| Revenue model | None (beta) | SaaS + API + financial services |

### Milestone Gate (End of Month 18)
- [ ] 100,000 farms on platform
- [ ] Satellite yield forecast integrated with 3+ banks
- [ ] Government of Tamil Nadu agriculture dept partnership
- [ ] SICKLE-Tamil-Extended dataset published
- [ ] Platform sustainable via B2B API revenue

---

## Dataset Usage by Phase

| Phase | SICKLE Role | New Data Role |
|-------|------------|--------------|
| 1 | Primary training source (pre-trained checkpoints) | Ingest pipeline only |
| 2 | Fine-tuning base + validation benchmark | IMD weather + 200 new yields |
| 3 | Transfer learning base for new regions | 1,500 new farm records |
| 4 | Research baseline + published dataset | 10,000+ UZHAVAN records dominant |

---

## Budget Estimate

| Phase | Key Costs | Estimate (INR) |
|-------|-----------|---------------|
| Phase 1 | Cloud infra + app development + 2 engineers | ₹40L |
| Phase 2 | 3 ML engineers + API subscriptions + GPU compute | ₹60L |
| Phase 3 | 5 engineers + field surveys + data collection | ₹80L |
| Phase 4 | 8 engineers + partnerships + marketing | ₹120L |
| **Total 18 months** | | **₹300L (~$360K)** |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| SICKLE models don't generalize outside delta | HIGH | HIGH | Aggressive Phase 1 ground truth collection |
| Cloud cover → no satellite data | MEDIUM | HIGH | S1 SAR fallback (all-weather) |
| Farmer trust in AI yield forecast | HIGH | MEDIUM | Show historical accuracy; start conservative |
| IMD API unreliability | LOW | MEDIUM | Cache 7-day forecast + ERA5 backup |
| Competition from FarmERP/DeHaat | MEDIUM | MEDIUM | Tamil-first differentiation + satellite edge |
| Data privacy concerns | LOW | HIGH | On-device inference + data minimization |

---

## Success Metrics by Phase

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|
| Farms registered | 500 | 5,000 | 25,000 | 100,000 |
| Crop type accuracy | 80% | 83% | 86% | 89% |
| Yield RMSE (kg/ha) | 749 | 600 | 450 | 350 |
| Harvest MAE (days) | 8.6 | 7.0 | 5.5 | 4.0 |
| DAU (Daily Active Users) | 50 | 500 | 5,000 | 20,000 |
| Tamil NPS Score | — | 40 | 55 | 65 |

---

*End of UZHAVAN AI Roadmap*  
*Report Version 1.0 — June 2026*
