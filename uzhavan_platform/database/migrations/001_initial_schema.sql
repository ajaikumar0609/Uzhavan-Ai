-- ============================================================
-- UZHAVAN AI — Agricultural Data Platform
-- Migration 001: Initial Schema
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- fuzzy name search

-- ============================================================
-- REFERENCE TABLES
-- ============================================================

CREATE TABLE crops (
    crop_id         SERIAL PRIMARY KEY,
    english_name    VARCHAR(100) NOT NULL UNIQUE,
    tamil_name      VARCHAR(100),
    scientific_name VARCHAR(150),
    category        VARCHAR(50),      -- Cereal, Pulse, Oilseed, Fruit, etc.
    sub_category    VARCHAR(50),
    season_type     VARCHAR(50),
    duration_days_min   INT,
    duration_days_max   INT,
    water_requirement_mm INT,
    soil_ph_min     DECIMAL(3,1),
    soil_ph_max     DECIMAL(3,1),
    expected_yield_kg_ha INT,
    source          VARCHAR(50) DEFAULT 'TNAU',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_crops_english ON crops USING gin(english_name gin_trgm_ops);
CREATE INDEX idx_crops_tamil   ON crops USING gin(tamil_name gin_trgm_ops);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE fertilizers (
    fertilizer_id   SERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL UNIQUE,
    tamil_name      VARCHAR(150),
    type            VARCHAR(50),      -- Chemical-N, Organic, Biofertilizer, etc.
    n_percent       DECIMAL(5,2) DEFAULT 0,
    p_percent       DECIMAL(5,2) DEFAULT 0,
    k_percent       DECIMAL(5,2) DEFAULT 0,
    secondary_nutrients TEXT,
    form            VARCHAR(50),      -- Granular, Liquid, Powder
    application_method VARCHAR(100),
    recommended_dose_kg_ha VARCHAR(50),
    cost_per_kg_inr DECIMAL(8,2),
    notes           TEXT,
    source          VARCHAR(50) DEFAULT 'TNAU',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE diseases (
    disease_id      SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    tamil_name      VARCHAR(200),
    pathogen_type   VARCHAR(50),      -- Fungal, Bacterial, Viral, Insect, Nematode
    pathogen_name   VARCHAR(200),
    affected_crops  TEXT[],           -- Array of crop names
    symptoms        TEXT,
    favorable_conditions TEXT,
    management_chemical TEXT,
    management_biological TEXT,
    management_cultural TEXT,
    severity_level  VARCHAR(20) CHECK (severity_level IN ('Low','Medium','High','Very High')),
    source          VARCHAR(50) DEFAULT 'TNAU',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_diseases_crops ON diseases USING gin(affected_crops);
CREATE INDEX idx_diseases_name  ON diseases USING gin(name gin_trgm_ops);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE pests (
    pest_id         SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    tamil_name      VARCHAR(200),
    scientific_name VARCHAR(200),
    order_class     VARCHAR(100),     -- Lepidoptera, Hemiptera, etc.
    affected_crops  TEXT[],
    damage_stage    VARCHAR(100),     -- Larval, Adult, Nymph
    damage_symptoms TEXT,
    threshold_per_plant VARCHAR(50),
    management_chemical TEXT,
    management_biological TEXT,
    management_cultural TEXT,
    source          VARCHAR(50) DEFAULT 'TNAU',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE crop_calendar (
    calendar_id     SERIAL PRIMARY KEY,
    crop_id         INT REFERENCES crops(crop_id),
    season_name     VARCHAR(50) NOT NULL,
    tamil_season    VARCHAR(50),
    sowing_month_start VARCHAR(20),
    sowing_month_end   VARCHAR(20),
    harvest_month_start VARCHAR(20),
    harvest_month_end   VARCHAR(20),
    duration_days   VARCHAR(20),
    zone            VARCHAR(100),
    districts       TEXT[],
    method          VARCHAR(50),      -- Transplanted, Direct, Drip, etc.
    key_varieties   TEXT[],
    water_source    VARCHAR(100),
    remarks         TEXT,
    source          VARCHAR(50) DEFAULT 'TNAU',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_calendar_crop    ON crop_calendar(crop_id);
CREATE INDEX idx_calendar_season  ON crop_calendar(season_name);
CREATE INDEX idx_calendar_district ON crop_calendar USING gin(districts);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE soil_types (
    soil_id         SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    tamil_name      VARCHAR(100),
    texture         VARCHAR(50),
    ph_range_min    DECIMAL(3,1),
    ph_range_max    DECIMAL(3,1),
    water_holding_capacity VARCHAR(20),
    drainage        VARCHAR(20),
    districts       TEXT[],
    suitable_crops  TEXT[],
    management_tips TEXT,
    source          VARCHAR(50) DEFAULT 'TNAU',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE government_schemes (
    scheme_id       SERIAL PRIMARY KEY,
    name            VARCHAR(300) NOT NULL,
    tamil_name      VARCHAR(300),
    ministry        VARCHAR(200),
    type            VARCHAR(100),
    eligibility     TEXT,
    benefit         TEXT,
    application_mode VARCHAR(200),
    documents_required TEXT,
    deadline_type   VARCHAR(100),
    contact         VARCHAR(200),
    source          VARCHAR(50) DEFAULT 'GOI/TN',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE district_profiles (
    district_id     SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    tamil_name      VARCHAR(100),
    headquarters    VARCHAR(100),
    agro_climatic_zone VARCHAR(100),
    area_sq_km      INT,
    avg_rainfall_mm INT,
    major_crops     TEXT[],
    major_soil_type VARCHAR(200),
    river_basin     VARCHAR(200),
    groundwater_status VARCHAR(50),  -- Safe, Semi-critical, Critical, Over-exploited
    agriculture_area_pct INT,
    notable_feature TEXT,
    geom            GEOMETRY(POINT, 4326),  -- PostGIS lat/lon centroid
    source          VARCHAR(50) DEFAULT 'TN Agri Dept',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_district_geom ON district_profiles USING gist(geom);
CREATE INDEX idx_district_crops ON district_profiles USING gin(major_crops);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE farm_machinery (
    machinery_id    SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    tamil_name      VARCHAR(200),
    category        VARCHAR(100),     -- Tillage, Sowing, Harvesting, Spraying, etc.
    power_source    VARCHAR(50),      -- Manual, Animal, Tractor, Self-propelled
    suitable_crops  TEXT[],
    suitable_soil   VARCHAR(200),
    capacity_per_hour VARCHAR(100),
    cost_range_inr  VARCHAR(100),
    subsidy_available BOOLEAN DEFAULT TRUE,
    subsidy_scheme  VARCHAR(200),
    manufacturer_examples TEXT,
    source          VARCHAR(50) DEFAULT 'TNAU',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- FARM MANAGEMENT TABLES
-- ============================================================

CREATE TABLE farmers (
    farmer_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(200) NOT NULL,
    phone           VARCHAR(15) UNIQUE,
    aadhaar_hash    VARCHAR(64),      -- SHA-256 hashed, never store raw
    district        VARCHAR(100),
    taluk           VARCHAR(100),
    village         VARCHAR(100),
    preferred_language VARCHAR(20) DEFAULT 'Tamil',
    kcc_holder      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_farmers_district ON farmers(district);
CREATE INDEX idx_farmers_phone    ON farmers(phone);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE farms (
    farm_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id       UUID REFERENCES farmers(farmer_id),
    name            VARCHAR(200),
    area_hectares   DECIMAL(8,4),
    district        VARCHAR(100),
    taluk           VARCHAR(100),
    village         VARCHAR(100),
    survey_number   VARCHAR(50),
    soil_type       VARCHAR(100),
    irrigation_type VARCHAR(100),
    water_source    VARCHAR(100),
    geom            GEOMETRY(POLYGON, 4326),  -- Farm boundary polygon
    elevation_m     INT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_farms_farmer  ON farms(farmer_id);
CREATE INDEX idx_farms_geom    ON farms USING gist(geom);
CREATE INDEX idx_farms_district ON farms(district);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE seasons (
    season_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id         UUID REFERENCES farms(farm_id),
    crop_id         INT REFERENCES crops(crop_id),
    season_name     VARCHAR(50),
    variety         VARCHAR(100),
    sowing_date     DATE,
    transplant_date DATE,
    expected_harvest_date DATE,
    actual_harvest_date DATE,
    area_sown_ha    DECIMAL(8,4),
    seed_rate_kg_ha DECIMAL(8,2),
    irrigation_count INT DEFAULT 0,
    fertilizer_applied JSONB,   -- {urea: 100, dap: 50, ...}
    pesticide_applied  JSONB,
    expected_yield_kg_ha INT,
    actual_yield_kg_ha   INT,
    selling_price_per_kg DECIMAL(8,2),
    total_cost_inr  DECIMAL(12,2),
    notes           TEXT,
    status          VARCHAR(20) DEFAULT 'active', -- active, harvested, abandoned
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_seasons_farm   ON seasons(farm_id);
CREATE INDEX idx_seasons_crop   ON seasons(crop_id);
CREATE INDEX idx_seasons_status ON seasons(status);

-- ============================================================
-- SATELLITE & AI TABLES
-- ============================================================

CREATE TABLE satellite_acquisitions (
    acq_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id         UUID REFERENCES farms(farm_id),
    sensor          VARCHAR(10) CHECK (sensor IN ('S2','S1','L8')),
    acquisition_date DATE NOT NULL,
    cloud_cover_pct INT,
    scene_id        VARCHAR(100),
    tile_path       TEXT,             -- S3/GCS path to NPZ file
    bands           TEXT[],
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sat_farm ON satellite_acquisitions(farm_id);
CREATE INDEX idx_sat_date ON satellite_acquisitions(acquisition_date);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE ndvi_timeseries (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id         UUID REFERENCES farms(farm_id),
    season_id       UUID REFERENCES seasons(season_id),
    date            DATE NOT NULL,
    ndvi_mean       DECIMAL(5,4),
    ndvi_std        DECIMAL(5,4),
    evi_mean        DECIMAL(5,4),
    lswi_mean       DECIMAL(5,4),
    ndwi_mean       DECIMAL(5,4),
    source_sensor   VARCHAR(10),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ndvi_farm   ON ndvi_timeseries(farm_id);
CREATE INDEX idx_ndvi_date   ON ndvi_timeseries(date);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE ai_predictions (
    prediction_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id         UUID REFERENCES farms(farm_id),
    season_id       UUID REFERENCES seasons(season_id),
    prediction_type VARCHAR(50) CHECK (prediction_type IN (
        'crop_type', 'yield', 'harvest_date', 'sowing_date',
        'transplant_date', 'growth_stage', 'disease'
    )),
    model_name      VARCHAR(100),
    model_version   VARCHAR(20),
    predicted_value TEXT,
    confidence      DECIMAL(5,4),
    top_k           JSONB,
    input_features  JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_farm    ON ai_predictions(farm_id);
CREATE INDEX idx_predictions_type    ON ai_predictions(prediction_type);
CREATE INDEX idx_predictions_created ON ai_predictions(created_at DESC);

-- ============================================================
-- RAG & ADVISORY TABLES
-- ============================================================

CREATE TABLE knowledge_chunks (
    chunk_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_url      TEXT,
    source_file     TEXT,
    title           VARCHAR(500),
    content         TEXT NOT NULL,
    content_md      TEXT,
    category        VARCHAR(100),
    crop            VARCHAR(100),
    language        VARCHAR(20) DEFAULT 'English',
    chunk_index     INT DEFAULT 0,
    word_count      INT,
    embedding_model VARCHAR(50),
    embedded_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chunks_crop     ON knowledge_chunks(crop);
CREATE INDEX idx_chunks_category ON knowledge_chunks(category);
CREATE INDEX idx_chunks_content  ON knowledge_chunks USING gin(to_tsvector('english', content));

-- ─────────────────────────────────────────────────────────────

CREATE TABLE chat_sessions (
    session_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id       UUID REFERENCES farmers(farmer_id),
    language        VARCHAR(20) DEFAULT 'Tamil',
    channel         VARCHAR(20) DEFAULT 'app', -- app, whatsapp, sms, ivr
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    last_active     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_messages (
    message_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES chat_sessions(session_id),
    role            VARCHAR(10) CHECK (role IN ('user','assistant','system')),
    content         TEXT NOT NULL,
    tools_used      TEXT[],           -- ['rag', 'weather', 'market', 'satellite']
    sources_cited   TEXT[],
    latency_ms      INT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON chat_messages(session_id);
CREATE INDEX idx_messages_created ON chat_messages(created_at DESC);

-- ============================================================
-- MARKET & WEATHER CACHE
-- ============================================================

CREATE TABLE mandi_prices (
    price_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commodity       VARCHAR(100) NOT NULL,
    district        VARCHAR(100),
    market          VARCHAR(100),
    price_date      DATE NOT NULL,
    min_price_inr   DECIMAL(10,2),
    max_price_inr   DECIMAL(10,2),
    modal_price_inr DECIMAL(10,2),
    arrivals_tonnes DECIMAL(10,2),
    source          VARCHAR(50) DEFAULT 'AGMARKNET',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mandi_commodity ON mandi_prices(commodity);
CREATE INDEX idx_mandi_date      ON mandi_prices(price_date DESC);
CREATE INDEX idx_mandi_district  ON mandi_prices(district);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE weather_cache (
    weather_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district        VARCHAR(100) NOT NULL,
    forecast_date   DATE NOT NULL,
    temp_max_c      DECIMAL(5,2),
    temp_min_c      DECIMAL(5,2),
    rainfall_mm     DECIMAL(8,2),
    humidity_pct    INT,
    wind_speed_kmh  DECIMAL(6,2),
    condition       VARCHAR(100),
    source          VARCHAR(50) DEFAULT 'Open-Meteo',
    fetched_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (district, forecast_date)
);

CREATE INDEX idx_weather_district ON weather_cache(district);
CREATE INDEX idx_weather_date     ON weather_cache(forecast_date DESC);

-- ============================================================
-- AUDIT / METADATA
-- ============================================================

CREATE TABLE data_sources (
    source_id       SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    url             TEXT,
    type            VARCHAR(50),      -- Portal, API, Dataset, PDF
    last_crawled    TIMESTAMPTZ,
    crawl_frequency VARCHAR(50),
    total_documents INT DEFAULT 0,
    notes           TEXT
);

INSERT INTO data_sources (name, url, type, notes) VALUES
  ('TNAU Agritech Portal', 'https://agritech.tnau.ac.in', 'Portal', '368 HTML pages + 1240 PDFs crawled'),
  ('SICKLE Dataset', 'https://github.com/sickle-dataset', 'Dataset', '2164 farm records, 3 satellites'),
  ('AGMARKNET', 'https://agmarknet.gov.in', 'API', 'Daily mandi prices'),
  ('Open-Meteo', 'https://open-meteo.com', 'API', 'Free weather forecast API'),
  ('API Setu', 'https://api.data.gov.in', 'API', 'Government data APIs'),
  ('OpenStreetMap', 'https://www.openstreetmap.org', 'API', 'Farm boundary geocoding');
