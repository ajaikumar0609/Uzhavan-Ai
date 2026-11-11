# M-06 Production Completion: Feature Pack sequence

Each FP is written, **approved by the project owner**, then implemented and tested before the next starts (per the engineering-workflow rule). The Colab disease training (M4) runs in parallel and is never modified by these FPs.

| Order | FP | Plan phase | Scope | Depends on | Status |
|---|---|---|---|---|---|
| 1 | **FP-006** | 1 | Remove fabricated outputs; shared DataState (LOADING/SUCCESS/EMPTY/UNAVAILABLE/ERROR/UNSURE) | – | ✅ COMPLETE 2026-09-25 |
| 2 | FP-007 | 14 + 13 (config) | Environment config: `VITE_API_BASE_URL` (desktop / emulator 10.0.2.2 / LAN / HTTPS); backend settings validation (fail-closed secrets, OTP logging only in development), CORS incl. PUT + Capacitor origins, pinned requirements, `.env.example` | 006 | **PLANNING: awaiting approval** |
| 3 | FP-008 | 2 + 3 | Auth mounted on :8000 with aligned paths + real auth (phone + dev-OTP, JWT, refresh, logout, session restore) + farmer & farm profile in Postgres | 007 | not started |
| 4 | FP-009 | 5 | Real weather: current / forecast (Open-Meteo, existing client) with provider, timestamp and location; unavailable state; crop-aware notes limited to documented rules | 007, 008 | not started |
| 5 | FP-010 | 6 | Real market: load `tn_mandi_prices` into Postgres; latest observed price + history trend; "Observed on" date; no advice | 007 | not started |
| 6 | FP-011 | 7 | Government schemes page (136 records), official links, and rule-based eligibility only from documented criteria (4 states) | 008 | not started |
| 7 | FP-012 | 4 | Home dashboard built only from real sources (profile, weather, market, recent activity) | 008–011 | not started |
| 8 | FP-013 | 16 | Diary / history (questions, scans, notes) | 008 | not started |
| 9 | FP-014 | 9 | Soil module (regional SoilGrids/SHC vs measured soil-test entry, clearly separated) | 008 | not started |
| 10 | FP-015 | 12 | Centralised i18n + top-right தமிழ் ↔ English switch | 006 | not started |
| 11 | FP-016 | 13 | Android: Chrome<111 colour fallback, status bar, safe areas, Capacitor APK + AAB config | 007, 015 | not started |
| 12 | FP-017 | 11 | Assistant evidence rules (no invented weather/prices/diagnosis/eligibility) wired to the new tools | 009–011 | not started |
| 13 | FP-018 | 8 | Disease integration: **only after** the M4 independent evaluation. Crop picker, UNSURE, per-crop production/research labels | M4 eval | blocked on Colab |
| 14 | FP-019 | 10 | Satellite module: research/under-validation labelling until the SICKLE licence + scope gates pass | SICKLE gates | blocked |
| 15 | FP-020 | 15, 17, 18 | Full UI completion pass, end-to-end testing (desktop, mobile, emulator), production quality gate, final 5 reports | all | not started |
