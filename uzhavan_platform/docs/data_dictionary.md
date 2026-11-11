# UZHAVAN AI — Data Dictionary

## Reference Tables

### `crops`
| Column | Type | Description |
|--------|------|-------------|
| `crop_id` | SERIAL PK | Auto-increment ID |
| `english_name` | VARCHAR(100) UNIQUE | Standard English crop name |
| `tamil_name` | VARCHAR(100) | Tamil name (Unicode) |
| `scientific_name` | VARCHAR(150) | Binomial nomenclature |
| `category` | VARCHAR(50) | Cereal / Pulse / Oilseed / Fruit / Vegetable / Spice / Flower / Plantation / Fibre / Sugar / Fodder / Root Crop |
| `sub_category` | VARCHAR(50) | e.g. Minor Millet, Tree vegetable |
| `season_type` | VARCHAR(50) | Kharif / Rabi / Multiple seasons / Annual / Perennial |
| `duration_days_min` | INT | Minimum crop duration in days |
| `duration_days_max` | INT | Maximum crop duration in days |
| `water_requirement_mm` | INT | Seasonal water requirement in mm |
| `soil_ph_min` | DECIMAL(3,1) | Minimum suitable soil pH |
| `soil_ph_max` | DECIMAL(3,1) | Maximum suitable soil pH |
| `expected_yield_kg_ha` | INT | TNAU benchmark yield (kg/ha) |
| `source` | VARCHAR(50) | Data source tag |

---

### `diseases`
| Column | Type | Description |
|--------|------|-------------|
| `disease_id` | SERIAL PK | Auto-increment ID |
| `name` | VARCHAR(200) | Disease name in English |
| `tamil_name` | VARCHAR(200) | Tamil name |
| `pathogen_type` | VARCHAR(50) | Fungal / Bacterial / Viral / Insect / Nematode / Oomycete |
| `pathogen_name` | VARCHAR(200) | Scientific name of causal organism |
| `affected_crops` | TEXT[] | Array of affected crop names |
| `symptoms` | TEXT | Visual diagnostic description |
| `favorable_conditions` | TEXT | Environmental conditions promoting disease |
| `management_chemical` | TEXT | Recommended chemical control (molecule + dose) |
| `management_biological` | TEXT | Bioagent / biopesticide recommendations |
| `management_cultural` | TEXT | Agronomic / cultural control measures |
| `severity_level` | VARCHAR(20) | Low / Medium / High / Very High |

**GIN index** on `affected_crops[]` for fast `@>` crop lookups.
**GIN + trgm index** on `name` for fuzzy name search.

---

### `pests`
| Column | Type | Description |
|--------|------|-------------|
| `pest_id` | SERIAL PK | Auto-increment ID |
| `name` | VARCHAR(200) | Common name |
| `tamil_name` | VARCHAR(200) | Tamil name |
| `scientific_name` | VARCHAR(200) | Scientific name |
| `order_class` | VARCHAR(100) | Order: Family (e.g. Lepidoptera: Crambidae) |
| `affected_crops` | TEXT[] | Array of affected crop names |
| `damage_stage` | VARCHAR(100) | Life stage causing damage (Larval / Adult / Nymph) |
| `damage_symptoms` | TEXT | Visible damage description |
| `threshold_per_plant` | VARCHAR(50) | Economic Threshold Level (ETL) |
| `management_chemical` | TEXT | Chemical control |
| `management_biological` | TEXT | Biocontrol agents / parasitoids |
| `management_cultural` | TEXT | Cultural practices |

---

### `fertilizers`
| Column | Type | Description |
|--------|------|-------------|
| `fertilizer_id` | SERIAL PK | Auto-increment ID |
| `name` | VARCHAR(150) UNIQUE | Standard fertilizer name + grade |
| `tamil_name` | VARCHAR(150) | Tamil name |
| `type` | VARCHAR(50) | Chemical-N / NP / Potassic / Phosphatic / Complex NPK / Micronutrient / Soil Amendment / Organic / Biofertilizer |
| `n_percent` | DECIMAL(5,2) | Nitrogen content (%) |
| `p_percent` | DECIMAL(5,2) | Phosphorus (P2O5) content (%) |
| `k_percent` | DECIMAL(5,2) | Potassium (K2O) content (%) |
| `secondary_nutrients` | TEXT | Ca, S, Mg content or special notes |
| `form` | VARCHAR(50) | Granular / Liquid / Powder / Living plant |
| `application_method` | VARCHAR(100) | How to apply |
| `recommended_dose_kg_ha` | VARCHAR(50) | TNAU recommended dose |
| `cost_per_kg_inr` | DECIMAL(8,2) | Approximate market cost (INR/kg) |
| `notes` | TEXT | Special instructions or warnings |

---

### `soil_types`
| Column | Type | Description |
|--------|------|-------------|
| `soil_id` | SERIAL PK | Auto-increment ID |
| `name` | VARCHAR(100) | Soil classification name |
| `tamil_name` | VARCHAR(100) | Tamil name |
| `texture` | VARCHAR(50) | Sandy / Loamy / Clay / Sandy loam etc. |
| `ph_range_min` | DECIMAL(3,1) | Minimum pH |
| `ph_range_max` | DECIMAL(3,1) | Maximum pH |
| `water_holding_capacity` | VARCHAR(20) | Very Low / Low / Medium / High / Very High / Saturated |
| `drainage` | VARCHAR(20) | Excellent / Good / Moderate / Poor / Very Poor |
| `districts` | TEXT[] | Tamil Nadu districts where soil type is common |
| `suitable_crops` | TEXT[] | Crops well-suited to this soil |
| `management_tips` | TEXT | TNAU soil health recommendations |

---

