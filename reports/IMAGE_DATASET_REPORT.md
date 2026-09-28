# SICKLE Image Dataset — Technical Analysis Report

**Report Date:** June 30, 2026  
**Project:** UZHAVAN AI  
**Scope:** All satellite imagery in `sickle_dataset/images/`

---

## 1. Dataset Overview

The SICKLE image dataset contains multi-temporal satellite imagery from three sensors covering 2,370 agricultural farms across Tamil Nadu's Cauvery river delta (2018–2020).

| Metric | Value |
|--------|-------|
| Total farms covered | 2,370 |
| Satellite sources | 3 (Sentinel-2, Sentinel-1, Landsat-8) |
| Image formats | NPZ (per-acquisition archives) + GeoTIFF (composites) |
| Total NPZ folders | ~7,110 (2,370 farms × 3 satellites) |
| Estimated total NPZ files | ~218,000 individual acquisitions |
| Total TIF files | ~7,113 (2,371 per satellite × 3) |
| Mask files | 6,492 (2,164 per resolution × 3 resolutions) |

---

## 2. Sentinel-2 (S2) Images

### 2.1 Resolution and Bands

| Band | Wavelength | Spatial Res | Shape per Farm |
|------|-----------|------------|---------------|
| B1 (Coastal Aerosol) | 443 nm | 60 m | ~7 × 6 pixels |
| B2 (Blue) | 490 nm | 10 m | ~34 × 33 pixels |
| B3 (Green) | 560 nm | 10 m | ~34 × 33 pixels |
| B4 (Red) | 665 nm | 10 m | ~34 × 33 pixels |
| B5 (Red Edge 1) | 705 nm | 20 m | ~17 × 17 pixels |
| B6 (Red Edge 2) | 740 nm | 20 m | ~17 × 17 pixels |
| B7 (Red Edge 3) | 783 nm | 20 m | ~17 × 17 pixels |
| B8 (NIR) | 842 nm | 10 m | ~34 × 33 pixels |
| B8A (NIR Narrow) | 865 nm | 20 m | ~17 × 17 pixels |
| B9 (Water Vapour) | 945 nm | 60 m | ~7 × 6 pixels |
| B11 (SWIR 1) | 1610 nm | 20 m | ~17 × 17 pixels |
| B12 (SWIR 2) | 2190 nm | 20 m | ~17 × 17 pixels |
| AOT (Aerosol Optical Thickness) | — | 10 m | ~34 × 33 pixels |
| WVP (Water Vapour Pressure) | — | 10 m | ~34 × 33 pixels |
| SCL (Scene Classification) | — | 20 m | ~17 × 17 pixels |
| MSK_CLDPRB (Cloud Prob.) | — | 20 m | ~17 × 17 pixels |

**Total bands per acquisition:** 16 arrays (stored as keys in NPZ archive)  
**Data type:** float32  
**Training image size:** Standardized to 32 × 32 pixels at 10 m resolution

### 2.2 Temporal Coverage

- **Average observations per farm:** ~56 acquisitions over 3 years
- **Minimum observations:** ~17 (sparse acquisitions, cloud-affected periods)
- **Maximum observations:** ~74 (clear-sky, high revisit periods)
- **Filename format:** `YYYYMMDDTHHMMSS_YYYYMMDDTHHMMSS_T44PKT.npz`
  - First timestamp: sensing start time
  - Second timestamp: sensing stop time
  - T44PKT: Sentinel-2 MGRS tile identifier for Tamil Nadu

### 2.3 Storage Estimates

| Unit | S2 Size Estimate |
|------|-----------------|
| Per acquisition (16 bands × 34×33 float32) | ~0.07 MB |
| Per farm (56 acquisitions) | ~3.9 MB |
| Entire dataset (2,370 farms) | ~9.3 GB |

### 2.4 Band Selection for ML Models

From `conf.json` training configs, the standard S2 band stack used for model training:
```json
["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12"]
```
12 spectral bands; AOT, WVP, SCL, MSK_CLDPRB excluded from model inputs (used for preprocessing).

