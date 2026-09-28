# SICKLE Dataset — Feature Engineering Report

**Role:** Machine Learning Engineer  
**Project:** UZHAVAN AI  
**Report Date:** June 30, 2026

---

## Overview

This report documents every feature that can be engineered from the SICKLE dataset. Features are organized by source type: spectral indices, temporal features, tabular features, cross-modal fusion features, and spatial features.

---

## 1. Spectral Index Features (from Satellite Bands)

### 1.1 Sentinel-2 Vegetation Indices

| Feature Name | Formula | Bands Used | Agri Significance |
|-------------|---------|-----------|------------------|
| NDVI | (B8−B4)/(B8+B4) | NIR, Red | Primary vegetation health index |
| EVI | 2.5×(B8−B4)/(B8+6×B4−7.5×B2+1) | NIR, Red, Blue | Reduces atmosphere and soil effects |
| EVI2 | 2.5×(B8−B4)/(B8+2.4×B4+1) | NIR, Red | EVI without blue band |
| SAVI | 1.5×(B8−B4)/(B8+B4+0.5) | NIR, Red | Soil-adjusted, good for sparse veg |
| MSAVI | (2×B8+1−√((2×B8+1)²−8×(B8−B4)))/2 | NIR, Red | Modified SAVI |
| NDWI_leaf | (B8A−B11)/(B8A+B11) = LSWI | NIR_narrow, SWIR1 | Leaf water content, irrigation status |
| NDWI_body | (B3−B8)/(B3+B8) | Green, NIR | Open water, flooded fields |
| NDRE | (B8A−B5)/(B8A+B5) | NIR_narrow, Red Edge | Crop N-stress, chlorophyll |
| CIre | B7/B5 − 1 | Red Edge3, Red Edge1 | Chlorophyll index (red edge) |
| CIgreen | B8A/B3 − 1 | NIR_narrow, Green | Chlorophyll index (green) |
| SWIR ratio | B11/B12 | SWIR1, SWIR2 | Soil moisture, litter |
| BSI | ((B11+B4)−(B8+B2))/((B11+B4)+(B8+B2)) | SWIR1,Red,NIR,Blue | Bare soil index |
| NDSI (soil) | (B11−B8)/(B11+B8) | SWIR1, NIR | Soil index |
| RVI (optical) | B8/B4 | NIR, Red | Simple ratio vegetation |
| ARVI | (B8−(2×B4−B2))/(B8+(2×B4−B2)) | NIR, Red, Blue | Atm-resistant VI |
| VARI | (B3−B4)/(B3+B4−B2) | Green, Red, Blue | Visible atm-resistant VI |
| WDRVI | (α×B8−B4)/(α×B8+B4), α=0.1 | NIR, Red | Wide dynamic range VI |

### 1.2 Sentinel-1 SAR Features

| Feature Name | Formula | Significance |
|-------------|---------|-------------|
| Cross-ratio (CR) | VH / VV | Vegetation canopy density |
| RVI_SAR | 4×VH / (VV+VH) | Radar vegetation index |
| RFDI | (VV−VH) / (VV+VH) | Roughness index |
| VV_dB | 10×log10(VV) | Surface roughness in dB |
| VH_dB | 10×log10(VH) | Volume scattering in dB |
| VV_VH_diff | VV_dB − VH_dB | Polarization contrast |
| DPSVWI | VV×VH / (VV+VH)² | Dual-pol vol.-water index |

### 1.3 Landsat-8 Thermal & Spectral

| Feature Name | Formula | Significance |
|-------------|---------|-------------|
| NDVI_L8 | (SR_B5−SR_B4)/(SR_B5+SR_B4) | Vegetation (backup for cloudy S2) |
| NDWI_L8 | (SR_B3−SR_B5)/(SR_B3+SR_B5) | Water body / irrigation |
| LST | Derived from ST_B10 + T_EMIS | Land Surface Temperature (°C) |
| LST_anomaly | LST − historical mean LST | Heat stress detection |
| NBR | (SR_B5−SR_B7)/(SR_B5+SR_B7) | Burn ratio |
| NDTI | (SR_B6−SR_B7)/(SR_B6+SR_B7) | Tillage index |
| ET_proxy | f(LST, NDVI) | Evapotranspiration proxy |

