# UZHAVAN AI — Test Report
**Date:** 2026-09-26 · **Version:** v1.0.0-alpha

---

## 1. Automated Tests

### Backend (pytest)
```
Platform: macOS 25.6.0 / Python 3.14 / pytest
Run: cd uzhavan_platform && .venv/bin/pytest tests/ -q
Result: 241 passed in 38.33 s
```

| Suite | File | Tests |
|-------|------|-------|
| Settings validation | `tests/api/test_settings.py` | 12 |
| Auth flow | `tests/api/test_auth_flow.py` | 18 |
| CORS + health | `tests/api/test_meta_cors.py` | 8 |
| Weather | `tests/api/test_weather.py` | 22 |
| Market | `tests/api/test_market.py` | 19 |
| Schemes | `tests/api/test_schemes.py` | 16 |
| Soil | `tests/api/test_soil.py` | 14 |
| Diary | `tests/api/test_diary.py` | 11 |
| Disease gate | `tests/api/test_disease_scan.py` | 9 |
| Satellite gate | `tests/api/test_satellite.py` | 6 |
| Phase integration A–F | `tests/integration/test_phase_*.py` | 106 |

### Flutter (flutter test)
```
Platform: macOS / Flutter 3.38.6 / Dart
Run: cd uzhavan_flutter && flutter test
Result: 144 passed, 0 failed (exit 0)
```

| Suite | File | Tests |
|-------|------|-------|
| App config / URL guard | `test/core/app_config_test.dart` | 12 |
| Token refresh | `test/core/token_refresh_test.dart` | 18 |
| Auth screens | `test/features/auth/auth_screen_test.dart` | 14 |
| Weather screen | `test/features/weather/weather_screen_test.dart` | 16 |
| Market screen | `test/features/market/market_screen_test.dart` | 19 |
| Schemes screen | `test/features/schemes/schemes_screen_test.dart` | 13 |
| Soil screen (C1/C2) | `test/features/soil/soil_screen_test.dart` | 17 |
| Live deviations | `test/features/live_deviations_test.dart` | 9 |
| Assistant screen | `test/features/assistant/assistant_screen_test.dart` | 26 |

---

## 2. Device QA — Pixel 6 Emulator (Android API 36)

**Date:** 2026-09-26  
**Backend:** QA instance on port 8010  
**APK:** Debug build with `API_BASE_URL=http://10.0.2.2:8010`

### Test Results

| # | Test | Result | Screenshot |
|---|------|--------|-----------|
| 1 | Fresh launch in Tamil → login screen | ✅ PASS | `01_fresh_launch_ta.png` |
| 2 | Wrong OTP → Tamil error message | ✅ PASS | `02_wrong_otp.png` |
| 3 | Correct OTP → home screen with real data | ✅ PASS | `03_home_after_login.png` |
| 4 | Home scrolled: market card + "பழைய தரவு" chip + attribution | ✅ PASS | `04_home_scrolled.png` |
| 5 | Market tab: commodity chips, real Agmarknet prices | ✅ PASS | `06_market.png` |
| 6 | Scan: crop picker (no paddy in list) | ✅ PASS | `08_crop_picker.png` |
| 7 | Gallery picker: own photo preview visible | ✅ PASS | `10_scan_preview.png` |
| 8 | Scan result: 503 → UNAVAILABLE state (disease gate) | ✅ PASS | `11_scan_result.png` |
| 9 | More menu: all 8 items visible | ✅ PASS | `12_more.png` / `18_more_menu.png` |
| 10 | Session persistence: app backgrounded → relaunch → home (no re-login) | ✅ PASS | `16_app_relaunch.png` |
| 11 | Weather full screen: IST dates, real temperature (28.2°C), attribution | ✅ PASS | `19_weather.png` |
| 12 | Schemes: 136 loaded, filter chips, Tamil search | ✅ PASS | `20_schemes.png` |
| 13 | Soil: C1 `category` key correct, sample counts, regional soil types | ✅ PASS | `21_soil.png` |
| 14 | Diary: auto-logged questions + scans present | ✅ PASS | `22_diary.png` |
| 15 | Satellite: under-validation state, all 4 gates shown | ✅ PASS | `23_satellite.png` |
| 16 | Profile: QA Farmer, Cuddalore, Tamil language | ✅ PASS | `24_profile.png` |
| 17 | Language switch Tamil → English: entire UI switches | ✅ PASS | `25_lang_switch_en.png` |
| 18 | Logout confirmation dialog | ✅ PASS | `26_after_logout.png` |
| 19 | Post-logout → login screen (language preference kept) | ✅ PASS | `27_logged_out.png` |
| 20 | Re-login after logout → home screen in English | ✅ PASS | `29_login_after_logout.png` |

### Observations
- Real weather data confirmed: 28.2°C Cuddalore (not the previously fabricated 30.0°C / 22.0°C defaults)
- IST date fix (D2) confirmed: forecast shows "சனி 2026-09-26" not UTC offset dates
- Disease gate enforced: 503 from backend, UNAVAILABLE state in Flutter, no ML service called
- Satellite gate enforced: `available:false`, no predictions or imagery shown
- Market for groundnut: real Agmarknet data from Cuddalore market

### Not QA'd on device (infrastructure limitations)
- Token refresh (requires waiting 15 min for access token expiry; tested via unit tests)
- Network failure states (no offline airplane mode test; tested via unit test mocks)
- Push notifications (not built)
- iOS build (not built)

---

## 3. Security Checks

| Check | Result |
|-------|--------|
| `tool/check_no_fabrication.sh` | ✅ 0 violations |
| No hardcoded OTPs | ✅ Confirmed (grep over codebase) |
| `.env` not in git | ✅ In `.gitignore` |
| JWT_SECRET: no placeholder in production | ✅ Settings module rejects at startup |
| Disease model approved flag | ✅ `DISEASE_MODEL_APPROVED=false` (default, never changed) |
| SICKLE data not served to farmers | ✅ Only `GET /api/satellite/status` → `available:false` |
| Stack traces never in API errors | ✅ Confirmed (all errors return `{code, message}`) |

---

## 4. Gate Status

### Disease Model Gates (FP-018)
| Gate | Status |
|------|--------|
| G1: 3 completed Colab seeds | ❌ NOT MET (Colab run not started) |
| G2: Independent eval on test split | ❌ NOT MET |
| G3: Cross-source macro-F1 ≥ 0.85 | ❌ NOT MET |
| G4: Per-disease recall ≥ 0.70 | ❌ NOT MET |
| G5: UNSURE threshold calibrated | ❌ NOT MET |

**Decision:** Disease scan returns 503 model_unavailable for all crops.

### Satellite Gates (FP-019)
| Gate | Status |
|------|--------|
| S1: SICKLE licence confirmed | ❌ BLOCKING |
| S3: Permitted farmer-facing use | ❌ BLOCKING |
| S7: Yield units confirmed | ❌ BLOCKING |
| S9: Processing parity measured | ❌ BLOCKING |
| S10: Independent evaluation passes ≤7d harvest gate | ❌ BLOCKING (8.12d fails) |

**Decision:** `GET /api/satellite/status` → `available:false, reason:"under_validation"`.