**RGB visualization bands:** B4 (Red=index 3), B3 (Green=index 2), B2 (Blue=index 1)

---

## 3. Sentinel-1 (S1) Images

### 3.1 Resolution and Bands

| Key | Description | Spatial Res | Shape per Farm |
|-----|-------------|------------|---------------|
| VV | Vertical-Vertical Polarization | ~10 m | 33 × 33 pixels |
| VH | Vertical-Horizontal Polarization | ~10 m | 33 × 33 pixels |
| angle | Local incidence angle | Per-scene scalar | 1 × 1 |

**Acquisition mode:** IW (Interferometric Wide swath) GRDH (Ground Range Detected High Resolution)  
**Data type:** float32 (backscatter coefficient in linear power units)  
**Typical value range:** -25 to 0 dB (log scale); stored as linear

### 3.2 Temporal Coverage

- **Average observations per farm:** ~15 acquisitions over 3 years
- **Revisit time:** Every 6 days (Sentinel-1A + 1B constellation)
- **Filename format:** `S1A_IW_GRDH_1SDV_YYYYMMDDTHHMMSS_YYYYMMDDTHHMMSS_<orbit>_<frame>_<prod>.npz`

### 3.3 Key Advantage for Precision Agriculture

Sentinel-1 C-band SAR penetrates clouds and rain. In Tamil Nadu's monsoon-dominated agriculture (June–November), optical sensors (S2, L8) may have >80% cloud cover for months. S1 provides uninterrupted temporal monitoring.

**SAR Vegetation Indices Computable from VV/VH:**
- Cross-ratio (CR): VH/VV — sensitive to vegetation structure
- RVI (Radar Vegetation Index): 4×VH/(VV+VH) — plant density proxy
- DPSVI: Dual-polarization SAR vegetation index

### 3.4 Storage Estimates

| Unit | S1 Size Estimate |
|------|-----------------|
| Per acquisition (3 arrays × 33×33 float32) | ~0.012 MB |
| Per farm (15 acquisitions) | ~0.18 MB |
| Entire dataset (2,370 farms) | ~0.43 GB |

---

## 4. Landsat-8 (L8) Images

### 4.1 Resolution and Bands

| Key | Description | Spatial Res | Shape per Farm |
|-----|-------------|------------|---------------|
| SR_B1 | Ultra Blue (Coastal) | 30 m | 11 × 11 pixels |
| SR_B2 | Blue | 30 m | 11 × 11 pixels |
| SR_B3 | Green | 30 m | 11 × 11 pixels |
| SR_B4 | Red | 30 m | 11 × 11 pixels |
| SR_B5 | NIR | 30 m | 11 × 11 pixels |
| SR_B6 | SWIR 1 | 30 m | 11 × 11 pixels |
| SR_B7 | SWIR 2 | 30 m | 11 × 11 pixels |
| ST_B10 | Thermal (LST) | 100→30 m | 11 × 11 pixels |
| QA_PIXEL | Pixel Quality | 30 m | 11 × 11 pixels |
| QA_RADSAT | Radiometric Saturation | 30 m | 11 × 11 pixels |
| SR_QA_AEROSOL | Aerosol | 30 m | 11 × 11 pixels |
| ST_ATRAN | Atm. Transmittance | 30 m | 11 × 11 pixels |
| ST_CDIST | Cloud Distance | 30 m | 11 × 11 pixels |
| ST_DRAD | Downwelling Radiance | 30 m | 11 × 11 pixels |
| ST_EMSD | Emissivity Std Dev | 30 m | 11 × 11 pixels |
| ST_QA | Thermal QA | 30 m | 11 × 11 pixels |
| ST_TRAD | Thermal Radiance | 30 m | 11 × 11 pixels |
| ST_URAD | Upwelling Radiance | 30 m | 11 × 11 pixels |
| T_EMIS | Emissivity | 30 m | 11 × 11 pixels |

