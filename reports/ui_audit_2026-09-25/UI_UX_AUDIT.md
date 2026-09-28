# UZHAVAN AI: UI/UX audit (read-only), 2026-09-25

**Scope:** React frontend `~/Desktop/agri/frontend` (TanStack Start + Vite; the prompt said `uzhavan_platform`, but that folder holds the backend) and the backend it calls, `~/Desktop/agri/uzhavan_platform`.
**Method:** full source review of all routes, hooks and API modules, plus a live click-through in Chromium (Playwright) at 390×844 (mobile) and 1440×900 (desktop). The live run had the frontend up and the **backend down** (no backend `.env`/venv on this machine), which is exactly what a demo shows if the backend isn't started. Screenshots are in `screenshots/`.
**No code was modified.** Temporary browser artifacts were removed.

## Key finding
**The app is built to never look broken, so it looks finished.** Weather, market, schemes, diary, profile and the disease result all **silently substitute hard-coded demo data** whenever their API fails. Most of those APIs don't exist, so they always fail. Nothing on screen marks the data as demo, and several screens carry "Based on TNAU & government data" footers. The disease scan in particular shows a **confident, fabricated diagnosis with a pesticide dose** for any photo.

---

## A. Page and route inventory
| Route | Page | In bottom nav | Main components |
|---|---|---|---|
| `/` | Home | ✅ Home | Greeting, weather card, Leaf-scan + Ask-AI tiles, farm-health ring (crop/stage/day), "AI recommendation" card, suggested questions, today's tasks, market carousel, schemes list, provenance footer |
| `/onboarding` | Registration | ❌ (entry via Profile) | Splash → language → phone + OTP → details (name/district/phone) → farm (acres/crop/soil) → Finish |
| `/assistant` | AI assistant | ✅ AI | Chat bubbles (SSE streaming, stage indicators), suggested questions, text input, mic (Web Speech STT), "Listen" (TTS), citations, clear chat |
| `/scan` | Disease detection | ✅ centre button | Camera frame (sample image), Gallery, Capture, Flash; analysing animation; result (name, scientific, severity, confidence ring, organic/chemical tabs, nearby officer + call, "Save to Farm Diary") |
| `/weather` | Weather | ✅ Weather | Current conditions, irrigation advice, hourly, 7-day |
| `/market` | Market prices | ✅ Market | Paddy 7-day chart, "sale recommendation", nearby markets list |
| `/diary` | Farm diary | ❌ (Home "All" link) | Activity timeline, income/expense summary |
| `/profile` | Profile/settings | ❌ (bell icon!) | Farmer card (name/district/crop/area), language toggle, dark mode, notifications/help/about rows, logout |
| `/sitemap.xml` | SEO | – | – |
| **(none)** | **Government schemes page** | – | Schemes appear **only as a 3-item card on Home**. There's no schemes page, detail view, eligibility checker or application steps |
| **(none)** | **Satellite / crop map** | – | **No UI** |
| **(none)** | **Soil** | – | Only a soil-type picker in onboarding. **No soil page** |

Navigation: the bottom bar has Home · Weather · Scan · Market · AI. The **bell icon (labelled "Notifications", with a permanent red dot) links to Profile**. Diary is reachable only from Home's tasks "All" link. Onboarding is reachable only from Profile.

## B. Functional status by feature
Frontend calls go to `VITE_API_URL` (`http://127.0.0.1:8000`) → `backend/conversation/main.py`, which serves **only** `/health`, `/metrics`, `/conversation`, `/voice/stt`, `/voice/tts` and `/api/disease/scan`.

