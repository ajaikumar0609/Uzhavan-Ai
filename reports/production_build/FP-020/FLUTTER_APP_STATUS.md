# UZHAVAN AI — Flutter App Status
**Date:** 2026-09-26 · **Flutter SDK:** 3.38.6 · **App ID:** `ai.uzhavan.uzhavan`

---

## Build Artefacts

| Artefact | Path | Size | Target |
|----------|------|------|--------|
| Release APK | `build/app/outputs/flutter-apk/app-release.apk` | 57.8 MB | Direct install / side-load |
| Release AAB | `build/app/outputs/bundle/release/app-release.aab` | 45.7 MB | Google Play Store |
| QA Debug APK | `build/app/outputs/flutter-apk/app-debug.apk` | — | `API_BASE_URL=http://10.0.2.2:8010` |

All release builds compiled with `--dart-define=API_BASE_URL=https://api.uzhavan.ai`.

---

## Screen Inventory

| Screen | Route | QA Status |
|--------|-------|-----------|
| Login (phone) | `/login` | ✅ Verified |
| OTP verify | `/otp` | ✅ Verified (wrong OTP Tamil error + resend countdown) |
| Onboarding profile | `/onboarding/profile` | ✅ Verified |
| Home | `/home` | ✅ Real data (weather + market + diary) |
| Assistant | `/assistant` | ✅ SSE stream, fallback + ungrounded warning |
| Scan | `/scan` | ✅ Crop picker (no paddy), 503 model_unavailable |
| Market | `/market` | ✅ Real Agmarknet prices, stale chip |
| More menu | `/more` | ✅ All 8 items |
| Weather | `/more/weather` | ✅ IST dates, 7-day forecast |
| Schemes | `/more/schemes` | ✅ 136 schemes, filter, detail |
| Soil | `/more/soil` | ✅ C1+C2 fixes, add test form |
| Farm diary | `/more/diary` | ✅ Auto-logged questions + scans |
| Satellite | `/more/satellite` | ✅ Under-validation state + gates |
| My farms | `/more/farms` | ✅ CRUD, TN bbox, acres→hectares |
| Profile | `/more/profile` | ✅ View + edit |
| Settings | `/more/settings` | ✅ Language, theme, about |

---

## Key Features

### Localisation
- Default language: Tamil (`ta-IN`)
- 133 ARB keys covering all screens and all 23 error codes  
- Language switch (top-right on every screen) switches instantly  
- Language preference persisted in secure storage across logout/relaunch  
- Font: Roboto (Latin) + Noto Sans Tamil fallback (F2 fix)  
- Nav label overflow fixed with ellipsis (F1 fix)  

### Security
- Tokens in `flutter_secure_storage` (Android Keystore-backed)  
- Single-flight JWT refresh (concurrent requests serialised)  
- Production build rejects `http://` API URLs (requires `https://` or `ALLOW_INSECURE_API=true`)  

### Data integrity
- `tool/check_no_fabrication.sh`: blocks 14 known fabricated strings at build time  
- All data states: loading / success / empty / unavailable / error / unsure  
- `DataStateView` widget: uniform retry, empty, unavailable states  

### AI / Assistant
- Voice input: on-device `speech_to_text` (ta-IN / en-IN)  
- Speak button: on-device TTS only on final completed answer  
- Stage indicators during streaming (grounding, reasoning, etc.)  
- Citations shown only when `sources` event fired (TNAU evidence retrieved)  
- Ungrounded warning (orange) when `grounded=false`  

---

## Known Bugs (acceptable for alpha)

| ID | Description | Severity |
|----|-------------|----------|
| - | Weather `condition.ta` always null (shown in English) | Low |
| - | Scheme `authority` is plain string, not bilingual (shown as-is) | Low |
| - | Assistant fallback fires when Ollama has no match (by design) | Info |

---

## Bugs Fixed This Sprint

| ID | Description |
|----|-------------|
| F1 | Nav label "உதவியாளர்" wrapping on Pixel 6 — shortened + ellipsis |
| F2 | Latin text rendering as serif in Tamil locale — Roboto + Noto fallback |
| F3 | Screen titles truncated — now allow 2-line wrap |
| C1 | Soil nutrients `category` key mismatch (was reading `name`) |
| C2 | Soil estimated units hardcoded (now reads `data.estimated.units`) |
| C3 | Scheme `source_documents` showing file paths (only http URLs shown) |
| D2 | Weather forecast dates in UTC (now `timezone=Asia/Kolkata`) |
| B1 | Weather farm-without-GPS 503 race (district HQ used as fallback; tested) |

---

## Test Summary

```
flutter test — 144 passed, 0 failed (exit 0)
```

Test files:
- `test/core/app_config_test.dart` — API URL resolution, release guards
- `test/core/token_refresh_test.dart` — single-flight refresh, reuse → logout
- `test/features/auth/auth_screen_test.dart` — phone / OTP screens
- `test/features/weather/weather_screen_test.dart` — DataState rendering
- `test/features/market/market_screen_test.dart` — commodity chips, empty crops
- `test/features/schemes/schemes_screen_test.dart` — filter, C3 link guard
- `test/features/soil/soil_screen_test.dart` — C1 category, C2 units
- `test/features/live_deviations_test.dart` — C1/C2/C3 live contract checks
- `test/features/assistant/assistant_screen_test.dart` — SSE stream, error codes