**Total bands per acquisition:** 19  
**Data type:** float32  
**Filename format:** `LC08_142052_YYYYMMDD.npz` (Path 142, Row 052 — Tamil Nadu scene)

### 4.2 Temporal Coverage

- **Average observations per farm:** ~21 acquisitions
- **Revisit time:** 16 days
- **Filename date:** Encoded directly as `YYYYMMDD` — calendar dates parseable

### 4.3 Unique Value: Thermal Band (ST_B10)

Landsat-8 is the only sensor in this dataset with a thermal infrared band. This enables:
- Land Surface Temperature (LST) estimation
- Crop water stress detection (evapotranspiration proxy)
- Soil moisture inference
- Heat stress early warning

### 4.4 Storage Estimates

| Unit | L8 Size Estimate |
|------|-----------------|
| Per acquisition (19 arrays × 11×11 float32) | ~0.009 MB |
| Per farm (21 acquisitions) | ~0.19 MB |
| Entire dataset (2,371 farms) | ~0.45 GB |

---

## 5. TIFF Properties

GeoTIFF files are stored in `images/{S2,S1,L8}/tif/` directories.

| Property | S2 TIF | S1 TIF | L8 TIF |
|----------|--------|--------|--------|
| Format | GeoTIFF | GeoTIFF | GeoTIFF |
| Coordinate System | UTM Zone 44N (EPSG:32644) | UTM Zone 44N | UTM Zone 44N |
| Projection | WGS84 | WGS84 | WGS84 |
| Files per satellite | 2,371 | 2,371 | 2,370 |
| Naming | By UNIQUE_ID integer | By UNIQUE_ID | By UNIQUE_ID |
| Use case | GIS visualization, composites | GIS visualization | GIS visualization |

The GeoTIFF files serve as multi-temporal composites for GIS inspection. NPZ files are used for model training due to their compressed per-band storage.

---

## 6. NPZ Tensor Shapes

### For Deep Learning Models

When loading all temporal acquisitions for a single farm, the models create 4D tensors:

| Satellite | Tensor Shape | Meaning |
|-----------|-------------|---------|
| S2 | (T, 12, 32, 32) | T=time steps, 12 bands, 32×32 spatial |
| S1 | (T, 2, 33, 33) | T=time steps, VV+VH, 33×33 spatial |
| L8 | (T, 7, 11, 11) | T=time steps, 7 SR bands, 11×11 spatial |

**T (time steps):** Variable per farm (S2: 17–74, S1: 12–23, L8: 9–33). Models handle variable-length sequences via padding, masking, or attention mechanisms.

**Multi-satellite fusion tensor (for [S2,L8,S1] models):**
- Each sensor processed by separate encoder
- Encoder outputs projected to common feature dimension (d_model=256)
- Concatenated or attention-fused for decoder

---

## 7. Memory Requirements

### Training Memory Estimates (per batch of 32 farms)

| Satellite | Sequence Length | Bands | Spatial | Batch Memory |
|-----------|----------------|-------|---------|-------------|
| S2 | 56 obs × 12 bands × 32×32 | 12 | 32×32 | ~1.5 GB |
| S1 | 15 obs × 2 bands × 33×33 | 2 | 33×33 | ~0.08 GB |
| L8 | 21 obs × 7 bands × 11×11 | 7 | 11×11 | ~0.07 GB |
| S2+S1+L8 fusion | Combined | — | — | ~1.7 GB |

**GPU VRAM requirement:** Minimum 8 GB for single-satellite models, 16 GB for multi-fusion.

### Disk Storage Summary

| Component | Estimated Size |
|-----------|---------------|
| S2 NPZ files | ~9.3 GB |
| S1 NPZ files | ~0.4 GB |
| L8 NPZ files | ~0.5 GB |
| TIF files (all 3) | ~2.0 GB |
| Mask files (3 resolutions) | ~0.5 GB |
| Model checkpoints (all runs) | ~15–20 GB |
| **Total dataset** | **~30 GB** |

