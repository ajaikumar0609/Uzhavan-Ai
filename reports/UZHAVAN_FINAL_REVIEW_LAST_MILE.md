# UZHAVAN AI: Final Review Last-Mile Smoke Test

**Run:** 2026-11-10, 13:35-14:00. **Device:** Oppo A9 2020, CPH1937, Android 11 (API 30), serial `3b197bae` (every adb command used this serial).
**Evidence:** `reports/artifacts/final_review_smoke/` (screenshots 04-20, TTS logs, `12_tamil_api_answers.json`).

## 1. Ready to demonstrate? YES, with a defined list of what to show and what to avoid
The English assistant, TNAU-labelled answers, Weather, Market, Soil, Schemes, local **English** speech, Stop, and the disease safety gate all work on the phone. **Tamil chat answers and Tamil speech do NOT work reliably today** (details below). Demo accordingly.

## 2. Environment (checked before testing)
| Item | Result |
|---|---|
| Phone | `get-state: device`, awake, unlocked |
| Backend `127.0.0.1:8000` | healthy; `/health/config`: database, redis, chroma all true |
| PostgreSQL / Redis / Ollama | accepting connections / PONG / 0.12.3 |
| Qwen2.5 7B | `qwen2.5:7b-instruct` present, loaded by `warm_up_demo.sh` |
| ChromaDB | 520 rows (original store, unchanged) |
| `adb reverse tcp:8000` | `UsbFfs tcp:8000 tcp:8000` |
| APK | **not rebuilt**: no Flutter source is newer than the 8 Nov 16:42 build; reinstalled 10 Nov 11:36 |
| Backend flag | restarted at ~13:57 with `M4_DEMO_MODE=false` **as an environment override** (your `.env` still says `true`; not edited) so the phone matches the production safety gate |

## 3. Results (PASS / FAIL / BLOCKED)
| # | Feature | Result | Evidence / note |
|---|---|---|---|
| 1 | Login and Home | **PASS** | demo login, `04_home.png` |
| 2 | Farmer profile / farm info | **PASS** | Home card: karunya, Banana, Land preparation, 3.0 acres. Dedicated Profile / My farms screens not opened (NOT RUN) |
| 3 | English AI assistant | **PASS** | 4 questions answered in 19-27 s, `06-09` |
| 4 | Tamil text assistant | **FAIL (quality)** | answers returned (HTTP 200) but weak or wrong, see section 4 |
| 5 | NPK definition question | **PASS** | correct definition, no fallback, no invented dose, exact amount deferred to an officer (`07`) |
| 6 | TNAU-grounded answer + source attribution | **PASS** (caveat) | soil-health answer shows a "Sources" list of 5 TNAU documents (`09`). Caveat: titles are generic ("Important Links", "Centenary Publications"), real but loosely relevant |
| 7 | Weather | **PASS** | current + 7-day forecast, source Open-Meteo (`16`) |
| 8 | Market | **PASS** | "Snapshot of AGMARKNET data up to 2026-09-24; not live", Rs/quintal, "Old data" badge, no forecast or advice (`13`) |
| 9 | Soil | **PASS** | Tamil Mannvalam soil types + Soil Health Card nutrient status (`18`) |
| 10 | Government schemes | **PASS** | 136 schemes, Central/State filters, "Status not stated on source" (`17`) |
| 11 | Disease scanner | **PASS (intended gate)** | Scan screen loads (`14`). Production gate verified at API level: **HTTP 503 `model_unavailable`**, "The disease model is not yet approved for use. Please contact your local agriculture officer." An image scan from the phone's gallery was not exercised |
| 12 | Local **Tamil** TTS | **FAIL today** | log `[TTS_LANGUAGE] requested=ta-IN selected=null`: no Tamil voice data on the phone now (it worked on 8 Nov: `...-seanet-embedded`). The app **refused to speak and showed install instructions** (no cloud fallback) (`20`). Fix: install Tamil voice data (see section 6) |
| 13 | Local **English** TTS | **PASS** | `en-us-x-tpf-seanet-embedded` (on-device), `network_required=0`, answers spoken automatically (`06-10 logs`) |
| 14 | Stop / interruption | **PASS** | `[TTS_STOP]` ~170 ms after the tap, `[TTS_CANCEL]`, banner removed (`10/11`). Audible silence not confirmed by me |
| 15 | Multi-turn text context | **PASS** (caveat) | follow-up stayed on soil health / banana (`10`), but it explained soil testing/pH, not the "second point" I asked for: exact references are unreliable |
| 16 | Navigation and lifecycle | **PASS** | all tabs, More menu and sub-screens work; app relaunch kept the session. (One accidental exit by my Back key; not an app fault) |
| S1 | Tamil on-device speech recognition | **BLOCKED** | Android 11 has no on-device recognizer; app shows the offline notice and captures nothing |
| S2 | English on-device speech recognition | **BLOCKED** | same |
| S3 | Automatic submission from speech | **BLOCKED** | depends on S1/S2; host-tested only |

