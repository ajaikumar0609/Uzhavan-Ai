# SICKLE Tabular Dataset — Deep Analysis Report

**File:** `sickle_dataset/sickle_dataset_tabular.csv`  
**Report Date:** June 30, 2026  
**Project:** UZHAVAN AI

---

## 1. Data Types

| Column | Raw Type | Semantic Type | Notes |
|--------|----------|--------------|-------|
| UNIQUE_ID | int64 | Nominal ID | Primary key; non-sequential (0–2,410) |
| PLOT_ID | float64 | Nominal ID | Float due to NaN presence; integer when valid |
| RIVER_PART | object | Categorical (5) | River sub-basin of Cauvery delta |
| STANDARD_SEASON | object | Categorical (7) | Growing window as "mmm-mmm" string |
| YEAR | float64 | Ordinal | 2018.0, 2019.0, 2020.0 |
| AREA | float64 | Continuous | Hectares; right-skewed |
| CROP | object | Categorical (21) | Target variable for crop classification |
| VARIETY | object | Categorical (19) | Paddy variety; mostly null |
| PADDY_BIN | float64 | Binary | 1 = paddy, 2 = non-paddy |
| SOWING_DATE | object | Date string | "YYYY-MM-DD" or "0" for non-paddy |
| TRANSPLANTING_DATE | object | Date string | "YYYY-MM-DD" or "0" for non-paddy |
| HARVESTING_DATE | object | Date string | "YYYY-MM-DD" or "0" |
| SOWING_DAY | float64 | Continuous | Days offset from season start |
| TRANSPLANTING_DAY | float64 | Continuous | Days offset from season start |
| HARVESTING_DAY | float64 | Continuous | Days offset from season start (0–184) |
| YIELD | float64 | Continuous | kg/ha; 0 for non-paddy |
| SPLIT | object | Categorical (3) | train / val / test |

---

## 2. Missing Values

| Column | Missing Count | Missing % | Action |
|--------|-------------|-----------|--------|
| VARIETY | 2,051 | 86.5% | Drop for general models; keep for paddy variety models |
| RIVER_PART | 525 | 22.2% | Impute with nearest neighbor or "Unknown" |
| PLOT_ID | 206 | 8.7% | These are padding rows — exclude from training |
| AREA | 206 | 8.7% | Same padding rows |
| CROP | 206 | 8.7% | Same padding rows |
| PADDY_BIN | 206 | 8.7% | Same padding rows |
| SOWING_DATE/DAY | 206 | 8.7% | Same padding rows |
| TRANSPLANTING_DATE/DAY | 206 | 8.7% | Same padding rows |
| HARVESTING_DATE/DAY | 206 | 8.7% | Same padding rows |
| YIELD | 206 | 8.7% | Same padding rows + zero for non-paddy |
| RIVER_PART (exc. padding) | 319 | — | 319 records with valid crops but unknown basin |
| All others | 0 | 0% | Complete |

**Effective dataset after removing 206 padding rows: 2,164 records.**

---

## 3. Duplicate Rows

- **Duplicate UNIQUE_ID:** 0 (primary key is unique)
- **Duplicate rows (all columns identical):** 0
- **Duplicate PLOT_ID × YEAR × SEASON combinations:** 0 (by design — one record per plot-season)
- **Same farm, multiple seasons:** Expected — farms appear across multiple seasonal windows

---

## 4. Unique Crop Names

```
1.  Paddy               2.  Banana
3.  Coconut             4.  Banyan
5.  Sugarcane           6.  Palm tree
7.  Groundnut           8.  Eucalyptus
9.  Tamarind tree       10. Mixed plantation
11. Cotton              12. Brinjal
13. Betelwine           14. Teak
15. Mixed               16. Bhendi
17. Sesame              18. Green gram
19. Blackgram           20. Black gram
21. Tomato
```

**Note:** "Blackgram" and "Black gram" are likely the same crop. Normalization required.

---

## 5. Crop Counts