---

## 8. Spectral Indices Derivable from Images

### From Sentinel-2

| Index | Formula | Application |
|-------|---------|------------|
| NDVI | (B8-B4)/(B8+B4) | Vegetation health |
| EVI | 2.5×(B8-B4)/(B8+6×B4-7.5×B2+1) | Enhanced vegetation |
| LSWI | (B8-B11)/(B8+B11) | Leaf water content |
| NDWI | (B3-B8)/(B3+B8) | Water bodies |
| NDRE | (B8A-B5)/(B8A+B5) | Red edge (crop stress) |
| SAVI | ((B8-B4)/(B8+B4+0.5))×1.5 | Soil-adjusted vegetation |
| CIre | B7/B5 - 1 | Chlorophyll index |
| SWIR ratio | B11/B12 | Soil moisture |

### From Sentinel-1

| Index | Formula | Application |
|-------|---------|------------|
| CR | VH/VV | Vegetation structure |
| RVI | 4×VH/(VV+VH) | Radar vegetation index |
| RFDI | (VV-VH)/(VV+VH) | Roughness index |

### From Landsat-8

| Index | Formula | Application |
|-------|---------|------------|
| NDVI | (SR_B5-SR_B4)/(SR_B5+SR_B4) | Vegetation |
| LST | Derived from ST_B10 | Land surface temperature |
| NDWI | (SR_B3-SR_B5)/(SR_B3+SR_B5) | Water stress |
| NBR | (SR_B5-SR_B7)/(SR_B5+SR_B7) | Burn ratio |

---

## 9. Data Quality Notes

### Cloud Contamination
- S2 and L8 optical images are affected by clouds during Tamil Nadu monsoon (June–September)
- `SCL` (S2) and `QA_PIXEL` (L8) bands provide per-pixel cloud flags
- Effective S2 clear-sky observations drop to ~20-30 during peak monsoon
- S1 SAR is unaffected by clouds — critical fallback

### Seasonal Gaps
- Some farms may have 0 valid optical observations during peak cloud season
- Models must handle missing timesteps gracefully (padding with 0, mask-based attention)

### Spatial Resolution Mismatch
- S2 (~10m) vs S1 (~10m) vs L8 (30m) — requires careful alignment for multi-sensor fusion
- Farm boundaries at 10m may span just 3×3 L8 pixels (11×11 with buffer)

### Mixed Pixels
- Farms smaller than 0.19 ha (median) may have significant boundary pixels mixing the farm with adjacent land

---

## 10. Visualization Recipes

### RGB Composite (Sentinel-2)
```python
import numpy as np
import matplotlib.pyplot as plt

def s2_rgb(npz_path):
    data = np.load(npz_path)
    rgb = np.stack([data['B4'], data['B3'], data['B2']], axis=-1)
    rgb = np.clip(rgb / 3000, 0, 1)  # Normalize to 0-1
    return rgb
```

### NDVI Time Series
```python
def ndvi_timeseries(farm_npz_dir):
    """Compute NDVI for each acquisition in a farm's S2 folder"""
    ndvi_series = []
    for f in sorted(os.listdir(farm_npz_dir)):
        data = np.load(f'{farm_npz_dir}/{f}')
        nir, red = data['B8'], data['B4']
        ndvi = (nir - red) / (nir + red + 1e-8)
        ndvi_series.append((f[:8], ndvi.mean()))  # date, mean NDVI
    return ndvi_series
```

### SAR VH/VV Composite
```python
def s1_composite(npz_path):
    data = np.load(npz_path)
    vv = 10 * np.log10(data['VV'] + 1e-10)  # Convert to dB
    vh = 10 * np.log10(data['VH'] + 1e-10)
    cr = vh - vv  # Cross-ratio
    rgb = np.stack([vv, vh, cr], axis=-1)
    return rgb
```

---

*End of Image Dataset Report*  
*Report Version 1.0 — UZHAVAN AI Project — June 2026*
