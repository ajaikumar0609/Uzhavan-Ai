# FP-006: Remove fabricated agricultural outputs and add honest data states

**Status:** `COMPLETE` (approved 2026-09-25; implemented + QA 2026-09-25)
**Sprint:** Sprint-006 (Production Completion)
**Milestone:** M-06: Real application (Phase 1 of 18)
**Owner:** Master Agent (spec) → Frontend Sub-Agent (implementation)
**Depends on:** nothing. It must land first, because every later FP builds on the state model defined here.
**Evidence:** `reports/ui_audit_2026-09-25/UI_UX_AUDIT.md` (sections D, G) · `reports/production_build/PHASE0_BASELINE.md`

---

## 1. Overview
The frontend currently **invents** agricultural information whenever a backend call fails or doesn't exist: a 94% "Rice Leaf Blast" diagnosis with a pesticide dose for any photo, a fictional agricultural officer, fixed Thanjavur weather, made-up mandi prices with "sell this week" advice, "Eligible" scheme badges with no farmer data, a fake farmer named முருகன் with 82% farm health, and "Based on TNAU & government data" footers over all of it.
FP-006 removes every fabricated output and replaces it with **explicit, bilingual data states**, so the app only shows what it actually knows. **No new features are added here.** Real data arrives in FP-007 onward.

## 2. Business Goal
- **Farmer safety:** no diagnosis, dose, irrigation instruction or sell advice without a real, validated source.
- **Credibility:** in a review, a panel can press any button and never see invented numbers.
- **A foundation for integration:** one shared state model (LOADING / SUCCESS / EMPTY / UNAVAILABLE / ERROR / UNSURE) that FP-007 to FP-017 plug real APIs into.

## 3. User Story
```
As a Tamil Nadu farmer
I want UZHAVAN to tell me plainly when it does not have information
So that I never act on a disease, price, weather or scheme result that was made up
```

## 4. Acceptance Criteria
- [ ] AC-1 **Disease:** with the disease service unavailable (the current state), uploading **any** image shows the UNAVAILABLE state "சரிபார்க்கப்பட்ட நோய் கண்டறியும் மாதிரி இன்னும் கிடைக்கவில்லை / Validated disease model unavailable". **No disease name, confidence, severity, treatment, dose or officer** is shown.
- [ ] AC-2 **Disease:** the result/preview area shows the **farmer's own uploaded photo**, never the bundled sample leaf. The simulated "Capture" (a 1.7 s timer with no image) is removed. Capture opens the device camera (`<input type="file" accept="image/*" capture="environment">`), or the button is hidden where unsupported.
- [ ] AC-3 **Disease:** a real backend result with no `officer` shows **no officer card** (no fictional fallback). The "Call officer" and "Save to Farm Diary" buttons are removed until FP-016 and the diary exist.
- [ ] AC-4 **Weather** (home card + /weather): while the API is unavailable, the UNAVAILABLE state "தற்போதைய வானிலை தரவு கிடைக்கவில்லை / Current weather data unavailable" appears with a Retry button. No temperature, humidity, rain %, hourly, 7-day or irrigation instruction is shown.
- [ ] AC-5 **Market** (home carousel + /market): UNAVAILABLE state "தற்போதைய சந்தை தரவு கிடைக்கவில்லை / Current market data unavailable" + Retry. The **7-day chart and the "Sell recommendation" card are removed** (no validated forecast exists; M6 gate).
- [ ] AC-6 **Schemes** (home): no "Eligible" / "தகுதி" badge anywhere. While the API is unavailable, the UNAVAILABLE state shows. When a list does load, each item shows "தகுதியை அறிய விவசாயி விவரங்கள் தேவை / Eligibility requires farmer profile information" until FP-010.
- [ ] AC-7 **Farmer identity:** no hard-coded name. The greeting shows the profile name if a profile exists; otherwise a neutral "வணக்கம் / Welcome" + "Complete your profile" link. Profile shows "Not set" fields instead of முருகன் / Thanjavur / Paddy / 2.5 acres.
- [ ] AC-8 **Home farm-health card and "AI Suggestions" card** (82%, ADT 43, day 68/115, "postpone urea") are **removed** (no data source until FP-008/FP-014). Today's tasks (static) are removed. The static suggested *questions* stay: they are prompts, not outputs.
- [ ] AC-9 **Diary:** the fake timeline and finance totals are removed. EMPTY state "இன்னும் பதிவுகள் இல்லை / No entries yet" when there are no real entries. UNAVAILABLE when the API fails.
- [ ] AC-10 **Provenance:** "TNAU மற்றும் அரசு தரவின் அடிப்படையில்" (Home) and "TNAU & அரசு தரவால் இயக்கப்படுகிறது" (onboarding splash) are removed. Source text may appear only on a card whose data actually came from that source (enforced from FP-007 on).
- [ ] AC-11 **Assistant:** network failure shows a bilingual message ("சேவையகத்தை அணுக முடியவில்லை / Can't reach the UZHAVAN server") instead of the raw "Failed to fetch", and **no "Listen" button** appears on error messages.
- [ ] AC-12 **Header bell:** the permanent red dot is removed and the link is relabelled "Profile / சுயவிவரம்" (no notification system exists yet).
- [ ] AC-13 Every data-backed card uses the shared `DataState` component with the six states. LOADING shows a skeleton; ERROR and UNAVAILABLE show Retry; UNSURE is reserved for the disease model (FP-012).
- [ ] AC-14 `lib/prototype.ts` keeps **only** `bi()`, the `Bi`/`Lang` types and `suggestedQuestions`. `weather`, `market`, `tasks`, `schemes`, `cropStatus` and `diseaseResult` are deleted, so a later regression **fails to compile**.
- [ ] AC-15 An automated **no-fabrication test** fails the build if any of the known fabricated strings (e.g. "Magnaporthe", "K. Raja", "ADT 43", "2320", "முருகன்" as a value, "Eligible") appear in `src/` outside tests.
- [ ] AC-16 `tsc` 0 errors; `vite build` passes; the backend test suite unchanged (70 pass).