| Rank | Crop | Count | Cumulative % |
|------|------|-------|-------------|
| 1 | Paddy | 907 | 41.9% |
| 2 | Banana | 499 | 64.9% |
| 3 | Coconut | 271 | 77.4% |
| 4 | Banyan | 180 | 85.7% |
| 5 | Sugarcane | 121 | 91.3% |
| 6 | Palm tree | 36 | 93.0% |
| 7 | Groundnut | 30 | 94.4% |
| 8 | Eucalyptus | 28 | 95.7% |
| 9 | Tamarind tree | 18 | 96.5% |
| 10 | Mixed plantation | 18 | 97.3% |
| 11 | Cotton | 14 | 97.9% |
| 12–21 | (10 minor crops) | 45 | 100% |

**Class imbalance ratio:** 907 (paddy) : 1 (tomato) = 907:1 — severe imbalance.

---

## 6. Yield Statistics

### All Records (including zero)

| Statistic | Value (kg/ha) |
|-----------|--------------|
| Count | 2,164 |
| Mean | 270.7 |
| Std Dev | 671.9 |
| Min | 0.0 |
| 25th percentile | 0.0 |
| Median | 0.0 |
| 75th percentile | 0.0 |
| Max | 3,840 |

### Paddy Records Only (non-zero yield)

| Statistic | Value (kg/ha) |
|-----------|--------------|
| Count | 319 |
| Mean | 1,836 |
| Std Dev | 433 |
| Min | 800 |
| 25th percentile | 1,620 |
| Median | 1,800 |
| 75th percentile | 2,040 |
| Max | 3,840 |

**Yield distribution:** Approximately normal for paddy (800–3,840 range), with most farms clustered 1,500–2,200 kg/ha.

**Reference:** Tamil Nadu state average paddy yield: ~2,900 kg/ha (irrigated). Dataset mean of 1,836 suggests smallholder, rain-fed, or stress-affected fields.

---

## 7. Farm Area Statistics

| Statistic | Value (ha) |
|-----------|-----------|
| Count | 2,164 |
| Mean | 0.351 ha |
| Std Dev | 0.469 ha |
| Min | 0.02 ha |
| 25th | 0.12 ha |
| Median | 0.19 ha |
| 75th | 0.38 ha |
| Max | 4.11 ha |

**Distribution:** Heavily right-skewed. 75% of farms are ≤ 0.38 ha.  
**Insight:** Sub-hectare smallholder farms dominate. This matches Tamil Nadu's land fragmentation patterns.

---

## 8. Seasons

| Season Code | Interpretation | Count |
|------------|---------------|-------|
| aug-jan | Samba season (Aug sow, Jan harvest) | 578 |
| jun-oct | Kuruvai early rice | 451 |
| sep-feb | Thaladi season | 417 |
| oct-mar | Rabi / winter | 315 |
| dec-may | Summer / dry season | 299 |
| may-sep | Kharif onset | 212 |
| apr-aug | Short summer rabi | 98 |

**Paddy Seasons:** Primarily aug-jan (Samba), jun-oct (Kuruvai), and sep-feb (Thaladi).

---

## 9. Years

| Year | Count | % of Total |
|------|-------|-----------|
| 2018 | 663 | 28.0% |
| 2019 | 848 | 35.8% |
| 2020 | 859 | 36.2% |

3 years of data across 3 growing seasons per year. Yearly growth in records suggests expanding ground truth collection effort.

---

## 10. River Basin Statistics

| Sub-basin | Count | % | Geographic Location |
|-----------|-------|---|-------------------|
| Upper Cauvery | 769 | 44.3% | Source region, Karnataka-TN border |
| Middle Vennar | 406 | 23.4% | Central delta distributary |
| Coastal Cauvery | 334 | 19.3% | Lower delta, near sea |
| Coastal Vennar | 179 | 10.3% | Eastern coastal distributary |
| Lower Cauvery | 157 | 9.1% | Southern terminal delta |

**Implication:** Upper Cauvery dominates. Models may be biased toward upper basin agro-ecology. Lower basin farms are underrepresented.

---

## 11. Correlation Matrix (Key Numeric Columns)

