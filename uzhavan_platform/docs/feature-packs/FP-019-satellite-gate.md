# FP-019: Satellite / crop-intelligence readiness gate

**Status:** `GATE REVIEWED 2026-09-25`, **not passed** · **Decision: SATELLITE = UNDER VALIDATION** (`GET /api/satellite/status` → `available:false`)
**Owner:** Master Agent. Evidence comes from `uzhavan_data/01_sickle/{audit.md,manifest.json}`, `uzhavan_data/02_satellite/{README.md,metadata/*}` and `uzhavan_ml/evaluation_report.md`.

| # | Check | Evidence | Result |
|---|---|---|---|
| S1 | **Licence (training data + model)** | SICKLE dataset licence is UNVERIFIED (access is granted on request by the authors; no terms recorded). The official SICKLE code repo (commit c496cee) has **no licence file**, so local research use only | ❌ blocks farmer-facing use |
| S2 | **Licence (live imagery)** | Copernicus Sentinel: free, full and open (legal notice saved; attribution "Contains modified Copernicus Sentinel data"). Landsat: USGS public domain | ✅ |
| S3 | **Permitted use** | depends on S1. Research/internal only until the authors confirm | ❌ |
| S4 | **Geographic scope** | Cauvery Delta only (S2 tiles 44PKS/PKT/PLS/PLT); georeferencing stripped from SICKLE chips | ⚠ narrow; the app must refuse other districts |
| S5 | **Temporal scope** | labels 2018–2020; the live test set is the 2024-25 samba season (48 scenes) | ⚠ domain shift not measured |
| S6 | **Task scope** | crop_type is **binary paddy/non-paddy** only; calendar tasks are paddy-only | ⚠ |
| S7 | **Units** | yield units unconfirmed (800–3,840; likely kg/acre) | ❌ blocks yield |
| S8 | **Data source + access** | key-free: Earth Search (S2 L2A), Planetary Computer (S1 GRD, Landsat C2 L2) via `00_metadata/scripts/sat_ingest.py`. Production parity needs Copernicus Data Space / Earth Engine accounts | ⚠ works; accounts pending |
| S9 | **Processing parity** | S2 −1000 offset handled; S1 σ0 geocoding corrected (delta only); SICKLE used an Earth Engine pipeline, and the bias hasn't been measured; the 33×33 chip generator isn't built | ❌ |
| S10 | **Independent evaluation** | baseline on the authors' val (14 plots for calendar): sowing 3.00 d, transplanting 4.70 d (≈ seasonal median), **harvest 8.12 d fails the ≤7 d gate**, yield MAPE 34%. All RESEARCH-ONLY | ❌ |
| S11 | **Provenance** | per-scene STAC items + sha256 manifests stored | ✅ |

**Outcome:** 3 blocking failures (S1/S3 licence, S7 units, S9–S10 parity and evaluation). The satellite feature remains **"Satellite intelligence under validation"**. No imagery or predictions are shown to farmers. To unblock: written licence confirmation from the SICKLE authors, yield-unit confirmation, a chip generator + Earth Engine parity check, and a retrain/evaluation on `sickle_split_v1` if the harvest gate is to be met.