**Out of scope (later FPs):** real weather/market/scheme/auth APIs (FP-007 to FP-010), the i18n framework (FP-015; FP-006 puts its new strings in one module ready to move), the Tailwind Chrome<111 fix (FP-016), and any disease model (FP-012, after independent evaluation).

## 5. UI Design
**Shared component** `components/app/DataState.tsx`:
| State | Visual | Text (ta / en) | Action |
|---|---|---|---|
| LOADING | card-shaped skeleton (existing `ui/skeleton`) | – | – |
| SUCCESS | the card's normal content + a small source/date line (from FP-007) | – | – |
| EMPTY | muted icon + one line | e.g. "இன்னும் பதிவுகள் இல்லை / No entries yet" | optional CTA |
| UNAVAILABLE | info icon, neutral tone | "{feature} தரவு கிடைக்கவில்லை / {Feature} data unavailable" | Retry |
| ERROR | warning icon | "ஏதோ தவறு நடந்தது / Something went wrong" | Retry |
| UNSURE | amber tone | "உறுதியாகச் சொல்ல முடியவில்லை: வேளாண் அலுவலரை அணுகவும் / Not sure: please consult an agricultural officer" | – |

Screen changes (layout otherwise unchanged):
- **Home:** greeting (profile or neutral); weather card → DataState; scan + AI tiles (unchanged); ~~farm health~~; ~~AI suggestions~~; suggested questions (unchanged); ~~tasks~~; market carousel → DataState; schemes → DataState, no badges; ~~provenance footer~~.
- **Scan:** real camera/gallery → **own-photo preview** (remove/retry) → uploading → UNAVAILABLE / ERROR / (FP-012: result or UNSURE).
- **Weather / Market / Diary / Profile:** as in AC-4, 5, 7, 9.

## 6. API Contract
**No backend API changes in FP-006.** The frontend keeps calling the existing paths. The **state mapping** is defined here and reused by every later FP:
| Response | UI state |
|---|---|
| network failure / connection refused | UNAVAILABLE |
| HTTP 404 / 501 / 503 | UNAVAILABLE |
| HTTP 5xx (other) | ERROR |
| HTTP 200 with an empty list | EMPTY |
| HTTP 200 with data | SUCCESS |
| disease 200 with `status:"unsure"` (FP-012) | UNSURE |

`lib/api/client.ts` gets a typed `ApiError.kind: "unavailable" | "error"` so hooks don't parse status codes themselves.

## 7. Database Changes
None.

## 8. AI Changes
None to the model or prompts. Assistant **UI** only: a bilingual network-error message, and the Listen button hidden on errors (AC-11).

## 9. Agent Responsibilities
| Agent | Task |
|---|---|
| Master Agent | This FP; review; gate sign-off. Writes no code |
| Frontend Sub-Agent | T1 `DataState` + `ApiError.kind` · T2 hooks: delete all prototype fallbacks, expose `status` · T3 Home · T4 Scan (camera, own preview, UNAVAILABLE) · T5 Weather/Market/Diary/Profile · T6 Assistant error UX · T7 trim `prototype.ts` · T8 no-fabrication test |
| QA Sub-Agent | Test plan §10; Android emulator + desktop run; screenshots |
| Security Sub-Agent | §11 review |
| Docs Sub-Agent | §13 |