## 4. Actual AI responses (honest reading)
**English (on the phone):** coherent, labelled "General guidance (not from TNAU sources)" when no verified source, no invented doses. Photosynthesis 27 s, NPK 19 s, rice yellowing 27 s (cautious, defers to an officer), soil health 26 s (with TNAU sources), follow-up ~29 s.
**Tamil (same `/conversation` API the app calls, `12_tamil_api_answers.json`):**
- *நாளைய வானிலை எப்படி இருக்கும்?* routed to the weather tools, but the answer is garbled and cites a temperature only. On the phone, the Tamil weather chip answered **"no rain this week"**, which **contradicts the Weather screen** (drizzle, 45-71% chance). **Do not demo Tamil weather through chat.**
- *சந்தையில் நெல் விலை என்ன?* market tools ran; the answer says "2900 கி.கி" (per kg), but market data is **per quintal**: wrong unit. **Do not demo Tamil price chat**; use the Market screen.
- *அரசு விவசாய திட்டங்களைப் பற்றி சொல்லுங்கள்.* **misrouted** to the generic advisory path (the inflected "திட்டங்களைப்" does not match the stored scheme keyword), producing nonsense. Fix is a one-line keyword stem; **not applied** (no code changes at this stage). **Use the Schemes screen.**

## 5. Other things to know
- Tamil free-text quality is still the qwen2.5:7b limit; I make no claim it is reliable.
- English answers occasionally show raw `**bold**` markdown on screen (cosmetic; speech strips it).
- A pH range ("5.5 to 6.5") appeared in a "General guidance" answer "based on TNAU"; plausible but not source-backed.
- Latency: 19-30 s per answer on this Mac, plus 25-60 s of speech.
- `.env` still has `M4_DEMO_MODE=true`/`AUTH_DEMO_MODE=true`/`OTP_DEV_LOG=true` (dev demo flags, rejected in production by the startup guard).
- No Git commits; no code changed in this run; M4 untouched.

## 6. What to do right now
1. **Demo:** Login and dashboard; farm card; English Ask-AI (NPK, soil health with sources, rice yellowing); spoken English answer + Stop; Weather, Market, Soil and Government-schemes screens; Scan screen and explain the 503 gate; architecture (local Ollama + TNAU RAG + FastAPI); tests (343 backend, 180 Flutter).
2. **Avoid:** Tamil chat answers (weather, market, schemes); Tamil speech; any speech *input*; claiming the disease model is approved; claiming fully offline.
3. **Optional, before the demo (2-3 min):** install Tamil voice data: Settings > General management (or Additional settings) > Text-to-speech output > Google engine settings > Install voice data > Tamil (while online), then re-run a Tamil question and check logcat for `TTS dispatch: ta-in-...-embedded`.

## 7. Final statement
Ready for an honest, English-led demonstration on the Oppo. Speech recognition is BLOCKED on this phone by design; Tamil chat and Tamil speech are not demonstration-grade today.