| Feature | UI | Endpoint the UI calls | Endpoint exists on :8000? | What the user sees today | Status |
|---|---|---|---|---|---|
| Tamil/English conversation | ✅ | `POST /conversation` (SSE) | ✅ (anonymous allowed by default) | Real streamed answer when the backend + LLM key run; **raw "Failed to fetch"** when not | **Backend-connected** (needs backend + LLM running) |
| TNAU citations | ✅ | `sources` SSE event | ✅ | Citations shown **only if** the backend emits sources | Connected; quality depends on the 520-chunk index (CPG 2020 not yet indexed) |
| Voice input (STT) | ✅ mic | **Browser Web Speech API** (`ta-IN`) | n/a (backend `/voice/stt` **unused**) | Works in Chrome/Edge (audio goes to Google); **not in Firefox**; always `ta-IN` even in English mode | Browser-only |
| Voice output (TTS) | ✅ "Listen" | Browser `speechSynthesis` | n/a (backend `/voice/tts` **unused**) | Depends on a Tamil voice being installed on the device | Browser-only |
| Disease scan | ✅ | `POST /api/disease/scan` → forwards to :8001 `/predict` | Route ✅, but the **:8001 model loader (`model_loader.py`) doesn't exist**, so the model can never load and every scan errors | **Fabricated "Rice Leaf Blast 94%" for ANY photo** (verified with a groundnut-rust photo) | **Broken + mock fallback (unsafe)** |
| Weather | ✅ | `GET /api/weather` | ❌ | Hard-coded Thanjavur 31°, 65% rain, "skip irrigation today" | **Mock only** |
| Market | ✅ | `GET /api/market/prices` | ❌ | Hard-coded prices (paddy ₹2,320), fake 7-day chart, **"good to sell this week"** | **Mock only** |
| Schemes | Home card only | `GET /api/schemes` | ❌ | 3 hard-coded schemes with **"Eligible" badges** | **Mock only** |
| Registration / OTP | ✅ | `/api/auth/send-otp`, `/verify-otp` | ❌ (a separate auth service uses `/auth/...` and `/farmers/profile` POST: **path and method mismatch**) | Can finish with **no phone, no OTP, no data** → lands on Home as "முருகன்" | **Broken (not enforced, not saved)** |
| Farmer profile | ✅ | `GET/PUT /api/farmer/profile` | ❌ | Always the placeholder farmer (முருகன், Thanjavur, Paddy, 2.5 acres) | **Mock only** |
| Farm diary | ✅ view | `GET/POST /api/diary` | ❌ | Fake timeline + finances; **no way to add an entry** (the hook exists, no UI) | **Mock only, read-only** |
| Home farm health / crop stage / tasks / AI recommendation | ✅ | none | – | Always fixed demo values | **Static mock** |
| Satellite intelligence | ❌ | – | – | – | **Missing** |
| Soil intelligence | ❌ (onboarding picker only) | – | – | – | **Missing** |

## C. Missing UI
| Missing | Why it matters |
|---|---|
| Government schemes page (list, detail, eligibility, how to apply, official link) | We have 136 structured schemes (`09_government_schemes/processed/schemes.jsonl`) and nowhere to show them |
| "Demo data" / "Offline" / "Last updated" indicators | `AppShell` has an `offline` banner prop that **no page uses** |
| Error states for weather/market/schemes/profile/diary | Hooks expose `isError`/`isLoading`; **no page renders them** |
| UNSURE / low-confidence disease result, "unsupported crop" | Required by the approved M4 gate |
| Crop picker before a disease scan | The M4 design needs the crop (per-crop heads) |
| User's own photo preview in the result | The result always shows the bundled sample leaf |
| Add-diary-entry form | `useCreateDiaryEntry` exists, but nothing calls it |
| Satellite / crop-calendar view | Research-only models today, so this should stay hidden or be labelled "coming soon" |
| Soil card | District soil data exists (`04_soil/processed`) |
| Market: "forecast available" vs "today's price only" states | Required by the approved M6 rule (16 eligible pairs) |