## 10. Testing
- **Static:** `tsc --noEmit` 0 errors; `vite build` passes.
- **No-fabrication test** (AC-15): a script scanning `src/` for the blocked-string list; exits non-zero on a hit. Wired as `npm run check:no-fabrication`.
- **Unit (Vitest):** hooks return `status` correctly for mocked fetch outcomes (refused, 404, 503, 500, 200-empty, 200-data): 6 cases × 5 hooks.
- **Manual/E2E**, with the backend **down** and then **up** (conversation only):
  1. Scan: upload a groundnut photo → own photo shown → UNAVAILABLE; no disease text (the regression for audit D#1).
  2. Home/Weather/Market/Schemes/Diary/Profile show UNAVAILABLE/EMPTY; Retry refetches.
  3. Assistant with the backend down → bilingual error, no Listen button; backend up → normal streaming answer.
- **Devices:** desktop Chrome 1440×900; mobile 390×844; **Android emulator Pixel 6** (Chrome 109; the colour issue is known and tracked in FP-016).

## 11. Security
- The camera uses the file input with `capture` (no `getUserMedia` stream); the image stays in memory with an object URL, and the URL is revoked on reset.
- No new data leaves the device; no new secrets. The error messages don't echo server internals (the raw `detail` is no longer shown to the user).
- Removing fabricated medical-like/pesticide advice is itself a safety fix.

## 12. Performance
- Fewer components on Home (3 cards removed). No new dependencies except dev-only Vitest (if not already present).
- Retry uses React Query `refetch`; no polling added.

## 13. Documentation
- Update `reports/ui_audit_2026-09-25/UI_UX_AUDIT.md` with a "Resolved by FP-006" column.
- A `frontend/src/components/app/DataState.tsx` JSDoc with the state table (§5, §6).
- `docs/feature-packs/FP-006…md` status → COMPLETE with evidence links (screenshots, test logs).

## 14. Demo Checklist
- [ ] Upload any leaf with the disease service off → honest UNAVAILABLE, the farmer's own photo, no diagnosis
- [ ] Home: no fake name/health/tasks/advice; weather/market/schemes show UNAVAILABLE + Retry
- [ ] Market: no chart, no sell advice
- [ ] Assistant: works with the backend up; graceful bilingual error with the backend down
- [ ] Emulator run recorded (screenshots in `reports/production_build/FP-006/`)

## 15. Release Notes
> **FP-006: Honest data states (v0.6.0-rc1).** UZHAVAN no longer shows invented results. Where a service isn't connected yet, you'll see a clear "data unavailable" message with a Retry button, in Tamil and English. The disease scanner now shows your own photo and won't display any diagnosis until a validated model is connected. The fixed weather, market prices, sell advice, scheme eligibility badges and sample farmer details have been removed.

---

## Sign-offs Required Before Status → COMPLETE
| Gate | Owner | Status | Evidence |
|---|---|---|---|
| Planning | Project owner | ✅ approved 2026-09-25 | chat approval |
| Architecture | Master Agent | ✅ | shared `DataState` + `ApiError.kind` mapping per §5/§6 (`lib/dataStatus.ts`, `lib/api/types.ts`) |
| Backend | – | N/A | no backend change; pytest unchanged at 70 pass / 10 errors (baseline) |
| Frontend | Frontend Sub-Agent | ✅ | AC-1…AC-16 done; 29 files changed/added (list in `reports/production_build/FP-006/QA_REPORT.md`) |
| AI | – | N/A | UI-only change |
| Tests | QA (Master Agent re-run) | ✅ | tsc 0 errors · vite build OK · no-fabrication OK (14 strings, 0 hits) · Vitest 37/37 · desktop 390×844 + Android emulator Pixel 6 screenshots |
| Security | Master Agent review | ✅ | object URL revoked on reset; raw server `detail` no longer shown; no secrets added; fabricated pesticide/diagnosis output removed |
| Performance | Master Agent review | ✅ | 3 Home cards removed; no runtime deps added (dev-only: vitest, @testing-library/react, jsdom) |
| Documentation | Master Agent | ✅ | this FP, the audit's "Resolved by FP-006" section, QA_REPORT.md |
| Standards | Master Agent | ✅ | matches the existing `bi()`/`L`/kit patterns; new strings centralised in `lib/uiStates.ts` |

**Known, deferred (not FP-006 scope):** the yellow-disc icon and invisible chip text on Chrome < 111 → FP-016 · the "Thanjavur" query parameter still sent (never displayed) → FP-007/FP-008 · the Profile "Notifications/Help/About" rows are still inert → FP-020 · `bun.lock` not regenerated (npm lockfile is authoritative).