---

## 2. Temporal Features (Time Series Engineering)

### 2.1 NDVI Time Series Statistics

| Feature | Computation | ML Value |
|---------|------------|---------|
| NDVI_mean | Mean NDVI over season | Baseline vegetation status |
| NDVI_max | Peak NDVI in season | Peak biomass |
| NDVI_min | Minimum NDVI in season | Dormancy / bare soil baseline |
| NDVI_std | Std dev of NDVI over season | Variability = stress indicator |
| NDVI_range | NDVI_max − NDVI_min | Phenological amplitude |
| NDVI_slope | Linear trend of NDVI vs time | Crop growth rate |
| NDVI_peak_doy | Day of year at NDVI peak | Phenology timing |
| NDVI_green_up | Day when NDVI crosses 0.4 | Green-up date |
| NDVI_senescence | Day when NDVI drops below 0.4 after peak | Senescence date |
| NDVI_integral | Area under NDVI curve (growing season) | Total photosynthetic activity |
| NDVI_half_max_up | Day NDVI reaches 50% of peak (rising) | Early canopy closure |
| NDVI_half_max_down | Day NDVI reaches 50% of peak (falling) | Grain filling completion |

### 2.2 Season Length Features

| Feature | Computation | ML Value |
|---------|------------|---------|
| SEASON_LENGTH | HARVESTING_DAY − SOWING_DAY | Total crop duration (days) |
| VEG_PERIOD | NDVI_senescence − NDVI_green_up | Active vegetative days |
| SOWING_DELAY | SOWING_DAY − season_typical_start | Late sowing penalty |
| TRANSPLANTING_DURATION | TRANSPLANTING_DAY − SOWING_DAY | Nursery duration |
| GRAIN_FILL_PERIOD | HARVESTING_DAY − TRANSPLANTING_DAY | Reproductive stage duration |

### 2.3 Harvest Duration Features

| Feature | Computation | ML Value |
|---------|------------|---------|
| HARVEST_DURATION | NDVI drop rate after peak | Harvest window width |
| DAYS_TO_MATURITY | TRANSPLANTING_DAY to HARVESTING_DAY | Variety-specific duration |
| HARVEST_TIMING_DELTA | Actual harvest − predicted harvest | Model residual feature |

### 2.4 Weather-Proxy Temporal Features (from L8 thermal)

| Feature | Computation | ML Value |
|---------|------------|---------|
| LST_max_season | Peak LST during season | Heat stress maximum |
| LST_min_season | Minimum LST during season | Cold stress minimum |
| LST_mean_season | Average LST | Growing degree days proxy |
| LST_anomaly_flag | Flag: LST > historical 90th pct | Unusual heat event |
| LST_consecutive_hot | Max consecutive hot days (LST > threshold) | Prolonged stress |

### 2.5 SAR Temporal Features (all-weather)

| Feature | Computation | ML Value |
|---------|------------|---------|
| S1_VH_max | Peak VH backscatter | Maximum canopy density |
| S1_VH_slope_up | VH growth rate (vegetative phase) | Growth rate |
| S1_VH_slope_down | VH decline rate (harvest phase) | Harvest detection |
| S1_RVI_mean | Mean RVI over season | Vegetation density average |
| S1_flood_flag | VV < flood threshold (−18 dB) | Paddy flood detection |
| S1_transplant_signal | VH spike after transplanting | Transplanting event detection |

### 2.6 Multi-temporal Correlation Features

| Feature | Computation | ML Value |
|---------|------------|---------|
| S2_S1_NDVI_correlation | Pearson(NDVI, VH) over time | Coherence of optical-SAR |
| CLOUD_FREE_PCT | % observations without cloud | Data quality metric |
| OBS_DENSITY | Observations per 30-day window | Temporal data coverage |
| INTERP_QUALITY | Std dev of cloud-gap interpolation | Feature reliability score |

