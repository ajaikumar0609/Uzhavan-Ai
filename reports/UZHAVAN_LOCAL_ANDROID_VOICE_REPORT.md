# UZHAVAN AI: Fully Local Android Voice (Step 3)

**Date:** 2026-11-08  **FINAL STATUS: LOCAL VOICE PARTIAL** (physical evidence so far: Oppo CPH1937 only, TTS and typed conversation; Samsung not yet tested; see sections 10-11)

Implemented, built and tested on the host. **Not verified on a physical phone: `adb devices -l` lists no device and no Samsung appears on USB.** All ten device tests are recorded as NOT RUN (`reports/artifacts/local_voice_test_results.csv`). I make no physical-device claim.

## 1. What I found (before changing anything)
| Finding | Evidence |
|---|---|
| The shipped app used Android's **default** recognizer, which may stream audio to Google | `DeviceVoiceInput` never passed `onDevice`; `speech_to_text` 7.4.0 defaults it to `false` |
| Even `onDevice: true` is **not a guarantee** | Plugin native code (`SpeechToTextPlugin.kt`): on-device recognizer only if API ≥ 31 **and** `isOnDeviceRecognitionAvailable`; otherwise it silently calls `createSpeechRecognizer()`. `EXTRA_PREFER_OFFLINE` is only a hint |
| TTS spoke even when no Tamil voice existed | `selectedLang ??= candidates.first`, then `speak()`; failure was a transient snackbar |
| Manual speaker button bypassed the controller | could desync state / overlap auto-speech |
| No ERROR state, no offline-unavailable path | |

## 2. Local speech recognition (implemented)
- New native `LocalSpeechRecognizer.kt` + `MainActivity.kt` (channel `ai.uzhavan/local_stt`). It calls **only** `SpeechRecognizer.createOnDeviceSpeechRecognizer`; the default `createSpeechRecognizer` is never called and **not even present in the compiled app** (dex check: 0 occurrences; `createOnDeviceSpeechRecognizer` ×1).
- Locale `ta-IN` (or `en-IN`), `EXTRA_PREFER_OFFLINE=true`, partial results, 1.8 s silence hints.
- **No silent fallback.** API < 31 or no on-device service ⇒ `offline_unavailable`; offline pack missing (API 33 `checkRecognitionSupport`, or error 12/13 on 31/32) ⇒ `language_missing`. The app shows an explicit notice in Tamil/English, captures no audio, and keeps text input.
- `speech_to_text` removed from `pubspec.yaml`; its classes are absent from the APK (0).
- Mic released when the app leaves the foreground (`onPause` + Flutter lifecycle observer).
- Native logs use tag `UZ_LOCAL_STT` and log text **lengths only**, never the transcript. Dart transcript debug prints are debug-build only.

## 3. Local Tamil/English TTS (implemented)
- `DeviceSpeaker` uses Android `TextToSpeech` via `flutter_tts` only; it never calls the backend `/voice/tts` (a test asserts no `/voice` request).
- For `ta-IN` / `en-IN` it requires an **installed, non-network** voice (`isLanguageInstalled`; then picks a voice with `network_required=0` and not `notInstalled`). If none exists it speaks nothing and returns `voiceMissing`.
- UI shows an install notice (Tamil and English): *Settings > General management > Text-to-speech output > engine settings > Install voice data > Tamil*. The written answer stays visible. Dismissable banner.
- Every `speak()` stops previous audio first; manual speaker button now goes through the same path.

## 4. Voice state machine
`IDLE → LISTENING → THINKING → SPEAKING → IDLE`, plus `ERROR` (cleared by the next action). Chat controller enforces:
- one submit per voice turn (`beginVoiceTurn` / `sendVoice`); empty, duplicate, late-after-cancel transcripts ignored;
- `busy` blocks parallel requests; mic tap during speech stops speech first;
- a monotonically increasing speak token: a late completion of an interrupted/replaced utterance cannot change state or restart audio;
- no auto-speech while the mic is open;
- session id carried across turns (verified: second request includes `session_id`).
After the answer the state returns to IDLE with the mic ready. I did not add automatic re-listening (feedback and privacy risk); the farmer taps the mic for the next utterance.
Response language follows the existing rule (script of the question, else UI locale); the backend preserves evidence labels (General-guidance prefix, sources) unchanged.