```
                 YEAR    AREA  SOWING_DAY  TRANSP_DAY  HARVEST_DAY   YIELD
YEAR            1.000   0.021      0.078       0.091       0.103    0.028
AREA            0.021   1.000     -0.032      -0.016      -0.018   -0.024
SOWING_DAY      0.078  -0.032      1.000       0.721       0.612    0.145
TRANSP_DAY      0.091  -0.016      0.721       1.000       0.624    0.124
HARVEST_DAY     0.103  -0.018      0.612       0.624       1.000    0.098
YIELD           0.028  -0.024      0.145       0.124       0.098    1.000
```

**Key Correlations:**
- SOWING_DAY ↔ TRANSPLANTING_DAY (r=0.72): Strong — earlier sowing leads to earlier transplanting
- SOWING_DAY ↔ HARVESTING_DAY (r=0.61): Strong — seasonal timing propagates through growth stages
- YIELD ↔ Day features (r~0.10–0.15): Weak direct linear correlation — suggests non-linear relationships
- AREA ↔ YIELD (r=-0.02): Near zero — farm size alone does not predict yield per ha

---

## 12. Key Distributions (Summary for Chart Generation)

### YIELD Distribution (Paddy non-zero)
- Shape: Approximately normal, slightly right-skewed
- Peak: 1,600–2,000 kg/ha
- Outlier threshold: >3,200 kg/ha (high-yield farms)

### AREA Distribution
- Shape: Right-skewed (log-normal)
- Log-transform recommended before ML

### SOWING_DAY Distribution
- Bimodal: cluster at 0–2 days (on-time sowing) and 10–20 days (late sowing)
- Many zeros: non-paddy crops padded with 0

### HARVESTING_DAY Distribution
- Trimodal: 0 (non-paddy), ~90 days (early harvest), ~144–184 days (late harvest)

---

## 13. Chart Descriptions (Generated as reference for dashboard)

| Chart | Type | X-axis | Y-axis | Insight |
|-------|------|--------|--------|---------|
| Crop Distribution | Horizontal Bar | Crop Name | Count | Paddy dominance |
| Yield Histogram | Histogram | YIELD (kg/ha) | Frequency | Approximately normal for paddy |
| Area Histogram | Histogram | AREA (ha) | Frequency | Right-skewed, log-normal |
| Seasonal Split | Pie | STANDARD_SEASON | % | aug-jan season dominant |
| River Basin Split | Pie | RIVER_PART | % | Upper Cauvery dominant |
| Year Distribution | Bar | YEAR | Count | Balanced 2018–2020 |
| Yield by Season | Box | Season | YIELD | Seasonal yield variability |
| Yield by Year | Box | YEAR | YIELD | Inter-year variability |
| Area by Crop | Box | CROP | AREA | Coconut largest, brinjal smallest |
| Harvest Day Hist | Histogram | HARVESTING_DAY | Frequency | Bimodal distribution |

---

## 14. Crop Frequency for ML

**Usable for classification (>10 samples):**
- Paddy (907), Banana (499), Coconut (271), Banyan (180), Sugarcane (121), Palm tree (36), Groundnut (30), Eucalyptus (28)

**Too rare for direct ML training (<20 samples):**
- Tamarind tree (18), Mixed plantation (18), Cotton (14), Brinjal (6), Betelwine (6), Teak (6), Mixed (6), Bhendi (4), Sesame (4), Green gram (4), Blackgram (3), Black gram (2), Tomato (1)

**Practical ML approach:**
1. Binary: Paddy vs. Non-paddy (reliable)
2. 5-class: Paddy / Banana / Coconut / Sugarcane / Other (moderate confidence)
3. 21-class: Experimental only, needs oversampling/focal loss

---

## 15. Feature Importance Suggestions

Based on domain knowledge and observed correlations:

| Feature | Expected Importance | Task |
|---------|--------------------|----|
| SOWING_DAY | HIGH | Yield, harvest prediction |
| TRANSPLANTING_DAY | HIGH | Yield, harvest prediction |
| STANDARD_SEASON | HIGH | All tasks |
| RIVER_PART | MEDIUM | Yield (soil/water context) |
| YEAR | MEDIUM | Trend modeling |
| AREA | LOW-MEDIUM | Yield normalization |
| CROP | N/A (target) | Classification tasks |
| PADDY_BIN | N/A (target) | Binary classification |
| VARIETY | LOW | Only for paddy deep-dives |

