-- Migration 003: Authentication tables for FP-001 (Farmer Auth)
-- OTP hashed with SHA-256, never stored in plaintext.
-- Rate limiting enforced at application layer using Redis;
-- this table provides audit trail and server-side expiry check.

CREATE TABLE IF NOT EXISTS otp_requests (
    id            SERIAL PRIMARY KEY,
    phone         VARCHAR(15)  NOT NULL,
    otp_hash      VARCHAR(64)  NOT NULL,    -- SHA-256 hex digest
    expires_at    TIMESTAMPTZ  NOT NULL,
    attempts      SMALLINT     NOT NULL DEFAULT 0,
    verified      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Index for the most common lookup: phone + not yet verified + not expired
CREATE INDEX IF NOT EXISTS idx_otp_phone_active
    ON otp_requests (phone, expires_at)
    WHERE verified = FALSE;

-- Purge trigger candidate: rows older than 24h can be deleted by a cron job.
-- No auto-delete here to keep the migration idempotent.

-- Refresh-token store (server-side revocation support)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_id      UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id     UUID         NOT NULL REFERENCES farmers(farmer_id) ON DELETE CASCADE,
    token_hash    VARCHAR(64)  NOT NULL UNIQUE,    -- SHA-256 of the raw refresh token
    issued_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    expires_at    TIMESTAMPTZ  NOT NULL,
    revoked       BOOLEAN      NOT NULL DEFAULT FALSE,
    user_agent    TEXT,
    ip_address    INET
);

CREATE INDEX IF NOT EXISTS idx_refresh_farmer
    ON refresh_tokens (farmer_id)
    WHERE revoked = FALSE;
