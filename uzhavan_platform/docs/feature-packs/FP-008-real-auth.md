# FP-008: Real phone-OTP auth on the main app

**Status:** `COMPLETE` (backend, 2026-09-25). Evidence: the live dev-server flow (send → OTP read from the dev log → verify → refresh → reuse 401 → cooldown 429); `tests/api/test_auth_flow.py`, `tests/api/auth/*`, `tests/api/test_postgres_integration.py`; full pytest 145 passed.
**Sprint:** Sprint-006 · **Milestone:** M-06 · **Owner:** Backend Sub-Agent · **Depends on:** FP-007
**Contract:** `docs/architecture/API_CONTRACT_M06.md` §0 and §2

## 1. Overview
Auth used to be a separate service (`api/auth`) on different paths. It had a SHA-256 OTP hash with no server key, a `phone_hash` column that doesn't exist, and a second JWT library in `/conversation`. Now it's one reusable library (`backend/auth/`), mounted on the main app under `/api/auth/*`, with one JWT implementation.

## 2. Business Goal
A farmer signs in with their phone number and a one-time code, safely, on the same server that answers their questions.

## 3. User Story
As a farmer, I enter my mobile number, receive a 6-digit code and stay signed in, so that my profile and farms are mine alone.

## 4. Acceptance Criteria
- [x] `POST /api/auth/send-otp` → `{status, expires_in:300, resend_after:60}`; 400 `invalid_phone`; 429 `rate_limited` + `Retry-After` (60 s cooldown, max 3 per phone per hour, Redis); 503 `otp_delivery_not_configured` in production without an SMS provider (checked before an OTP is generated; nothing is logged).
- [x] OTP: 6 digits from `secrets`; stored as HMAC-SHA256(server key, `phone:otp`); 5-minute expiry; max 5 attempts (atomic `UPDATE … WHERE attempts < 5`). No universal or test OTP.
- [x] The OTP is logged only when `ENV=development` **and** `OTP_DEV_LOG=true`.
- [x] `POST /api/auth/verify-otp` → access + refresh tokens, `token_type`, `expires_in:900`, `is_new_farmer`, `profile_complete`; errors `otp_incorrect`, `otp_attempts_exceeded`, 410 `otp_expired`, 404 `otp_not_found`.
- [x] `POST /api/auth/refresh` rotates both tokens. Reusing a revoked token → 401, and all of that farmer's tokens are revoked.
- [x] `POST /api/auth/logout` 🔒 → 204 (revokes).
- [x] Access JWT HS256, 15 min, claims `sub, phone, iat, exp, typ:"access"` (+`jti`). The refresh token is opaque and stored as SHA-256, 30 days.
- [x] `/conversation` and `/api/disease/scan` accept the same access tokens (`backend/conversation/auth.py` → `backend/auth/tokens.py`).

## 5. UI Design
None (the Flutter client implements the screens against the contract).

## 6. API Contract
As in contract §2. Error body: `{"detail":{"code","message":{"en","ta":null}}}`. `ta` is null because no verified translations exist yet. The client localises by `code`.

## 7. Database Changes
`database/migrations/004_auth_profile_farms.sql` (idempotent): `refresh_tokens.revoked_at`; `farmers.name` is now nullable, plus `farmers.district_id`; `preferred_language` defaults to `'ta'`. Backup: `backups/uzhavan_dev_before_FP-008-009_20260925_165947.sql`.

## 8. AI Changes
None. The cognitive engine is unchanged.

## 9. Agent Responsibilities
Backend Sub-Agent: all of the above. Flutter Sub-Agent: screens and token storage. QA: device run.

## 10. Testing
`tests/api/auth/test_{otp,rate_limit,main}.py` (the 10 formerly erroring tests, adapted); `tests/api/test_auth_flow.py` covers the full flow, rotation, reuse revocation, logout, cooldown, hourly cap, production 503 with no log, the provider matrix and the shared JWT. `tests/api/test_postgres_integration.py` runs the real Postgres repository and cleans up after itself.

## 11. Security
Fail-closed OTP delivery; HMAC with a server key (`OTP_HMAC_KEY`, else derived from `JWT_SECRET`); constant-time compare; Redis down → 503 (no unlimited sends); refresh-token families revoked on reuse; there's no stack trace in any 500.

## 12. Performance
One Redis SET NX + INCR per send; a few indexed queries per verify. The DB pool is created lazily.

## 13. Documentation
`.env.example` (OTP_DEV_LOG, OTP_HMAC_KEY, SMS_PROVIDER, MSG91_*, TWILIO_*); this FP; CHANGELOG.

## 14. Demo Checklist
- [x] Dev: send-otp → OTP in the server log → verify → tokens
- [x] Resend within 60 s → 429
- [x] Refresh reuse → 401
- [x] `ENV=production` without SMS → 503 (test)

## 15. Release Notes
> **FP-008: Real sign-in.** Farmers sign in with their mobile number and a one-time code. Codes expire in 5 minutes, can be tried 5 times, and can be requested at most 3 times an hour. Sessions renew securely and end on logout. SMS delivery (MSG91/Twilio) has a place in the code but is not connected yet: production refuses to send codes until a provider is configured.

**Known gaps:** the MSG91/Twilio providers are stubs (no external call). `api/auth/main.py` is now a thin legacy app that serves the same routers.