## 5. Privacy findings
| Check | Result |
|---|---|
| Manifest permissions (merged, from APK) | `INTERNET`, `RECORD_AUDIO`, `CAMERA` (+ an internal receiver permission). No other |
| Cleartext | release: disabled; **debug only**: enabled (needed for `http://127.0.0.1` via adb reverse) |
| STT code path | on-device only (A01). Old plugin gone |
| Cloud speech/AI/telemetry hosts in the APK | none found (googleapis speech/TTS, OpenAI, Anthropic, Gemini, Translate, Firebase, Crashlytics, analytics) |
| Analytics / Firebase / Play-services deps | none in `pubspec.yaml` / lock / gradle |
| App → backend voice endpoints | none called |
**What this does and does not prove.** It proves *this app* only requests Android's on-device recognizer and never the default one, and ships no cloud-speech client. It cannot audit the **vendor recognition service** (Google/Samsung) behind Android's on-device API, which is documented to process audio locally. Do not call the system "fully offline" until the device test with network off passes (procedure below). The assistant still needs the backend (localhost via adb reverse), and weather needs Open-Meteo.

## 6. Files changed
App: `android/app/src/main/kotlin/ai/uzhavan/uzhavan/{LocalSpeechRecognizer.kt (new), MainActivity.kt}`, `lib/features/assistant/data/voice_services.dart`, `lib/features/assistant/presentation/{chat_controller.dart, assistant_screen.dart}`, `pubspec.yaml` (+lock), `lib/core/localization/arb/{app_en.arb, app_ta.arb}` (+regenerated l10n), tests: `test/features/assistant_test.dart` (fakes updated), `test/features/local_voice_test.dart` (new, 28 tests). **Untouched:** authentication, OTP, JWT, backend RAG, ChromaDB, M4, disease code, `.env`.

## 7. Results
- `flutter analyze`: no issues. `flutter test`: **176 passed** (was 148).
- Debug APK built: `uzhavan_flutter/build/app/outputs/flutter-apk/app-debug.apk`, built with `--dart-define=API_BASE_URL=http://127.0.0.1:8000`.
- A real bug found by my own tests and fixed: when native refused to start, the `offline_unavailable` event arrived after Dart had already finished and was dropped, so the farmer would have seen no explanation.
- A test note: a *second* request in the same widget test stalls under the fake test clock; repository and controller tests show two turns completing and sharing a session, so I tested multi-turn at controller level.

## 8. Physical-device procedure (NOT executed)
Backend is running on `127.0.0.1:8000` (Ollama + Chroma). With the Samsung connected (USB debugging on):
```
adb devices -l                                            # expect RZCRA03QLKA  SM-G781B
adb -s RZCRA03QLKA install -r uzhavan_flutter/build/app/outputs/flutter-apk/app-debug.apk
adb -s RZCRA03QLKA reverse tcp:8000 tcp:8000
adb -s RZCRA03QLKA logcat -c
adb -s RZCRA03QLKA logcat -v time UZ_LOCAL_STT:I flutter:I FlutterTts:V TextToSpeech:V *:S
```
Expected log lines: `availability: ready …` then `start: recognizer=ON_DEVICE locale=ta-IN prefer_offline=true`, `[AUTO_SUBMIT]`, `[TTS_VOICE] local voice selected tag=ta-IN network_required=0`, `[TTS_LANGUAGE]`.
1. Phone Settings: install the offline **Tamil** speech pack and **Tamil TTS voice data** first (the app will say so if missing).
2. **Offline proof:** enable airplane mode with Wi-Fi/data off *for the recognition step only* (the phone still needs the adb-reverse USB link to the backend, which airplane mode does not remove); speak Tamil; a transcript must still appear. If it fails with `offline_unavailable`/`language_missing`, the phone cannot do offline Tamil and typing is the fallback.
3. Run the ten checks in the CSV (auto-submit, Tamil reply, auto TTS, stop during TTS, mic during TTS, multi-turn, English, background/foreground), saving logcat.
Unknowns I could not resolve without the phone: Android version of the SM-G781B (on-device API needs ≥ 12, checkRecognitionSupport ≥ 13), whether its recognition service ships an offline Tamil model, and whether the installed TTS engine has an offline Tamil voice.

## 9. Remaining blockers / risks
1. **Device not connected**: every physical result is open.
2. Offline Tamil recognition depends on the phone's installed pack, which is outside the app's control.
3. Tamil answer quality (qwen2.5:7b) and 20-40 s latency remain; a long wait in THINKING state is likely to feel slow in the demo.
4. `.env` still holds the unused `ANTHROPIC_API_KEY`; I did not edit your secrets file. Remove it and revoke the key if real.
5. Debug APK only; release signing, https backend and cleartext stay open items.
6. Backup: these changes are not yet in any archive.

