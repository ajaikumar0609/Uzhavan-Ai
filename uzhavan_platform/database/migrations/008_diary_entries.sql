-- Migration 008: farmer diary (contract §8). question/scan rows are written automatically
-- by the /conversation and /api/disease/scan routes; clients POST note/observation/expense/income.
-- Idempotent.
BEGIN;

CREATE TABLE IF NOT EXISTS diary_entries (
    entry_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id   UUID NOT NULL REFERENCES farmers(farmer_id) ON DELETE CASCADE,
    farm_id     UUID REFERENCES farms(farm_id) ON DELETE SET NULL,
    kind        VARCHAR(20) NOT NULL
                CHECK (kind IN ('note', 'observation', 'expense', 'income', 'question', 'scan')),
    text        TEXT NOT NULL CHECK (char_length(text) BETWEEN 1 AND 1000),
    amount_inr  NUMERIC(12,2) CHECK (amount_inr IS NULL OR (amount_inr >= 0 AND amount_inr <= 100000000)),
    entry_date  DATE NOT NULL,
    ref         JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_diary_farmer_date ON diary_entries (farmer_id, entry_date DESC, created_at DESC);

COMMIT;
