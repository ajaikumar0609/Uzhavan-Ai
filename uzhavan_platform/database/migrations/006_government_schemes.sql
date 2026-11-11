-- Migration 006: extend government_schemes for the 136-record scheme catalogue (FP-012).
-- Choice: EXTEND the existing (empty) 001 table rather than add a new one, so there is one
-- scheme table. The public id is the new `scheme_key` (e.g. central_pm_kisan); the SERIAL
-- scheme_id stays as the internal PK. Reused 001 columns: name, tamil_name, eligibility,
-- benefit (= source "benefits"), documents_required (= source "required_documents").
-- Idempotent.
BEGIN;

ALTER TABLE government_schemes ALTER COLUMN name TYPE TEXT;
ALTER TABLE government_schemes ALTER COLUMN tamil_name TYPE TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS scheme_key             VARCHAR(80);
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS authority              TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS level                  VARCHAR(10);
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS state                  VARCHAR(50);
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS active                 BOOLEAN;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS crops                  TEXT[];
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS crop_applicability     TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS description            TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS description_ta         TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS eligibility_ta         TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS application_method     TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS required_documents_ta  TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS official_url           TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS source_documents       JSONB;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS date_checked           DATE;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS last_updated_on_source TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS source_catalogue       TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS source_go_file         TEXT;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS components             JSONB;
ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS updated_at             TIMESTAMPTZ DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_government_schemes_scheme_key ON government_schemes (scheme_key);
CREATE INDEX IF NOT EXISTS idx_government_schemes_level ON government_schemes (level);
CREATE INDEX IF NOT EXISTS idx_government_schemes_crops ON government_schemes USING GIN (crops);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'government_schemes_level_check') THEN
        ALTER TABLE government_schemes ADD CONSTRAINT government_schemes_level_check
            CHECK (level IS NULL OR level IN ('central', 'state'));
    END IF;
END $$;

COMMIT;