---

## 3. Tabular / Agronomic Features

### 3.1 Area-Normalized Features

| Feature | Formula | ML Value |
|---------|---------|---------|
| YIELD_PER_HA | YIELD / AREA | Standardized productivity |
| LOG_AREA | log(1 + AREA) | Linearize right-skewed area |
| AREA_CATEGORY | Bins: micro (<0.1), small (0.1–0.5), medium (0.5–2), large (>2) | Ordinal area class |
| AREA_DEVIATION | AREA − mean(AREA for crop type) | Area vs. crop-type average |

### 3.2 Yield Normalization Features

| Feature | Formula | ML Value |
|---------|---------|---------|
| YIELD_Z_SCORE | (YIELD − basin_mean_yield) / basin_std | Performance vs. local baseline |
| YIELD_PERCENTILE | Rank within same basin×season | Relative performance |
| YIELD_TREND | YIELD vs. year (per farm) | Farm improvement/decline |
| YIELD_DEVIATION | YIELD − season_mean_yield | Good/bad season indicator |

### 3.3 Season Encoding Features

| Feature | Computation | ML Value |
|---------|------------|---------|
| SEASON_START_MONTH | Extract month from season string | Numeric month |
| SEASON_END_MONTH | Extract end month | Numeric month |
| SEASON_SIN | sin(2π×start_month/12) | Cyclical encoding |
| SEASON_COS | cos(2π×start_month/12) | Cyclical encoding |
| IS_SAMBA | Boolean: season == 'aug-jan' | Main paddy season flag |
| IS_MONSOON | Boolean: start_month in [6,7,8,9] | Rain-fed season |
| IS_RABI | Boolean: start_month in [10,11,12] | Winter/dry season |

### 3.4 River Basin Encoding

| Feature | Computation | ML Value |
|---------|------------|---------|
| BASIN_ONEHOT | One-hot: 5 binary columns | Basin for tree models |
| BASIN_EMBEDDING | Learned embedding (dim=8) | Basin for neural models |
| COASTAL_FLAG | Boolean: 'Coastal' in RIVER_PART | Proximity to sea |
| UPPER_FLAG | Boolean: 'Upper' in RIVER_PART | Upstream water availability |
| BASIN_YIELD_MEAN | Historical mean yield by basin | Basin productivity prior |
| BASIN_YIELD_STD | Historical std yield by basin | Basin yield variability |

### 3.5 Crop Encoding Features

| Feature | Computation | ML Value |
|---------|------------|---------|
| CROP_LABEL_ENC | LabelEncoder on 21 crops | Ordinal encoding |
| CROP_ONEHOT | One-hot: 21 binary columns | For linear models |
| CROP_EMBEDDING | Learned embedding (dim=16) | For neural models |
| CROP_PERENNIAL | Boolean: coconut/banana/teak/etc. | Perennial vs. annual |
| CROP_FOOD_GRAIN | Boolean: paddy/groundnut/gram | Food grain flag |
| CROP_COMMERCIAL | Boolean: sugarcane/cotton | Commercial crop flag |
| CROP_MEAN_YIELD | Historical yield by crop type | Crop productivity prior |
| CROP_MEAN_AREA | Historical area by crop type | Typical farm size |

### 3.6 Year / Trend Features

| Feature | Computation | ML Value |
|---------|------------|---------|
| YEAR_NORM | (YEAR − 2018) / 2 → [0,1] | Normalized year |
| YEAR_SIN | sin(2π×YEAR/3) | Cyclical multi-year pattern |
| EL_NINO_PROXY | Year-specific binary flag | Climate event |
| FARM_AGE | Current year − first year seen | Farm experience proxy |
| CONSECUTIVE_PADDY | Count of consecutive paddy seasons | Monoculture risk |

### 3.7 Cross-Feature Interactions

