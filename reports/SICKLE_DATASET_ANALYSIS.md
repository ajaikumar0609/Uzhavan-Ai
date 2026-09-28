# SICKLE Dataset — Complete Technical Audit

**Prepared for:** UZHAVAN AI Project  
**Audit Date:** June 30, 2026  
**Dataset Version:** WACV 2024 Release  
**Auditor:** Senior AI Research Engineer / Data Scientist Role

---

## Table of Contents

1. [Overall Dataset Structure](#1-overall-dataset-structure)
2. [Satellite Imagery](#2-satellite-imagery)
3. [Tabular Dataset](#3-tabular-dataset)
4. [Images](#4-images)
5. [Masks](#5-masks)
6. [Dataset Statistics](#6-dataset-statistics)
7. [Models](#7-models)
8. [ML Tasks Supported](#8-ml-tasks-supported)
9. [Integration into Precision Farming](#9-integration-into-precision-farming)
10. [Limitations](#10-limitations)

---

## 1. Overall Dataset Structure

```
agri/
├── sickle_dataset/                  # Full dataset (2,370 records)
│   ├── sickle_dataset_tabular.csv   # Ground truth tabular annotations
│   ├── images/
│   │   ├── S2/                      # Sentinel-2 optical imagery
│   │   │   ├── npy/                 # Per-farm NPZ archives (one folder per farm)
│   │   │   └── tif/                 # GeoTIFF mosaics (one per farm)
│   │   ├── S1/                      # Sentinel-1 SAR imagery
│   │   │   ├── npy/
│   │   │   └── tif/
│   │   └── L8/                      # Landsat-8 imagery
│   │       ├── npy/
│   │       └── tif/
│   └── masks/
│       ├── 10m/                     # Farm boundary masks at 10m resolution
│       ├── 30m/                     # Farm boundary masks at 30m resolution
│       └── 3m/                      # Farm boundary masks at 3m resolution
│
├── sickle_toy_dataset/              # Subset for prototyping (matches structure above)
│   ├── sickle_dataset_tabular.csv
│   ├── images/
│   │   ├── S2/, S1/, L8/
│   └── masks/
│       ├── 10m/, 30m/, 3m/
│
├── runs/
│   └── wacv_2024/                   # Pre-trained model checkpoints & training logs
│       ├── crop_type/               # 13 experiment variants
│       ├── crop_yield/              # 26 experiment variants
│       ├── harvesting_date/         # 13 experiment variants
│       ├── sowing_date/             # 13 experiment variants
│       └── transplanting_date/      # 13 experiment variants
│
├── all_files.txt                    # Auto-generated file manifest
└── dataset_structure.txt            # Auto-generated directory tree
```

### Folder Purpose Summary

| Folder | Purpose |
|--------|---------|
| `sickle_dataset/` | Production-grade full dataset with all 2,370 farm records |
| `sickle_toy_dataset/` | Lightweight subset for rapid prototyping and debugging |
| `images/S2/npy/` | Per-acquisition NPZ archives of Sentinel-2 spectral bands |
| `images/S2/tif/` | Single-file GeoTIFF composites per farm |
| `images/S1/npy/` | Per-acquisition NPZ archives of Sentinel-1 SAR bands |
| `images/L8/npy/` | Per-acquisition NPZ archives of Landsat-8 surface reflectance |
| `masks/10m/` | Binary/class raster masks at 10 m native resolution |
| `masks/30m/` | Masks resampled to 30 m for Landsat alignment |
| `masks/3m/` | High-resolution boundary masks for sub-field analysis |
| `runs/wacv_2024/` | PyTorch model checkpoints, training configs, and epoch logs |

---

## 2. Satellite Imagery

### 2.1 Sentinel-2 (S2)

**Source:** ESA Copernicus Programme — MSI (MultiSpectral Instrument) aboard Sentinel-2A/2B  
**Spatial Resolution:** 10 m (bands B2, B3, B4, B8), 20 m (B5–B7, B8A, B11, B12), 60 m (B1, B9)  
**Image Size in Dataset:** 32 × 32 pixels at 10 m native resolution (~3.2 ha coverage)  
**Revisit Time:** ~5 days (constellation of 2 satellites)  
**Observed Bands in Dataset:**

| Key | Band | Wavelength | Resolution | Description |
|-----|------|-----------|-----------|-------------|
| B1 | Band 1 | 443 nm | 60 m | Coastal Aerosol |
| B2 | Band 2 | 490 nm | 10 m | Blue |
| B3 | Band 3 | 560 nm | 10 m | Green |
| B4 | Band 4 | 665 nm | 10 m | Red |
| B5 | Band 5 | 705 nm | 20 m | Red Edge 1 |
| B6 | Band 6 | 740 nm | 20 m | Red Edge 2 |
| B7 | Band 7 | 783 nm | 20 m | Red Edge 3 |
| B8 | Band 8 | 842 nm | 10 m | NIR |
| B8A | Band 8A | 865 nm | 20 m | NIR Narrow |
| B9 | Band 9 | 945 nm | 60 m | Water Vapour |
| B11 | Band 11 | 1610 nm | 20 m | SWIR 1 |
| B12 | Band 12 | 2190 nm | 20 m | SWIR 2 |
| AOT | Aerosol Optical Thickness | — | 10 m | Atmospheric correction |
| WVP | Water Vapour Pressure | — | 10 m | Atmospheric product |
| SCL | Scene Classification Layer | — | 20 m | Cloud/shadow masks |
| MSK_CLDPRB | Cloud Probability | — | 20 m | Per-pixel cloud score |

**Temporal Coverage:** 2018–2020  
**Average Observations per Farm:** ~56 acquisitions  
**Filename Format:** `YYYYMMDDTHHMMSS_YYYYMMDDTHHMMSS_T<tile>.npz` (e.g., `20190804T045709_20190804T050757_T44PKT.npz`)

### 2.2 Sentinel-1 (S1)

**Source:** ESA Copernicus Programme — C-band SAR (Synthetic Aperture Radar), IW-GRDH mode  
**Spatial Resolution:** ~10 m (ground range detected, high resolution)  
**Image Size in Dataset:** 33 × 33 pixels  
**Revisit Time:** ~6 days  
**Observed Bands:**

| Key | Polarization | Description |
|-----|-------------|-------------|
| VV | Vertical-Vertical | Surface roughness, structure, soil moisture |
| VH | Vertical-Horizontal | Vegetation volume scattering |
| angle | Incidence Angle | Per-acquisition incidence angle scalar |

**Key Advantage:** Cloud-penetrating radar — works in monsoon conditions where optical sensors fail.  
**Average Observations per Farm:** ~15 acquisitions  
**Filename Format:** `S1A_IW_GRDH_1SDV_YYYYMMDDTHHMMSS_...npz`

### 2.3 Landsat-8 (L8)

**Source:** USGS/NASA — OLI (Operational Land Imager) + TIRS (Thermal Infrared Sensor)  
**Spatial Resolution:** 30 m (optical), 100 m (thermal resampled to 30 m)  
**Image Size in Dataset:** 11 × 11 pixels at 30 m resolution (~3.3 ha coverage)  
**Revisit Time:** 16 days  
**Observed Bands:**

| Key | Description |
|-----|-------------|
| SR_B1 | Ultra Blue (Coastal/Aerosol) |
| SR_B2 | Blue |
| SR_B3 | Green |
| SR_B4 | Red |
| SR_B5 | Near-Infrared (NIR) |
| SR_B6 | SWIR 1 |
| SR_B7 | SWIR 2 |
| ST_B10 | Thermal Infrared (Land Surface Temperature) |
| QA_PIXEL | Pixel Quality Assessment (cloud flags) |
| QA_RADSAT | Radiometric Saturation |
| SR_QA_AEROSOL | Aerosol attributes |
| ST_ATRAN | Atmospheric transmittance |
| ST_CDIST | Cloud distance |
| ST_DRAD | Downwelling radiance |
| ST_EMSD | Emissivity standard deviation |
| ST_QA | Thermal quality |
| ST_TRAD | Thermal radiance |
| ST_URAD | Upwelling radiance |
| T_EMIS | Emissivity |

**Average Observations per Farm:** ~21 acquisitions  
**Unique Feature:** Thermal band (ST_B10) enables Land Surface Temperature (LST) monitoring — critical for drought and heat stress detection.

---

## 3. Tabular Dataset

**File:** `sickle_dataset/sickle_dataset_tabular.csv`  
**Shape:** 2,370 rows × 17 columns  
**Encoding:** UTF-8, comma-delimited

### 3.1 Column Definitions

| Column | Type | Missing | Description |
|--------|------|---------|-------------|
| `UNIQUE_ID` | int64 | 0 | Primary key for each farm-season record (0–2,410) |
| `PLOT_ID` | float64 | 206 | Physical farm plot identifier (1–448); 206 rows are padding entries |
| `RIVER_PART` | string | 525 | Sub-basin of Cauvery river delta (5 categories) |
| `STANDARD_SEASON` | string | 0 | Growing season as month-range string (7 categories) |
| `YEAR` | float64 | 0 | Crop year: 2018, 2019, or 2020 |
| `AREA` | float64 | 206 | Farm plot area in hectares (0.02–4.11) |
| `CROP` | string | 206 | Crop name (21 unique types) |
| `VARIETY` | string | 2,051 | Rice variety name (paddy-only; 19 varieties) |
| `PADDY_BIN` | float64 | 206 | Binary label: 1 = paddy rice, 2 = non-paddy crop |
| `SOWING_DATE` | string | 206 | Sowing date string (ISO-like) or '0' for non-paddy |
| `TRANSPLANTING_DATE` | string | 206 | Transplanting date or '0' |
| `HARVESTING_DATE` | string | 206 | Harvest date string or '0' |
| `SOWING_DAY` | float64 | 206 | Days from season start to sowing (relative offset) |
| `TRANSPLANTING_DAY` | float64 | 206 | Days from season start to transplanting |
| `HARVESTING_DAY` | float64 | 206 | Days from season start to harvest (0–184) |
| `YIELD` | float64 | 206 | Paddy yield in kg/ha (0 for non-paddy, up to 3,840 for paddy) |
| `SPLIT` | string | 0 | Dataset split: train / val / test |

### 3.2 Missing Value Analysis

| Column | Missing Count | Missing % | Reason |
|--------|-------------|-----------|--------|
| VARIETY | 2,051 | 86.5% | Only recorded for paddy crops |
| RIVER_PART | 525 | 22.2% | Unknown in 206 padding rows + data gaps |
| PLOT_ID, AREA, CROP, etc. | 206 | 8.7% | 206 synthetic padding rows added to complete seasonal grid |

**Note:** The 206 rows with all numeric columns = NaN represent seasonal grid-fill entries where no farm was observed for that season × plot combination.

### 3.3 Crop Distribution

| Crop | Count | % of Valid Records |
|------|-------|-------------------|
| Paddy | 907 | 41.9% |
| Banana | 499 | 23.1% |
| Coconut | 271 | 12.5% |
| Banyan | 180 | 8.3% |
| Sugarcane | 121 | 5.6% |
| Palm tree | 36 | 1.7% |
| Groundnut | 30 | 1.4% |
| Eucalyptus | 28 | 1.3% |
| Tamarind tree | 18 | 0.8% |
| Mixed plantation | 18 | 0.8% |
| Cotton | 14 | 0.6% |
| Brinjal | 6 | 0.3% |
| Betelwine | 6 | 0.3% |
| Teak | 6 | 0.3% |
| Mixed | 6 | 0.3% |
| Bhendi | 4 | 0.2% |
| Sesame | 4 | 0.2% |
| Green gram | 4 | 0.2% |
| Blackgram | 3 | 0.1% |
| Black gram | 2 | 0.1% |
| Tomato | 1 | 0.05% |
| **Total** | **2,164** | **100%** |

**Insight:** The dataset is heavily paddy-dominated (41.9%). 18 of 21 crops are rare (<2%). Multi-class crop classification will require oversampling or focal loss.

### 3.4 Year Distribution

| Year | Count | % |
|------|-------|---|
| 2018 | 663 | 28.0% |
| 2019 | 848 | 35.8% |
| 2020 | 859 | 36.2% |

### 3.5 Season Distribution

| Season | Count | Months | Crop Relevance |
|--------|-------|--------|----------------|
| aug-jan | 578 | Aug–Jan | Samba paddy, short-duration crops |
| jun-oct | 451 | Jun–Oct | Kuruvai paddy (early Kharif) |
| sep-feb | 417 | Sep–Feb | Thaladi paddy |
| oct-mar | 315 | Oct–Mar | Rabi season |
| dec-may | 299 | Dec–May | Summer crops |
| may-sep | 212 | May–Sep | Kharif onset |
| apr-aug | 98 | Apr–Aug | Short rabi / summer |

### 3.6 River Basin Distribution

| Sub-basin | Count | % |
|-----------|-------|---|
| Upper Cauvery | 769 | 44.3% |
| Middle Vennar | 406 | 23.4% |
| Coastal Cauvery | 334 | 19.3% |
| Coastal Vennar | 179 | 10.3% |
| Lower Cauvery | 157 | 9.1% |

### 3.7 Yield Statistics (Paddy Only, non-zero)

| Statistic | Value (kg/ha) |
|-----------|--------------|
| Count | 319 observations |
| Mean | 1,836 |
| Std Dev | 433 |
| Min | 800 |
| 25th percentile | 1,620 |
| Median | 1,800 |
| 75th percentile | 2,040 |
| Max | 3,840 |

**Note:** Tamil Nadu paddy average is ~2,500 kg/ha nationally. Dataset values (mean 1,836) suggest smallholder farms with below-average yields.

### 3.8 Farm Area Statistics

| Statistic | Value (hectares) |
|-----------|-----------------|
| Count | 2,164 |
| Mean | 0.35 ha |
| Std Dev | 0.47 ha |
| Min | 0.02 ha |
| 25th | 0.12 ha |
| Median | 0.19 ha |
| 75th | 0.38 ha |
| Max | 4.11 ha |

**Insight:** Median farm size is 0.19 ha — characteristic of Tamil Nadu smallholder agriculture. This is critical context for UZHAVAN AI: these are subsistence-scale farms, not commercial operations.

---

## 4. Images

### 4.1 Structure Overview

| Satellite | Format | Farms | Avg Temporal Obs | Array Shape (per obs) |
|-----------|--------|-------|-----------------|----------------------|
| Sentinel-2 | NPZ (per obs) + TIF (composite) | 2,370 | ~56 | (H×W) per band, varying by resolution |
| Sentinel-1 | NPZ (per obs) + TIF (composite) | 2,370 | ~15 | 33×33 per polarization |
| Landsat-8 | NPZ (per obs) + TIF (composite) | 2,371 | ~21 | 11×11 per band |

### 4.2 Sentinel-2 Image Details

- **Per-observation format:** NPZ archive with named arrays per band
- **10m bands (B2, B3, B4, B8, AOT, WVP):** ~34×33 pixels per farm
- **20m bands (B5–B7, B8A, B11, B12, SCL, MSK_CLDPRB):** ~17×17 pixels
- **60m bands (B1, B9):** ~7×6 pixels
- **Total S2 acquisitions:** 2,370 farms × ~56 obs = ~132,720 NPZ files
- **Training config image size:** 32×32 (padded/cropped to uniform size)

### 4.3 Sentinel-1 Image Details

- **Per-observation format:** NPZ with VV, VH, angle
- **Pixel dimensions:** 33×33 pixels per farm
- **Total S1 acquisitions:** 2,370 farms × ~15 obs = ~35,550 NPZ files

### 4.4 Landsat-8 Image Details

- **Per-observation format:** NPZ with 19 named arrays
- **Pixel dimensions:** 11×11 pixels per farm
- **Total L8 acquisitions:** 2,371 farms × ~21 obs = ~49,791 NPZ files
- **Filename date format:** `LC08_142052_YYYYMMDD.npz`

### 4.5 GeoTIFF Files

- **Purpose:** Single-file multi-temporal composites per farm for GIS tools
- **Count:** 2,371 TIF files per satellite (S2, S1, L8)
- **Usable in:** QGIS, ArcGIS, Google Earth Engine

---

## 5. Masks

### 5.1 Overview

| Resolution | Count | Format | Use Case |
|-----------|-------|--------|---------|
| 10m | 2,164 | GeoTIFF (.tif) | Sentinel-2 spatial alignment |
| 30m | 2,164 | GeoTIFF (.tif) | Landsat-8 spatial alignment |
| 3m | 2,164 | GeoTIFF (.tif) | High-resolution field boundary delineation |

**Total mask files:** 6,492

### 5.2 Naming Convention

Masks are named by `UNIQUE_ID` integer (e.g., `0.tif`, `1.tif`, ..., `2410.tif`), directly linking to the tabular CSV via `UNIQUE_ID` column.

### 5.3 Label Semantics

Based on model training configs (`num_classes: 2`, `ignore_index: -999`):

| Pixel Value | Meaning |
|------------|---------|
| 0 | Background / non-farm area |
| 1 | Paddy rice pixel |
| 2 | Non-paddy crop pixel |
| -999 (as ignore) | No-data / invalid |

The masks serve dual purpose:
1. **Spatial masks** — define the farm boundary polygon as a raster
2. **Semantic labels** — encode crop class within the farm boundary

---

## 6. Dataset Statistics

### 6.1 High-Level Summary

| Metric | Value |
|--------|-------|
| Total records | 2,370 |
| Valid farm records | 2,164 |
| Unique farm plots | 351 |
| Crop types | 21 |
| Years covered | 3 (2018, 2019, 2020) |
| Growing seasons | 7 |
| River sub-basins | 5 |
| Satellite sources | 3 (S2, S1, L8) |
| Total images (approx.) | ~218,000 NPZ files |
| Total mask files | 6,492 |
| Train / Val / Test | 1,937 / 227 / 206 |

### 6.2 Paddy vs Non-Paddy

| Class | Count | % |
|-------|-------|---|
| Paddy (PADDY_BIN=1) | 907 | 41.9% |
| Non-Paddy (PADDY_BIN=2) | 1,257 | 58.1% |

### 6.3 Yield Coverage

| Metric | Value |
|--------|-------|
| Farms with yield data | 319 (paddy only) |
| Farms with yield = 0 | 1,845 (non-paddy or missing) |
| Mean yield (paddy, non-zero) | 1,836 kg/ha |
| Max yield | 3,840 kg/ha |

---

## 7. Models

All models are stored in `runs/wacv_2024/` with per-task and per-satellite-combination subfolders. Each experiment contains:
- `conf.json` — full training configuration
- `trainlog.json` — per-epoch train/val metrics (100 epochs)
- `checkpoint_best.pth.tar` — best validation checkpoint (PyTorch)
- `checkpoint_last.pth.tar` — final epoch checkpoint

### 7.1 ConvLSTM

**Architecture:** Convolutional Long Short-Term Memory Network  
**Design Principle:** Replaces fully-connected LSTM gates with convolutional operations, preserving spatial structure across time steps.  
**Encoder:** Two-stage convolutional encoder (widths: [64, 128])  
**Decoder:** Symmetric decoder (widths: [32, 128])  
**Temporal Handling:** Hidden states carry spatial-temporal context through sequence  
**Parameters:** ~1.07M (S2 config)  
**Strength:** Captures local spatial patterns and sequential dependencies simultaneously  
**Weakness:** Computationally expensive for long sequences; limited global context

### 7.2 UTAE (U-Net with Temporal Attention Encoder)

**Architecture:** U-Net backbone augmented with a Lightweight Temporal Attention Encoder  
**Design Principle:** The LTAE module attends over the time dimension using multi-head self-attention with positional encoding, then feeds the aggregated feature to a standard U-Net decoder.  
**Encoder:** Two-stage convolutional (widths: [64, 128]), `n_head=16`, `d_model=256`, `d_k=4`  
**Attention:** Group-based temporal attention (`agg_mode: att_group`)  
**Positional Encoding:** Encodes acquisition day-of-year to model seasonal patterns  
**Parameters:** ~1.07M  
**Strength:** Handles variable-length temporal sequences elegantly; learns which time steps matter most  
**Weakness:** Attention weights can be noisy with very short or irregular sequences

### 7.3 UNet3D

**Architecture:** 3D U-Net treating the time dimension as depth  
**Design Principle:** Standard U-Net but with 3D convolutions that process (Time × Height × Width) volumetrically  
**Encoder/Decoder:** Strided 3D convolutions (`str_conv_k=4, str_conv_s=2, str_conv_p=1`)  
**Parameters:** ~1.07M  
**Strength:** Implicitly models spatiotemporal correlations; effective when temporal and spatial patterns are interleaved  
**Weakness:** Requires uniform time-series length (padding needed for variable-length sequences); high memory usage for long sequences

### 7.4 Model Performance Summary

#### Crop Type Classification (F1 Score — higher is better)

| Model | S2 | S1 | L8 | S2+L8+S1 |
|-------|----|----|----|----|
| UNet3D | 0.789 | **0.823** | 0.796 | **0.839** |
| ConvLSTM | 0.509 | 0.492 | 0.767 | 0.752 |
| UTAE | 0.433 | 0.442 | 0.433 | 0.433 |

#### Crop Yield (RMSE kg/ha — lower is better)

| Model | S2 | S1 | L8 | S2+L8+S1 |
|-------|----|----|----|----|
| UNet3D_season | 995 | 1234 | 1123 | **810** |
| UTAE_season | 830 | 780 | 839 | **749** |
| ConvLSTM_season | 796 | 849 | 851 | 843 |

#### Harvesting Date Prediction (MAE days — lower is better)

| Model | S2 | S1 | L8 | S2+L8+S1 |
|-------|----|----|----|----|
| UNet3D | 11.2 | 9.6 | **8.6** | 9.9 |
| UTAE | 12.6 | 10.5 | 17.7 | 10.9 |
| ConvLSTM | 21.0 | 18.5 | 17.9 | 15.0 |

#### Sowing Date Prediction (MAE days — lower is better)

| Model | S2 | S1 | L8 | S2+L8+S1 |
|-------|----|----|----|----|
| UNet3D | 2.77 | 4.76 | **2.88** | **2.40** |
| UTAE | 4.73 | 4.21 | 3.81 | 4.62 |
| ConvLSTM | 4.12 | 4.04 | 4.23 | 3.82 |

#### Transplanting Date Prediction (MAE days — lower is better)

| Model | S2 | S1 | L8 | S2+L8+S1 |
|-------|----|----|----|----|
| UNet3D | 6.09 | 6.14 | **4.37** | 4.37 |
| UTAE | 5.90 | 5.83 | 5.14 | 5.78 |
| ConvLSTM | 5.74 | 5.83 | 5.71 | 4.57 |

**Overall Best Architecture:** UNet3D with multi-satellite fusion (S2+L8+S1) for most tasks. UTAE_season is competitive for yield prediction.

---

## 8. ML Tasks Supported

### 8.1 Crop Classification

- **Type:** Binary (paddy / non-paddy) and multi-class (21 crops)
- **Label source:** `CROP` and `PADDY_BIN` columns
- **Spatial labels:** Mask files (0/1/2 pixel classes)
- **Input:** Multi-temporal satellite image sequence
- **Best model:** UNet3D with S2+L8+S1 fusion (F1 = 0.839)
- **Challenge:** 21-class classification is severely imbalanced (paddy 41.9%, tomato 0.05%)

### 8.2 Yield Prediction

- **Type:** Regression (kg/ha)
- **Label source:** `YIELD` column
- **Coverage:** Paddy only (319 records with non-zero yield)
- **Best result:** RMSE ~749 kg/ha (UTAE_season, S2+L8+S1)
- **Challenge:** Only 319 yield labels — small training set for regression

### 8.3 Harvest Date Prediction

- **Type:** Regression (days from season start)
- **Label source:** `HARVESTING_DAY`
- **Range:** 0–184 days
- **Best result:** MAE ~8.6 days (UNet3D, L8)
- **Application:** Harvest scheduling, logistics planning

### 8.4 Sowing Date Prediction

- **Type:** Regression (days from season start)
- **Label source:** `SOWING_DAY`
- **Best result:** MAE ~2.4 days (UNet3D, S2+L8+S1)
- **Application:** Irrigation scheduling, input planning

### 8.5 Transplanting Date Prediction

- **Type:** Regression (days from season start)
- **Label source:** `TRANSPLANTING_DAY`
- **Coverage:** Paddy only (transplanting is paddy-specific)
- **Best result:** MAE ~4.4 days (UNet3D, S2+L8+S1 and L8)
- **Application:** Labor planning, fertilizer timing

### 8.6 Semantic Segmentation

- **Type:** Per-pixel crop classification
- **Input:** Satellite imagery at farm boundary
- **Output:** Pixel-wise crop type or farm boundary map
- **Resolution:** 10m, 30m, or 3m depending on mask used
- **Application:** Farm boundary delineation, precision field mapping

---

## 9. Integration into Precision Farming (UZHAVAN AI)

The SICKLE dataset enables a satellite-first precision agriculture AI platform for Tamil Nadu. The following integration strategy maps dataset capabilities to platform modules:

### 9.1 Core Model Services

```
SICKLE Dataset
      │
      ├── Crop Type API ──────────── Identifies paddy vs. non-paddy from S1/S2/L8
      ├── Yield Forecast API ──────── Predicts kg/ha 4-6 weeks before harvest
      ├── Harvest Calendar API ────── Predicts harvest date ± 8 days
      ├── Sowing Advisory API ──────── Recommends sowing window ± 2 days
      └── Transplanting API ────────── Predicts transplanting window ± 4 days
```

### 9.2 Farm Intelligence Layer

- **River basin stratification:** Use `RIVER_PART` to localize predictions by Cauvery sub-basin
- **Season-aware inference:** `STANDARD_SEASON` guides which model variant to deploy
- **Area-normalized yield:** Combine `YIELD` and `AREA` for yield-per-hectare metrics
- **Crop-type gating:** Run paddy-specific models only when `PADDY_BIN=1` is predicted

### 9.3 Satellite Data Pipeline

```
Google Earth Engine / Copernicus Hub
         │
         ▼ (weekly acquisition)
    S2 + S1 + L8 Preprocessor
         │
         ├── Band extraction → NPZ format
         ├── Cloud masking (SCL / MSK_CLDPRB)
         └── Farm boundary crop (mask files)
              │
              ▼
        SICKLE-trained models
              │
              ├── Crop Type → Dashboard
              ├── Yield Estimate → Alert system
              └── Calendar Events → SMS/WhatsApp to farmers
```

---

## 10. Limitations

### 10.1 Geographic Scope

The dataset is confined to Tamil Nadu's Cauvery river delta. Models trained on SICKLE will not generalize directly to:
- Other Indian states (different crop varieties, soil types, agro-climatic zones)
- Crops not present in the dataset (wheat, rice from Punjab, etc.)
- Non-river-irrigated rain-fed farming systems

### 10.2 Crop Imbalance

21 crop types with extreme imbalance (paddy=907, tomato=1). Any multi-class model will have poor precision on rare crops. Practically, the dataset supports binary paddy/non-paddy classification reliably.

### 10.3 Yield Data Gap

Only 319 of 2,164 valid records have non-zero yield labels (14.7%). Yield is only recorded for paddy. No yield data for banana, coconut, sugarcane — the dominant non-paddy crops.

### 10.4 Temporal Coverage

Three years (2018–2020) is a relatively short observation window. Models may not capture decadal trends, multi-year El Niño/La Niña cycles, or climate change trajectories.

### 10.5 Farm Size Bias

Median farm 0.19 ha. Satellite pixels at 10m resolution may cover multiple farms in dense agricultural areas, creating mixed-pixel issues.

### 10.6 No Weather Data

No meteorological data (rainfall, temperature, humidity) is included. Weather is a first-order driver of yield. Models that ignore it will have limited predictive accuracy.

### 10.7 No Soil Data

No soil health indicators (N, P, K, pH, organic carbon). Yield prediction without soil data leaves a major explanatory variable unexplained.

### 10.8 Label Noise

Sowing/transplanting/harvesting dates are farmer-reported and may carry ±5–10 day uncertainty, which propagates into model error floors.

---

*End of SICKLE Dataset Technical Audit*  
*Report Version 1.0 — UZHAVAN AI Project — June 2026*