## D. Broken / misleading UX
| # | Screen | Problem | Severity |
|---|---|---|---|
| 1 | Scan | Backend failure (always, today) **or** tapping Capture shows **"Rice Leaf Blast, 94%, high accuracy"** + chemical dose (Tricyclazole 0.6 g/L) for **any** image, including a groundnut leaf | 🔴 Critical (farmer safety) |
| 2 | Scan | Fictional "Agri Officer K. Raja, 4.2 km" shown, even alongside a *real* result (`useDisease` falls back to it) | 🔴 |
| 3 | Scan | The Capture button doesn't open a camera; it simulates a scan after 1.7 s | 🔴 |
| 4 | Market | Fabricated price trend and **"good to sell this week"** advice | 🔴 (financial advice from fake data) |
| 5 | Home / Onboarding | "Based on TNAU & government data" / "Powered by TNAU & govt data" shown over mock data | 🔴 (false provenance) |
| 6 | Home | Schemes marked **"Eligible"** with no farmer data | 🟠 |
| 7 | Onboarding | OTP never verified; the "Continue" button advances with an empty phone; a failed profile save is swallowed and the user still lands on Home | 🟠 |
| 8 | Weather / Home | Fixed Thanjavur weather + irrigation instruction shown as current | 🟠 |
| 9 | Home / Profile | Name "முருகன்", crop "Paddy (ADT 43)", 82% health, day 68/115 shown as the user's own | 🟠 |
| 10 | Header | Bell labelled "Notifications" with a permanent red dot → opens Profile | 🟡 |
| 11 | Scan result | "Call officer" and "Save to Farm Diary" buttons do nothing (no handlers) | 🟡 |
| 12 | Profile | Notifications / Help Center / About rows do nothing | 🟡 |
| 13 | Home | Suggested-question chips open the assistant **without the question** | 🟡 |
| 14 | Assistant | The error shows raw English **"Failed to fetch"** in the Tamil UI, and offers "Listen" on the error | 🟡 |
| 15 | Assistant | STT is locked to `ta-IN` in English mode; there's no Tanglish handling in the UI | 🟡 |
| 16 | Shell | Fake phone status bar (fixed "9:41", signal, battery) on real phones too, not only in the desktop mock-up | 🟡 |
| 17 | Profile | Area shown as `area_ha × 2.47` without rounding (e.g. "2.4700000000000002 acres") once real data arrives | 🟡 |
| 18 | Contract | Backend severity `medium` vs frontend `moderate` → the severity colour falls to the default | 🟡 |
| 19 | Global | Missing favicon (404) | ⚪ |

## E. Demo readiness
| Flow | Ready? | Condition |
|---|---|---|
| 1. Register / add farm | ❌ | Walks through visually but saves nothing and verifies nothing. Present it as "UI prototype" only |
| 2. Ask in Tamil | ✅ with conditions | Backend on :8000 + LLM key running; Chrome/Edge for voice; Tamil TTS voice installed |
| 3. TNAU-grounded answer | ✅ with conditions | As above; citations depend on retrieval (CPG 2020 not indexed yet) |
| 4. Scan diseased leaf | ⛔ **do not demo as-is** | Always shows a fabricated rice-blast diagnosis. Blocked until the M4 model + the UNSURE state are wired, or the fallback is removed |
| 5. Weather-aware advice | ❌ | The weather screen is 100% mock. The assistant *may* use weather through its tools; unverified in this audit |
| Market / schemes / diary / profile | ❌ | Mock only. Show only if clearly labelled "demo data" |
| Desktop presentation | ✅ | Renders as a centred phone mock-up; no layout breakage; no horizontal overflow at 390 px |

## F. Recommended changes, in priority order (no code changed yet; awaiting approval)
**P0: remove fabricated outputs (safety and honesty; small changes)**
1. Scan: delete the prototype fallback. On error show "Couldn't analyse; try again or contact your agri officer", with no diagnosis. Remove the fictional officer fallback. Show the user's own photo.
2. Scan: remove the simulated Capture, or wire it to the real camera (`<input capture="environment">`).
3. Weather, market, schemes, profile, diary, home crop-status/tasks/AI-recommendation: replace silent fallbacks with an explicit "demo data" badge (or an error state), and render `isLoading`/`isError`.
4. Remove the "Based on / Powered by TNAU & government data" footers from any screen showing mock data.
5. Remove "Eligible" badges until eligibility is actually computed.
6. Remove market "sell" advice until M6 exists; show "today's price" only (the real Agmarknet data is ready).

**P1: connect what already exists**

7. Add backend endpoints on :8000 backed by the data we collected:
   - `/api/market/prices`: `tn_mandi_prices.parquet`, latest price per market and commodity.
   - `/api/weather`: NASA POWER / Open-Meteo live.
   - `/api/schemes`: `schemes.jsonl`.