### `district_profiles`
| Column | Type | Description |
|--------|------|-------------|
| `district_id` | SERIAL PK | Auto-increment ID |
| `name` | VARCHAR(100) UNIQUE | District name |
| `tamil_name` | VARCHAR(100) | Tamil name |
| `headquarters` | VARCHAR(100) | District HQ town |
| `agro_climatic_zone` | VARCHAR(100) | One of 7 TN agro-climatic zones |
| `area_sq_km` | INT | Geographic area |
| `avg_rainfall_mm` | INT | Average annual rainfall |
| `major_crops` | TEXT[] | Top crops by area |
| `major_soil_type` | VARCHAR(200) | Dominant soil types |
| `river_basin` | VARCHAR(200) | Major river basin |
| `groundwater_status` | VARCHAR(50) | Safe / Semi-critical / Critical / Over-exploited |
| `agriculture_area_pct` | INT | % of district area under agriculture |
| `notable_feature` | TEXT | Key agricultural/economic identity |
| `geom` | GEOMETRY(POINT, 4326) | PostGIS centroid lat/lon |

---

### `government_schemes`
| Column | Type | Description |
|--------|------|-------------|
| `scheme_id` | SERIAL PK | Auto-increment ID |
| `name` | VARCHAR(300) | Full scheme name |
| `tamil_name` | VARCHAR(300) | Tamil name |
| `ministry` | VARCHAR(200) | Implementing ministry |
| `type` | VARCHAR(100) | Income Support / Crop Insurance / Credit / Subsidy-Machinery / Irrigation etc. |
| `eligibility` | TEXT | Who can apply |
| `benefit` | TEXT | What the farmer gets |
| `application_mode` | VARCHAR(200) | Online portal / Bank branch / CSC / Agriculture office |
| `documents_required` | TEXT | Required documents |
| `deadline_type` | VARCHAR(100) | Rolling / Seasonal / Annual |
| `contact` | VARCHAR(200) | Helpline or office contact |

---

### `farm_machinery`
| Column | Type | Description |
|--------|------|-------------|
| `machinery_id` | SERIAL PK | Auto-increment ID |
| `name` | VARCHAR(200) | Equipment name |
| `tamil_name` | VARCHAR(200) | Tamil name |
| `category` | VARCHAR(100) | Tillage / Sowing / Weeding / Spraying / Harvesting / Post-Harvest / Irrigation |
| `power_source` | VARCHAR(50) | Manual / Animal / Tractor / Self-propelled / Electric / Battery |
| `suitable_crops` | TEXT[] | Crops this machine is used for |
| `suitable_soil` | VARCHAR(200) | Soil type suitability |
| `capacity_per_hour` | VARCHAR(100) | Work rate (ha/hr or kg/hr) |
| `cost_range_inr` | VARCHAR(100) | Market price range (INR) |
| `subsidy_available` | BOOLEAN | Whether government subsidy applies |
| `subsidy_scheme` | VARCHAR(200) | Scheme name (SMAM / PMKSY / State scheme) |
| `manufacturer_examples` | TEXT | Known brands / manufacturers |

---

## Farm Management Tables

### `farmers`
| Column | Type | Description |
|--------|------|-------------|
| `farmer_id` | UUID PK | UUID v4 |
| `name` | VARCHAR(200) | Full name |
| `phone` | VARCHAR(15) UNIQUE | Mobile number (for authentication + SMS) |
| `aadhaar_hash` | VARCHAR(64) | SHA-256 hash of Aadhaar — PII never stored raw |
| `district` | VARCHAR(100) | District |
| `taluk` | VARCHAR(100) | Taluk |
| `village` | VARCHAR(100) | Village |
| `preferred_language` | VARCHAR(20) | Tamil / English / Telugu |
| `kcc_holder` | BOOLEAN | Has active Kisan Credit Card |

### `farms`
| Column | Type | Description |
|--------|------|-------------|
| `farm_id` | UUID PK | UUID v4 |
| `farmer_id` | UUID FK | → farmers |
| `area_hectares` | DECIMAL(8,4) | Farm area |
| `survey_number` | VARCHAR(50) | Government survey number |
| `soil_type` | VARCHAR(100) | Dominant soil type |
| `irrigation_type` | VARCHAR(100) | Canal / Drip / Sprinkler / Rainfed / Well |
| `geom` | GEOMETRY(POLYGON,4326) | Farm boundary polygon (PostGIS) |

### `seasons`
| Column | Type | Description |
|--------|------|-------------|
| `season_id` | UUID PK | UUID v4 |
| `farm_id` | UUID FK | → farms |
| `crop_id` | INT FK | → crops |
| `fertilizer_applied` | JSONB | `{urea: 100, dap: 50, ...}` flexible record |
| `pesticide_applied` | JSONB | `{chlorpyrifos: {dose: "2mL/L", date: "..."}, ...}` |
| `status` | VARCHAR(20) | active / harvested / abandoned |

---

## AI / Satellite Tables

### `ai_predictions`
`prediction_type` enum: `crop_type` | `yield` | `harvest_date` | `sowing_date` | `transplant_date` | `growth_stage` | `disease`

### `knowledge_chunks`
RAG chunks from TNAU pages. Embedded by `advisory-rag` service.
Full-text search index on `content` via `to_tsvector('english', content)`.

---

## Naming Conventions
- Snake_case for all table and column names
- `_id` suffix for all primary and foreign keys
- `_at` suffix for all TIMESTAMPTZ columns
- `_pct` suffix for percentage values
- `_mm` suffix for millimetre measurements
- `_ha` suffix for hectare measurements
- `_inr` suffix for Indian Rupee amounts
- Arrays stored as PostgreSQL native `TEXT[]` with GIN indexes
- JSON flexibility via `JSONB` (binary JSON, queryable)