| Feature | Formula | ML Value |
|---------|---------|---------|
| AREA×YIELD | AREA × YIELD | Total farm production |
| SEASON×BASIN | Interaction of season + basin | Local agro-climatic context |
| YEAR×CROP | Interaction of year + crop | Inter-annual crop pattern |
| SOWING_EARLINESS | Expected sow date − actual sow date | Earliness vs. typical |
| GROWTH_EFFICIENCY | YIELD / SEASON_LENGTH | Yield per day |
| PADDY_INTENSITY | Paddy seasons / total seasons | Crop rotation intensity |

---

## 4. Satellite Fusion Features

### 4.1 Cross-Sensor Indices

| Feature | Formula | Sensors | ML Value |
|---------|---------|--------|---------|
| OPT_SAR_COHERENCE | Pearson(NDVI, VH) over season | S2 + S1 | Vegetation consistency |
| THERMAL_VEG_INDEX | LST × (1 − NDVI) | L8 + S2 | Water stress composite |
| S1_S2_FUSION | Concat(S1_features, S2_features) | S1 + S2 | Multi-modal input |
| CLOUD_GAP_FILL | Replace cloud-masked S2 with S1-predicted NDVI | S1 + S2 | Temporal gap filling |

### 4.2 Phenology Features (Multi-sensor)

| Feature | Method | ML Value |
|---------|--------|---------|
| TRANSPLANTING_SIGNAL | S1 VH spike + S2 NDWI high | Transplanting detection |
| HARVEST_SIGNAL | S1 VH drop + S2 NDVI drop | Harvest detection |
| FLOOD_TRANSPLANT | S1 VV < −18dB at transplanting time | Flooded paddy detection |
| SENESCENCE_SIGNAL | S2 B11 increase + NDVI decrease | Crop maturity signal |

---

## 5. Spatial Features

### 5.1 Farm Geometry

| Feature | Source | ML Value |
|---------|--------|---------|
| FARM_PERIMETER | Mask polygon | Boundary complexity |
| FARM_COMPACTNESS | Area / Perimeter² | Shape regularity |
| FARM_ORIENTATION | Principal axis angle | Irrigation row direction |
| CENTROID_LAT | Mask centroid | Latitude gradient |
| CENTROID_LON | Mask centroid | Longitude gradient |
| ELEVATION | SRTM/ALOS DEM (external) | Drainage, frost risk |

### 5.2 Neighborhood Features

| Feature | Computation | ML Value |
|---------|------------|---------|
| NEIGHBOR_CROP_MODE | Most common crop in 1km radius | Spatial autocorrelation |
| NEIGHBOR_HARVEST_MEAN | Mean harvest date in 1km radius | Harvest cluster timing |
| CANAL_DISTANCE | Distance to nearest canal (GIS) | Irrigation access |
| ROAD_DISTANCE | Distance to nearest road (GIS) | Market access |
| MANDI_DISTANCE | Distance to nearest APMC mandi | Market proximity |

---

## 6. Feature Priority Matrix for UZHAVAN AI

| Feature Category | Crop Type | Yield Forecast | Harvest Calendar | Sowing Advisory |
|-----------------|-----------|---------------|-----------------|----------------|
| NDVI time series | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ |
| S1 SAR features | ★★★★★ | ★★★★ | ★★★★ | ★★★ |
| L8 thermal (LST) | ★★★ | ★★★★ | ★★★ | ★★ |
| Season encoding | ★★★★ | ★★★★★ | ★★★★★ | ★★★★★ |
| River basin | ★★★★ | ★★★★ | ★★★ | ★★★★ |
| Area normalization | ★★ | ★★★★ | ★ | ★ |
| Year trend | ★★ | ★★★ | ★★ | ★★ |
| Phenology features | ★★★★ | ★★★★★ | ★★★★★ | ★★★★★ |
| SAR flood signal | ★★★ | ★★★ | ★★ | ★★★★ |
| Spatial neighborhood | ★★★ | ★★★ | ★★★★ | ★★★★ |

---

## 7. Suggested Feature Pipeline Code