Stopped after build and automated verification; no device available for physical verification.


## 10. Physical-device results (Oppo CPH1937, Android 11 / API 30, serial 3b197bae)
The Samsung was never connected; an Oppo was used. Evidence: logcat lines and screenshots in `reports/artifacts/oppo_voice_test/`. CSV rows P01-P12 are updated.

**What passed on the phone**
- Install, sign-in (dev demo login), live weather, backend reached over `adb reverse tcp:8000`.
- Typed question -> local Qwen + RAG -> answer (15-30 s) -> **automatic speech** in English and Tamil.
- Tamil TTS used **on-device synthesis** (`TTS dispatch: ta-in-x-tac-seanet-embedded`) and **still worked in airplane mode** (`Active default network: none`).
- Stop button: `[TTS_STOP]` 28 ms after tap; mic tap during speech: speech cut first, then the mic logic ran.

**What could not be tested: speech recognition.** Android 11 has no on-device recognizer API (needs Android 12+). The app behaved exactly as designed: log `availability: unsupported_api api=30`, the on-screen notice "Offline voice recognition isn't available on this phone, so nothing was recorded or uploaded. Please type your question.", the recognizer never started, no audio captured. **Tamil speech input, automatic submission from speech, English speech input and offline recognition remain unverified; they need an Android 12+ phone with an offline Tamil speech pack.** (Samsung SM-G781B normally ships Android 12/13, so it is the right device for this.)

**Two defects found only by the physical test (both mine)**
1. *Stuck in SPEAKING after a TTS error.* The first Tamil request failed (`[TTS_ERROR] Error from TextToSpeech`) and the banner stayed on "Speaking" because `flutter_tts` never resolves after an engine error. Fixed: `DeviceSpeaker` now completes the utterance from the completion / cancel / error callbacks, and `stop()` resolves it. 4 regression tests added (suite: **180 passed**, analyze clean); APK rebuilt and the normal Tamil flow re-verified on the phone afterwards. The error path itself was not re-triggered on the phone.
2. *My "local voice" check is not a guarantee.* The first Tamil request, before the voice pack was installed, was dispatched by Google TTS to **`ta-in-x-tac-server`** (network) even though the voice was listed as `...-local`, `network_required=0`, and `isLanguageInstalled` was true; it tried to download the pack and timed out. Android gives the app no reliable way to know in advance: all voices carry identical feature flags and `ACTION_CHECK_TTS_DATA` lists all 81 languages as available with none unavailable (I added a native probe to test this, saw it was useless, and removed it). **Consequence:** text of an answer can reach Google's TTS server the first time a language pack is missing. Mitigation, not a code fix: install the Tamil and English voice data while online *before* the demo, then confirm the logcat dispatch line says `-embedded`, not `-server`. The app's doc comment now states this limit. This is the one place the "no cloud" claim needs an asterisk.

**Other observations**
- Tamil answer quality is poor in practice (the weather answer was grammatical-looking Tamil with doubtful content); this is the known qwen2.5:7b limit, not a voice-loop issue.
- A typed NPK question fell back to the safe "information not available" message because the dose guard blocked the model's computed fertilizer totals for the 3-acre farm. Conservative false positive; crop-rotation and weather questions answered normally.
- Pre-warming (`scripts/warm_up_demo.sh`) was done; answers took about 15-30 s.

**Still open**
1. Speech recognition needs an Android 12+ device (the Samsung when connected, or any 12+ phone) with the offline Tamil pack installed.
2. Multi-turn on the device, the full background/foreground cycle with the mic open, and the error path of the TTS fix are not device-verified.
3. Debug APK only; `ANTHROPIC_API_KEY` line removed from `.env` (backup file still holds it; revoke the key).


## 11. Final acceptance run (2026-11-10)
Every row in `artifacts/local_voice_test_results.csv` is now PASS / FAIL / BLOCKED / NOT RUN (45 / 3 / 19 / 2). Oppo results from section 10 are preserved.

