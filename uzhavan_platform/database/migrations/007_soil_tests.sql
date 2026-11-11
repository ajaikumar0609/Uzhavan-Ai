-- Migration 007: farmer-entered soil test results (FP-014, contract §7). kind = measured.
-- Range CHECKs mirror the API validation (backend/conversation/routes/soil.py). Idempotent.
BEGIN;

CREATE TABLE IF NOT EXISTS soil_tests (
    test_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id   UUID NOT NULL REFERENCES farmers(farmer_id) ON DELETE CASCADE,
    farm_id     UUID NOT NULL REFERENCES farms(farm_id) ON DELETE CASCADE,
    sample_date DATE NOT NULL,
    lab_name    VARCHAR(100),
    ph          NUMERIC(4,2)  CHECK (ph IS NULL OR (ph >= 0 AND ph <= 14)),
    ec_ds_m     NUMERIC(6,3)  CHECK (ec_ds_m IS NULL OR (ec_ds_m >= 0 AND ec_ds_m <= 20)),
    oc_pct      NUMERIC(5,2)  CHECK (oc_pct IS NULL OR (oc_pct >= 0 AND oc_pct <= 10)),
    n_kg_ha     NUMERIC(7,2)  CHECK (n_kg_ha IS NULL OR (n_kg_ha >= 0 AND n_kg_ha <= 2000)),
    p_kg_ha     NUMERIC(7,2)  CHECK (p_kg_ha IS NULL OR (p_kg_ha >= 0 AND p_kg_ha <= 500)),
    k_kg_ha     NUMERIC(7,2)  CHECK (k_kg_ha IS NULL OR (k_kg_ha >= 0 AND k_kg_ha <= 3000)),
    s_ppm       NUMERIC(7,2)  CHECK (s_ppm IS NULL OR (s_ppm >= 0 AND s_ppm <= 1000)),
    zn_ppm      NUMERIC(7,2)  CHECK (zn_ppm IS NULL OR (zn_ppm >= 0 AND zn_ppm <= 1000)),
    fe_ppm      NUMERIC(7,2)  CHECK (fe_ppm IS NULL OR (fe_ppm >= 0 AND fe_ppm <= 1000)),
    cu_ppm      NUMERIC(7,2)  CHECK (cu_ppm IS NULL OR (cu_ppm >= 0 AND cu_ppm <= 1000)),
    mn_ppm      NUMERIC(7,2)  CHECK (mn_ppm IS NULL OR (mn_ppm >= 0 AND mn_ppm <= 1000)),
    b_ppm       NUMERIC(7,2)  CHECK (b_ppm IS NULL OR (b_ppm >= 0 AND b_ppm <= 1000)),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_soil_tests_farm ON soil_tests (farm_id, sample_date DESC);
CREATE INDEX IF NOT EXISTS idx_soil_tests_farmer ON soil_tests (farmer_id);

COMMIT;