```python
class SICKLEFeatureEngineer:
    """Complete feature engineering pipeline for SICKLE dataset."""
    
    def compute_ndvi_series(self, s2_npz_dir: str) -> dict:
        """Compute NDVI for all S2 acquisitions of one farm."""
        ndvi_series = {}
        for f in sorted(os.listdir(s2_npz_dir)):
            data = np.load(f'{s2_npz_dir}/{f}')
            nir, red = data['B8'], data['B4']
            ndvi = (nir - red) / (nir + red + 1e-8)
            date = f[:8]  # YYYYMMDD from filename
            ndvi_series[date] = ndvi.mean()
        return ndvi_series
    
    def temporal_features(self, ndvi_series: dict) -> dict:
        """Extract temporal statistics from NDVI series."""
        values = list(ndvi_series.values())
        return {
            'ndvi_mean': np.mean(values),
            'ndvi_max': np.max(values),
            'ndvi_min': np.min(values),
            'ndvi_std': np.std(values),
            'ndvi_range': np.max(values) - np.min(values),
            'ndvi_integral': np.trapz(values),
            'ndvi_peak_idx': int(np.argmax(values)),
        }
    
    def compute_spectral_indices(self, npz_path: str) -> dict:
        """Compute all spectral indices from a single S2 acquisition."""
        data = np.load(npz_path)
        b2, b3, b4 = data['B2'], data['B3'], data['B4']
        b8, b8a = data['B8'], data['B8A']
        b11, b12 = data['B11'], data['B12']
        
        def ratio(a, b): return (a - b) / (a + b + 1e-8)
        
        return {
            'ndvi': ratio(b8, b4).mean(),
            'evi2': (2.5 * (b8 - b4) / (b8 + 2.4 * b4 + 1)).mean(),
            'ndwi_leaf': ratio(b8a, b11).mean(),
            'ndwi_body': ratio(b3, b8).mean(),
            'ndre': ratio(b8a, data['B5']).mean(),
            'bsi': ((b11 + b4 - b8 - b2) / (b11 + b4 + b8 + b2 + 1e-8)).mean(),
            'swir_ratio': (b11 / (b12 + 1e-8)).mean(),
        }
    
    def tabular_features(self, row: dict) -> dict:
        """Engineer tabular features from a CSV row."""
        import math
        month = int(row['STANDARD_SEASON'].split('-')[0] in 
                    {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,
                     'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12})
        return {
            'log_area': math.log1p(row.get('AREA', 0)),
            'season_sin': math.sin(2 * math.pi * month / 12),
            'season_cos': math.cos(2 * math.pi * month / 12),
            'year_norm': (row.get('YEAR', 2018) - 2018) / 2,
            'is_coastal': 1 if 'Coastal' in str(row.get('RIVER_PART', '')) else 0,
            'is_paddy': 1 if row.get('PADDY_BIN', 2) == 1 else 0,
        }
```

---

## 8. Feature Selection Recommendations

### For Deep Learning Models (UNet3D, UTAE, ConvLSTM)
- Use raw satellite band stacks as input (the model learns features internally)
- Add positional encoding for acquisition dates (day-of-year)
- Optionally concatenate pre-computed NDVI, LSWI, RVI channels to raw bands

### For Traditional ML Models (XGBoost, Random Forest)
- Use temporal statistics: ndvi_mean, ndvi_max, ndvi_peak_doy, ndvi_integral
- Add tabular features: log_area, season_enc, basin_enc, year_norm
- Add phenology features: season_length, sowing_delay, grain_fill_period
- Use SHAP for post-hoc feature importance analysis

### Minimum Viable Feature Set for Yield Prediction
```python
YIELD_FEATURES = [
    'ndvi_integral',       # Total photosynthetic activity
    'ndvi_max',            # Peak biomass
    'ndvi_std',            # Variability (stress)
    's1_vh_max',           # Peak canopy density (cloud-free)
    'lst_mean_season',     # Temperature stress proxy
    'log_area',            # Farm size
    'season_sin',          # Season timing
    'season_cos',
    'basin_yield_mean',    # Historical baseline
    'year_norm',           # Trend
]
```

---

*End of Feature Engineering Report*  
*Report Version 1.0 — UZHAVAN AI Project — June 2026*