**Note:** The most powerful features are the satellite time-series arrays (not shown in this table), which carry far more information than any tabular column for spatial tasks.

---

## 16. Columns Useful for Machine Learning

### Input Features (X)
- `RIVER_PART` — Encode as one-hot or embedding (5 categories)
- `STANDARD_SEASON` — One-hot or cyclical sine/cosine encoding (7 categories)
- `YEAR` — Normalize to 0–1 or use as ordinal
- `AREA` — Log-transform then standardize
- `SOWING_DAY` — Standardize (for harvest prediction models)
- `TRANSPLANTING_DAY` — Standardize (for harvest/yield models)

### Target Variables (Y)
- `CROP` — Multi-class classification target (21 classes)
- `PADDY_BIN` — Binary classification target
- `YIELD` — Regression target (kg/ha)
- `HARVESTING_DAY` — Regression target (days)
- `SOWING_DAY` — Regression target (days)
- `TRANSPLANTING_DAY` — Regression target (days)

### Exclude
- `UNIQUE_ID` — Random identifier, no predictive value
- `PLOT_ID` — Use as grouping key only (not a feature)
- `VARIETY` — Too sparse (86.5% missing)
- `SOWING_DATE`, `TRANSPLANTING_DATE`, `HARVESTING_DATE` — Raw strings; use DAY versions
- `SPLIT` — Meta-column only

---

## 17. Columns Useful for UZHAVAN AI

| Column | UZHAVAN AI Module | Use Case |
|--------|------------------|---------|
| CROP | Crop Advisor, Dashboard | Display current crop, suggest next crop |
| YIELD | Yield Forecast, Market Price | Show yield vs. price opportunity |
| AREA | Input Advisor | Compute input quantities (fertilizer, seeds) |
| RIVER_PART | Water Management | Basin-specific irrigation advisory |
| STANDARD_SEASON | Calendar Module | Season-aware notifications |
| YEAR | Historical Dashboard | Year-over-year comparison |
| SOWING_DAY | Sowing Calendar | Optimal sowing date recommendation |
| TRANSPLANTING_DAY | Labor Planner | Transplanting crew scheduling |
| HARVESTING_DAY | Harvest Calendar | Harvest logistics, market planning |
| PADDY_BIN | Crop Detection | Confirms paddy presence from satellite |

---

## 18. Suggested Preprocessing Pipeline

```python
# Step 1: Remove padding rows
df = df.dropna(subset=['PLOT_ID'])  # Removes 206 padding rows

# Step 2: Fix crop name inconsistency  
df['CROP'] = df['CROP'].replace({'Black gram': 'Blackgram'})

# Step 3: Encode categoricals
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
df['SEASON_ENC'] = LabelEncoder().fit_transform(df['STANDARD_SEASON'])
df['BASIN_ENC'] = LabelEncoder().fit_transform(df['RIVER_PART'].fillna('Unknown'))
df['YEAR_NORM'] = (df['YEAR'] - 2018) / 2  # Normalize to 0-1

# Step 4: Log-transform area (right-skewed)
import numpy as np
df['LOG_AREA'] = np.log1p(df['AREA'])

# Step 5: Handle yield zeros (paddy-specific model)
paddy_df = df[(df['PADDY_BIN'] == 1) & (df['YIELD'] > 0)].copy()

# Step 6: Feature scaling for regression
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
numerical_cols = ['LOG_AREA', 'SOWING_DAY', 'TRANSPLANTING_DAY', 'YEAR_NORM']
paddy_df[numerical_cols] = scaler.fit_transform(paddy_df[numerical_cols])

# Step 7: Train/val/test split (use existing SPLIT column)
train_df = df[df['SPLIT'] == 'train']
val_df   = df[df['SPLIT'] == 'val']
test_df  = df[df['SPLIT'] == 'test']

# Step 8: Class weights for imbalanced classification
from sklearn.utils.class_weight import compute_class_weight
weights = compute_class_weight('balanced', classes=df['CROP'].unique(), y=df['CROP'])
```

---

*End of Tabular Dataset Deep Analysis*  
*Report Version 1.0 — UZHAVAN AI Project — June 2026*
