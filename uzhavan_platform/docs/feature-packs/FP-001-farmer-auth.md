# FP-001 — Farmer Authentication

**Status:** `PLANNING`
**Sprint:** Sprint-004
**Milestone:** M-04 — Authentication
**Owner:** TL Agent

---

## 1. Requirement
Tamil Nadu farmers need to log in to UZHAVAN AI using their mobile number (no email, no password). The system sends a 6-digit OTP via SMS. After verification, the farmer gets a JWT access token. On first login, the farmer registers their name, district, and primary crop. They can optionally add a farm (location, area, soil type).

---

## 2. User Story
```
As a Tamil Nadu farmer
I want to sign in with my mobile number and OTP
So that my farm profile and advisory history are saved and private
```

---

## 3. Acceptance Criteria

- [ ] AC-1: Given a valid 10-digit Indian phone number, when farmer taps "Send OTP", then SMS arrives within 30 seconds
- [ ] AC-2: Given a correct OTP entered within 5 minutes, when farmer taps "Verify", then JWT access token is returned
- [ ] AC-3: Given an expired or wrong OTP, when farmer taps "Verify", then Tamil error message shown: "தவறான OTP. மீண்டும் முயற்சிக்கவும்"
- [ ] AC-4: Given more than 3 OTP requests in 1 hour, when farmer tries again, then request is blocked with Tamil message
- [ ] AC-5: Given first login, when OTP verified, then farmer is directed to profile setup (name + district + primary crop)
- [ ] AC-6: Given farm created, when farmer views profile, then farm details visible with area in acres and hectares

**Out of Scope (v1):**
- Social login (Google/Facebook)
- Password-based login
- Multi-farm management (limit: 3 farms per farmer in v1)
- Aadhaar-based verification

---

## 4. API Contract
*SA Agent sign-off required*

```
POST /auth/send-otp
Body:    { "phone": "9876543210" }
Returns: { "status": "sent", "expires_in": 300 }
Errors:  400 (invalid phone), 429 (rate limited)

POST /auth/verify-otp
Body:    { "phone": "9876543210", "otp": "123456" }
Returns: { "access_token": "JWT", "is_new_farmer": true }
Errors:  400 (wrong OTP), 410 (expired OTP)

POST /farmers/profile
Auth:    Bearer JWT
Body:    { "name": "...", "district": "Thanjavur", "primary_crop": "Rice", "preferred_language": "Tamil" }
Returns: { "farmer_id": "UUID", "name": "..." }

POST /farms
Auth:    Bearer JWT
Body:    { "name": "...", "area_hectares": 1.8, "district": "...", "soil_type": "Alluvial", "irrigation_type": "Canal" }
Returns: { "farm_id": "UUID", ... }

GET /farmers/me
Auth:    Bearer JWT
Returns: { farmer profile + farms[] }
```

---

## 5. Database Changes

```
New tables:   otp_requests (phone, otp_hash, expires_at, attempts)
New columns:  none (farmers table already exists)
Migration:    003_auth_tables.sql
Notes:        OTP stored as SHA-256 hash, never plaintext
```

---

## 6. AI / RAG Changes
```
No AI changes in FP-001.
Farmer ID will be injected into advisory context in FP-002.
```

---

## 7. Flutter Screens
```
New screens:
  - PhoneInputScreen    (enter phone, request OTP)
  - OtpVerifyScreen     (6-digit OTP input)
  - ProfileSetupScreen  (name, district, primary crop)
  - FarmSetupScreen     (area, soil type, irrigation)

Navigation:
  App launch → check token → 
    valid: HomeScreen
    invalid/missing: PhoneInputScreen → OtpVerifyScreen → ProfileSetupScreen → HomeScreen
```

---

## 8. Tests
```
Unit tests:
  - test_otp_hash_matches()
  - test_jwt_expiry()
  - test_phone_validation()

Integration tests:
  - test_send_otp_success()
  - test_send_otp_rate_limit()
  - test_verify_otp_success()
  - test_verify_otp_expired()
  - test_verify_otp_wrong()
  - test_create_farmer_profile()
  - test_create_farm()

Coverage target: 80%
```

---

## 9. Security Review
```
Auth required:    JWT on /farmers/* and /farms/*
File upload:      No
SQL queries:      Parameterized — all OTP and farmer queries
Prompt injection: N/A (no LLM in auth flow)
OTP storage:      SHA-256 hash only
Rate limiting:    3 OTP requests/hour/phone (Redis counter)
JWT:              HS256, 15min access + 7day refresh
Verdict:          Pending Security Agent review
```

---

## 10. Documentation
```
README updated:    Yes (auth section)
API docs:          FastAPI /docs auto-generated
Data dictionary:   Yes (otp_requests table)
Changelog entry:   Yes
```

---

## 11. Demo Checklist
```
[ ] Farmer registers with phone (Tamil UI)
[ ] OTP arrives (mock in dev, real SMS in staging)
[ ] Farmer creates profile in Tamil
[ ] Farm added with location
[ ] Login survives app restart (token persisted)
[ ] Wrong OTP shows Tamil error
[ ] Rate limit works (4th OTP request blocked)
[ ] "Murugan test": Murugan (42, Thanjavur) completes registration in < 2 minutes
```

---

## 12. Release Notes
```
## FP-001 — Farmer Login (v0.4.0)

What farmers can now do:
- Sign in securely with your mobile number — no password needed
- Create your farm profile in Tamil
- Your advisory history is now saved

How to use:
- Open UZHAVAN AI → Enter your 10-digit mobile number → Enter the OTP → Done
```

---

## Sign-offs

| Agent | Sign-off | Date |
|-------|----------|------|
| PM Agent | [ ] | |
| SA Agent | [ ] | |
| Testing Agent | [ ] | |
| Security Agent | [ ] | |
| Documentation Agent | [ ] | |
| Standards Agent | [ ] | |
| **Master Agent** | [ ] | |