8. Auth/profile: align the frontend paths with the auth service (`/auth/*`, `/farmers/profile`) or add `/api` routes; enforce OTP verification; surface save errors.
9. Build a schemes page (list, detail, official link, required documents, "how to apply" where available).
10. Disease scan UI for M4: crop picker (the 6 supported crops), UNSURE state, "unsupported crop" state, research-only labelling per crop (only groundnut can become production-eligible).

**P2: polish**

11. Assistant: Tamil error messages, hide "Listen" on errors, STT language follows the UI language, pass the suggested question through from Home.
12. Bell → real notifications or remove the dot; make Call / Save / Help / About work or remove them.
13. Fake status bar only inside the desktop frame; favicon; round the acres; align severity vocabulary.
14. Diary add-entry form.

**Hide for the demo (research-only or missing):** satellite and crop-calendar views, soil intelligence, and rice disease.

---

## G. Android emulator run (Pixel 6 AVD, Android Chrome 109), 2026-09-25
Setup: `emulator -avd Pixel_6`, `adb reverse tcp:5180 tcp:5180` and `tcp:8000`, app opened at `http://127.0.0.1:5180`. Screenshots `10`–`13`.

| # | Finding | Severity |
|---|---|---|
| G1 | **Invisible text and icons on older Android Chrome.** The crop-stage chip is an empty green pill, and the "Ask AI" and AI-recommendation icons are plain yellow discs. Cause: **Tailwind CSS v4 needs Chrome ≥ 111**. Opacity utilities such as `bg-success/15` are emitted as a *solid* colour, with the translucent version applied only under `@supports (color: color-mix(...))`. On Chrome 109 the background becomes solid and matches the text/icon colour (`text-success`, `text-accent`), so the content disappears. It affects every `Chip` (success/warning/danger/info variants) and every icon on a `/15`-style tint. Budget phones with older Chrome/WebView will look the same | 🟠 High (field devices) |
| G2 | **Double status bar**: the real Android status bar (3:34) sits above the app's fake "9:41 / signal / battery" bar | 🟡 |
| G3 | The scan "camera" is a **static stock photo**, not a live camera preview | 🔴 (with D#1–3) |
| G4 | Tamil fonts (Noto Sans Tamil) render correctly. Layout fits 1080×2400 with no overflow. The bottom nav and the centre scan button are reachable | ✅ |
| G5 | The assistant's mic button is **enabled** on Android Chrome (Web Speech available). Speech itself wasn't tested (the emulator has no microphone input configured) | ✅ UI |

Fix options for G1 (not applied): add a PostCSS/`@supports not (color: color-mix(in lab, red, red))` fallback that defines the tints as fixed rgba colours, **or** set and document a minimum of Android Chrome 111+. The first is recommended for rural devices.

---

## Resolved by FP-006 (2026-09-25)
| Audit item | Status |
|---|---|
| D#1 fabricated diagnosis + dose · D#2 fictional officer · D#3 simulated capture | ✅ resolved: own photo, honest UNAVAILABLE, real camera input |
| D#4 fake market trend + sell advice | ✅ removed |
| D#5 false TNAU/government provenance footers | ✅ removed |
| D#6 fake "Eligible" badges | ✅ removed ("eligibility requires farmer profile") |
| D#7 onboarding doesn't verify OTP | ⏳ FP-008 |
| D#8 fixed weather · D#9 fake farmer name/crop/health | ✅ removed (UNAVAILABLE / neutral greeting / "Profile not set up") |
| D#10 bell with a fake dot | ✅ now a Profile icon, no dot |
| D#11 dead Call/Save buttons | ✅ removed |
| D#12 inert Profile rows | ⏳ FP-020 |
| D#13 suggested-question pass-through | ⏳ FP-017 |
| D#14 raw "Failed to fetch" + Listen on errors | ✅ resolved |
| D#15 STT fixed to ta-IN | ⏳ FP-015 |
| D#16 / G2 fake status bar | ⏳ FP-016 |
| D#17 unrounded acres | ✅ 1 decimal |
| D#18 severity medium/moderate | ✅ accepted both |
| G1 invisible text/icons on Chrome < 111 | ⏳ FP-016 |
