-- Migration 004: real auth + farmer profile + farms without PostGIS (FP-008, FP-009)
-- Idempotent: safe to run more than once. Does not modify earlier migrations.
-- Backup taken before first apply: backups/uzhavan_dev_before_FP-008-009_<ts>.sql
--
-- 1. farmers: a new farmer has no name after OTP verification -> name becomes nullable.
--    Adds district_id (id from /api/meta/districts). Existing columns are kept.
--    preferred_language now stores 'ta' | 'en' (legacy 'Tamil'/'English' mapped on read).
-- 2. refresh_tokens: revoked_at for rotation / reuse-detection audit.
-- 3. farms: lat/lon DOUBLE PRECISION with Tamil Nadu bbox CHECKs, optional boundary_geojson.
--    If an older PostGIS-based farms table exists (001), the new columns are added to it.

BEGIN;

-- ── 1. farmers ────────────────────────────────────────────────────────────────
ALTER TABLE farmers ALTER COLUMN name DROP NOT NULL;
ALTER TABLE farmers ADD COLUMN IF NOT EXISTS district_id VARCHAR(50);
ALTER TABLE farmers ALTER COLUMN preferred_language SET DEFAULT 'ta';

-- ── 2. refresh_tokens ─────────────────────────────────────────────────────────
ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ;

-- ── 3. farms ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS farms (
    farm_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id           UUID NOT NULL REFERENCES farmers(farmer_id) ON DELETE CASCADE,
    name                VARCHAR(100) NOT NULL,
    district_id         VARCHAR(50)  NOT NULL,
    village             VARCHAR(100),
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    boundary_geojson    JSONB,
    area_ha             DOUBLE PRECISION,
    crop_id             VARCHAR(50),
    crop_stage_id       VARCHAR(50),
    season_id           VARCHAR(50),
    irrigation_type_id  VARCHAR(50),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Columns added when an older farms table already existed (no-ops on a fresh create).
ALTER TABLE farms ADD COLUMN IF NOT EXISTS district_id        VARCHAR(50);
ALTER TABLE farms ADD COLUMN IF NOT EXISTS village            VARCHAR(100);
ALTER TABLE farms ADD COLUMN IF NOT EXISTS latitude           DOUBLE PRECISION;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS longitude          DOUBLE PRECISION;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS boundary_geojson   JSONB;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS area_ha            DOUBLE PRECISION;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS crop_id            VARCHAR(50);
ALTER TABLE farms ADD COLUMN IF NOT EXISTS crop_stage_id      VARCHAR(50);
ALTER TABLE farms ADD COLUMN IF NOT EXISTS season_id          VARCHAR(50);
ALTER TABLE farms ADD COLUMN IF NOT EXISTS irrigation_type_id VARCHAR(50);
ALTER TABLE farms ADD COLUMN IF NOT EXISTS created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE farms ADD COLUMN IF NOT EXISTS updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW();

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'farms_latitude_tn_bbox') THEN
        ALTER TABLE farms ADD CONSTRAINT farms_latitude_tn_bbox
            CHECK (latitude IS NULL OR (latitude >= 8.0 AND latitude <= 13.6));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'farms_longitude_tn_bbox') THEN
        ALTER TABLE farms ADD CONSTRAINT farms_longitude_tn_bbox
            CHECK (longitude IS NULL OR (longitude >= 76.2 AND longitude <= 80.4));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'farms_latlon_pair') THEN
        ALTER TABLE farms ADD CONSTRAINT farms_latlon_pair
            CHECK ((latitude IS NULL) = (longitude IS NULL));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'farms_area_ha_positive') THEN
        ALTER TABLE farms ADD CONSTRAINT farms_area_ha_positive
            CHECK (area_ha IS NULL OR (area_ha > 0 AND area_ha <= 10000));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_farms_farmer_id ON farms (farmer_id);

COMMIT;