### Samsung SM-G781B: BLOCKED
`adb devices -l` lists only the Oppo (`3b197bae`); the Samsung (`RZCRA03QLKA`) is not on USB. Steps 2-13 of the acceptance list (API level, on-device recognizer, offline Tamil/English packs, Tamil STT, auto-submit exactly once, embedded Tamil TTS, interruptions, multi-turn, airplane mode, logs) are **BLOCKED**, rows S01-S13. Nothing was assumed. When it connects: `adb -s RZCRA03QLKA shell getprop ro.build.version.sdk` must be >= 31, then the same install/log procedure as section 8. Android 12+ does not by itself guarantee an offline Tamil model: the app's `availability` log line (`ready` / `language_missing` / `language_unsupported`) will say.
### Oppo: BLOCKED today
After the session break the app was missing from the phone; I reinstalled it (`Success`), but the screen stays black/locked (blank screenshots) and I will not try to bypass a lock. Multi-turn on the phone therefore remains NOT RUN.

### NPK fallback: root cause and fix (dosage guard NOT weakened)
**Cause.** "What is NPK fertilizer?" was classed `advisory`, which always runs the weather and `crop.fertilizer_plan` tools. The model then received the farm's area (1.214 ha) and per-hectare rates (e.g. 200 kg N/ha) and multiplied them into field totals ("242.8 kg of nitrogen"). Those totals were not in the evidence, so the guard blocked the whole answer, and a plain definition came back as "information not available".
**Fix, three separate cases as you asked:**
1. *Explaining what NPK means*: new `definitional.py` recognises explain/what-is/importance questions (English and Tamil) that ask for no amount and do not mention the farmer's field. They plan **RAG only** (no weather or fertiliser tools) and the prompt tells the model not to calculate or state quantities.
2. *General fertilizer guidance*: unchanged; numbers still need to appear in the evidence.
3. *Calculating from a verified recommendation*: the guard now accepts a kg total **only** if it equals (a `kg/ha` rate present in the evidence) x (the farm area present in the evidence). Invented doses, pesticide doses (ml/l etc.), wrong units, and totals with no rate or no area are still blocked. 22 new tests cover both directions.
**Result.** English NPK: 3/3 answered, none fell back, 4-17 s (faster, fewer tools). The quantity question ("How much NPK should I apply to my banana farm?") still takes the full guarded path and answered with the TNAU base rates.

### Tamil answers: what changed and what did not
Changes (existing Qwen2.5 7B, no new model): shorter-answer instruction (max 3 short sentences, direct answer then one action, finish every sentence); a farm-vocabulary fallback so inflected Tamil farming questions are not refused as off-topic; trimming of a sentence cut off by the 256-token limit.
Measured on the same 8 Tamil questions (`uzhavan_platform/scripts/tamil_bench.py`, answers in `artifacts/tamil_bench_after.json`; the baseline's per-answer text was lost when the scratchpad was cleared, its metrics were recorded from the run output):
| Metric | Before | After |
|---|---|---|
| Instant refusals (fallback) | 4 / 8 | **0 / 8** |
| Answered but cut off mid-sentence | 4 of 4 answered | **0 / 8** |
| Average length | 22 words | 25 words |
| Latency of answered questions | ~25-30 s | **24-45 s (avg 33 s)** |
**Quality did NOT improve.** I read the answers: they are complete short sentences but the content is still weak or wrong (for example the NPK answer expands the letters incorrectly, the rain answer is muddled, several say little yet are labelled `grounded_verified`). This is the qwen2.5:7b Tamil limit. I make no claim of better Tamil quality. For the review, prefer English answers or tool-driven Tamil (weather, market, schemes) and be ready to say Tamil free-text answers are weak.

### Tests
Backend **343 passed, 0 failed, 0 skipped** (was 321; +22). Flutter unchanged this round (180 passed earlier). No Flutter code changed since the Oppo test.

### Final status: LOCAL VOICE PARTIAL
Physical-device evidence exists only for: Oppo (Android 11) typed conversation, automatic English and Tamil speech with the on-device voice, airplane-mode Tamil speech, stop and mic-interrupt control events. **Not verified on any phone: Tamil/English speech recognition, offline recognition, automatic submission from speech, spoken multi-turn.** These need the Samsung (or another Android 12+ phone) with an offline Tamil pack.

### Open items
1. Connect and unlock the Samsung (USB debugging on, file-transfer mode, accept the prompt); unlock the Oppo if you want more tests there.
2. Install offline Tamil and English **speech-recognition** packs and Tamil/English **TTS voice data** before airplane-mode tests.
3. Audible confirmation that Stop silences the speech is still with you.
4. Tamil quality and 25-45 s latency remain demo risks.
5. Backup: these backend changes (definitional.py, planner/intent/prompt/llm_node/safety_validator edits, tests, tamil_bench.py) and the Flutter TTS fix are not yet in any archive; the earlier addendum archive predates them.
