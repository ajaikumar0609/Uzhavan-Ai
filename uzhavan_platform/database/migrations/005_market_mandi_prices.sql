-- Migration 005: mandi_prices for the AGMARKNET snapshot (FP-011) + data_sources load records.
-- Idempotent. Does not modify earlier migrations. Existing columns of mandi_prices (001) are kept:
--   commodity, district (source spelling), market, price_date, min/max/modal_price_inr, arrivals_tonnes, source.
-- Added: district_id (meta id or NULL), market_type, variety, commodity_source_name, price_unit,
--   snapshot_date, source_file. Indexes for the /api/market queries.
BEGIN;

ALTER TABLE mandi_prices ADD COLUMN IF NOT EXISTS district_id           VARCHAR(50);
ALTER TABLE mandi_prices ADD COLUMN IF NOT EXISTS market_type           VARCHAR(30);
ALTER TABLE mandi_prices ADD COLUMN IF NOT EXISTS variety               VARCHAR(150);
ALTER TABLE mandi_prices ADD COLUMN IF NOT EXISTS commodity_source_name VARCHAR(150);
ALTER TABLE mandi_prices ADD COLUMN IF NOT EXISTS price_unit            VARCHAR(30);
ALTER TABLE mandi_prices ADD COLUMN IF NOT EXISTS snapshot_date         DATE;
ALTER TABLE mandi_prices ADD COLUMN IF NOT EXISTS source_file           VARCHAR(200);
ALTER TABLE mandi_prices ALTER COLUMN market TYPE VARCHAR(150);

CREATE INDEX IF NOT EXISTS idx_mandi_commodity_market_date ON mandi_prices (commodity, market, price_date DESC);
CREATE INDEX IF NOT EXISTS idx_mandi_commodity_date        ON mandi_prices (commodity, price_date DESC);
CREATE INDEX IF NOT EXISTS idx_mandi_district_id           ON mandi_prices (district_id);
CREATE INDEX IF NOT EXISTS idx_mandi_market                ON mandi_prices (market);

-- data_sources: record each file load (source, snapshot date, row count, sha256).
ALTER TABLE data_sources ADD COLUMN IF NOT EXISTS snapshot_date DATE;
ALTER TABLE data_sources ADD COLUMN IF NOT EXISTS row_count     BIGINT;
ALTER TABLE data_sources ADD COLUMN IF NOT EXISTS file_path     TEXT;
ALTER TABLE data_sources ADD COLUMN IF NOT EXISTS file_sha256   CHAR(64);
ALTER TABLE data_sources ADD COLUMN IF NOT EXISTS loaded_at     TIMESTAMPTZ;
CREATE UNIQUE INDEX IF NOT EXISTS uq_data_sources_name ON data_sources (name);

COMMIT;
