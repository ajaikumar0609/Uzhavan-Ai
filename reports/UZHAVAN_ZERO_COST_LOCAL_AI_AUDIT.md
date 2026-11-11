# UZHAVAN AI: Zero-Cost / Local-First AI Audit and Assistant Repair

**Date:** 2026-11-08  **Result: POLICY ENFORCED. ASSISTANT IMPROVED BUT NOT REVIEW-GRADE IN TAMIL**

Inventory: `reports/artifacts/uzhavan_external_service_inventory.csv`. Raw run: `reports/artifacts/zero_cost_final_assistant_run.json` (taken **before** the last two tweaks, repeat_penalty 1.05 and the Tamil 0.48 threshold; the Tamil rows in section 4 reflect the later re-run, which was not saved).

## 1. Policy compliance: what I found and removed
| Finding (before) | Where | Action |
|---|---|---|
| Hard-coded **Anthropic** and **OpenAI** endpoints with LLM fallback by env var | `backend/cognitive/llm/service.py` | Removed. Only `ollama` exists. Unsupported provider returns an error and makes **no** network call |
| `LLM_PROVIDER` accepted `claude`/`openai`; `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `CLAUDE_MODEL`, `OPENAI_MODEL` settings | `backend/shared/settings.py` | `LLM_PROVIDER` is now `Literal["ollama"]` (start-up fails for anything else, any environment); the key/model fields are gone |
| **OpenAI Whisper** (STT), **Google Cloud TTS**, **gTTS** (sends text to Google Translate; was the **default** TTS) | `backend/conversation/routes/voice.py`, `settings.TTS_PROVIDER="gtts"` | Rewritten local-only. STT = local faster-whisper (off by default). `/voice/tts` returns 503 "use on-device TTS". Default `TTS_PROVIDER=browser-only` |
| Template advertised paid keys + gTTS | `.env.example`, `requirements-voice.txt` | Paid keys and gTTS removed |
| Health route probed paid-provider keys | `routes/health.py` | Now reports only the local provider |

**Not touched, needs your action:** `uzhavan_platform/.env` still contains an `ANTHROPIC_API_KEY` line. Nothing reads it any more, but a live key should not sit in a project file. I did not edit your secrets file. **Delete the line (and revoke the key if it is real).**

**Mobile app (not changed, out of scope this step):** Flutter uses on-device `speech_to_text` and `flutter_tts`, and never calls the backend voice routes. But Android's recognizer may stream audio to Google's servers unless on-device recognition is forced; the app does not set it. This is a privacy/policy gap that needs a decision (force `onDevice`/offline Tamil pack, or accept).

**Remaining external calls at runtime:** one: **Open-Meteo** (weather). I fetched and read their terms (2026-11-08): free API is **non-commercial only**, 600/min · 5,000/h · 10,000/day, data CC BY 4.0 (attribution), no per-call billing, they may block misuse; only district lat/lon is sent, no farmer data. The project is fine under these terms while it stays free with no ads or subscriptions. If it is ever commercialised, a paid Open-Meteo plan (or IMD data already in `uzhavan_data`) is needed. Market and soil services use local data only (their URLs are citation links, no HTTP call). Paid **SMS** (MSG91/Twilio) is configurable but disabled (`SMS_PROVIDER=none`); not an AI API, but a future cost.

## 2. Assistant repair: root causes and fixes
| # | Problem | Cause | Fix |
|---|---|---|---|
| 1 | RAG contributed nothing, silently | `RAGAgent` treated `RAGService.retrieve()`'s `ServiceResult` as a list → `'tuple' object has no attribute 'confidence'`, swallowed by `except` | Unwrap `.data` (2 call sites) |
| 2 | Crop questions would have still found nothing | Filter `crop="paddy"` vs KB metadata `"Rice"`/`"Paddy"`/`"Corn"` | Alias map + `$in` incl. `"General"` |
| 3 | "Why are rice leaves yellow?", "improve soil health?" refused as off-topic | Keyword classifier had no such English words | Added specific English words to `advisory` |
| 4 | Tamil `மஞ்சளாக` refused | Keyword `மஞ்சள்` doesn't match the inflected form | Added stem `மஞ்சள`, `ஊட்டச்சத்து`, `வளம்`. (My first attempt with `இலை/நெல்/மண்` broke an existing disease-intent test: caught by the suite and narrowed) |
| 5 | Unsourced answers flagged `grounded: true` | formatter set `grounded = not fallback`; any citation (even weather) counted as "verified" for knowledge questions | `grounded` now = evidence-backed only; knowledge/dosage need RAG citations; new `grounding_mode` field in the response and SSE `completed` event |
| 6 | Citations unrelated to the question ("Site Map" for photosynthesis) | bge-m3 gives 0.45-0.5 for anything in this small corpus | English: lexical gate (≥2 question terms in chunk) + cosine ≥ 0.45 over a wider candidate pool; Tamil: cosine ≥ 0.48 (calibrated on only 4 samples) |
| 7 | **Invented pesticide dose**: "chlorpyrifos 20 ml/L … based on TNAU", marked verified with 6 sources | Dose check covered few units; existing numeric check only matched a bare number | New dose guard, **all grounding modes**: dose + unit must appear in the evidence text (bare "2" no longer validates "2 ml"); also dose-phrased questions classified as `PESTICIDE_DOSAGE` |
| 8 | English requests answered in Tamil | Mode instructions are Tamil; no language rule in user turn | Explicit language rule appended to the user turn |
| 9 | Garbled Tamil | `repeat_penalty: 1.2` | 1.05 (temperature 0.2); checked directly against local Ollama |
| label | Policy "label as GENERAL GUIDANCE" | none existed | Answer is prefixed "General guidance (not from TNAU sources): " / `பொது வழிகாட்டுதல் (TNAU ஆதாரம் இல்லாமல்): ` when no verified evidence |

Files modified: `backend/{cognitive/llm/service.py, shared/settings.py, shared/models/response.py, conversation/routes/{voice,health,conversation}.py, knowledge/rag/engine.py, tools/agents/rag_agent.py, cognitive/graph/nodes/{formatter,grounding_validator,intent,prompt_builder,safety_validator}.py}`, `.env.example`, `requirements-voice.txt`, `tests/api/{test_settings.py (replaced the claude-key test with provider-rejection tests), test_zero_cost_local_ai.py (new)}`. **Authentication/OTP/JWT, disease inference/checkpoints, M4, DB schema/records, ChromaDB data: untouched.**

## 3. Tests
| Run | Result |
|---|---|
| Full backend suite (against a **copy** of Chroma; live store never opened by tests) | **321 passed, 0 failed, 0 skipped** (was 269 collected earlier; PostgreSQL/Redis/Ollama now running so the 7 DB tests also ran) |
| New `test_zero_cost_local_ai.py` | 44 tests: no banned AI hosts/SDK imports in code; no paid packages in requirements; `.env.example` clean; settings reject claude/openai/gemini/anthropic in dev and production; LLM service makes zero network calls for external providers; Ollama outage → local error and only localhost contacted; whole `/conversation` with Ollama **and** external data down never touches a paid host; voice STT/TTS never call out; RAG agent regression; crop-filter aliases; **live local Ollama generation**; **real Chroma copy**: citations are real chunks from the local collection; unrelated question → no citations; dosage guard (every mode, number+unit); General-guidance labels (EN/TA); intent regressions |
| Live Chroma after everything | 520 rows, fingerprint identical to Sprint 1 (`16925b95…`); PostgreSQL farmers 6 / diary 31 unchanged |

## 4. Live assistant after repair (local Ollama qwen2.5:7b + local Chroma, `127.0.0.1`)
| Question | Time | Mode | Sources | Result |
|---|---|---|---|---|
| What is photosynthesis? | 38 s | general_guidance (not grounded) | 0 | Correct, coherent, labelled |
| What is NPK fertilizer? | 22-36 s | grounded_verified once; fell back once | 2 | Correct definition; in one run the model added example ratios not in evidence and the numeric guard **correctly blocked** it → safe fallback. Behaviour varies run to run |
| Why are rice leaves turning yellow? | 29 s | general_guidance | 0 | Sensible (nutrient/water/pest), labelled |
| How can I improve soil health? | 22 s | grounded_verified | 6 | Reasonable; sources only loosely relevant |
| Importance of crop rotation | 21 s | grounded_verified | 1 | Correct; one weakly relevant source |
| chlorpyrifos dose ml/L on paddy | 31 s | fallback | 0 | **Blocked: no invented dose** (before: "20 ml per liter") |
| Tamil: yellow rice leaves | 30 s | grounded_verified | 6 | Readable but uninformative ("information not available, tell me crop age…"); honest, not a hallucination |
| Tamil: NPK | 30 s | grounded_verified | 6 | Readable, low value |
Ollama was called locally for every non-fallback answer (confirmed from its log). No external host was contacted.

## 5. Honest limitations (review risks)
1. **Tamil quality from qwen2.5:7b is weak.** It does not follow evidence well in Tamil; answers are readable after the fix but often content-free. This is a model limit, not a setting. Options that keep the policy: a larger **local** model (e.g. a 14B variant; needs a download and RAM: not done, your call), or answer Tamil from tool-driven templates (weather, market, schemes) and keep free-text Tamil for simple questions.
2. **The knowledge base is coarse** (520 page-size chunks, English only, many unrelated pages). Citations are now real and filtered, but "verified" does not mean *good*. Fixing this means re-chunking/re-ingesting, which I was told not to do. This is the biggest lever for answer quality.
3. **Dose guard checks the figure exists in the evidence, not that it belongs to the same chemical.** It stops invented numbers; it can't catch a real number attached to the wrong chemical.
4. **Latency 20-40 s** per answer on this Mac; poor for voice. Smaller model (qwen2.5:3b is already installed) or shorter answers are the trade-offs.
5. Thresholds (0.45 / 0.48) come from a handful of samples; build a labelled benchmark before trusting them.
6. Answers still vary run to run (temperature, KV state).
7. The backend is now started on **127.0.0.1** (not 0.0.0.0), which works with `adb reverse`.

## 6. Constraints honoured
No paid/external AI API used or added; no farmer data sent anywhere; no model downloaded; no training; M4 untouched; no Git staging/commit/push; no re-ingest or deletion of Chroma data (read-only; tests used copies); `.env` not edited.

**Backup note:** the earlier addendum archive predates these edits. These 17 files exist only on this disk; refresh the addendum archive before the SSD copy.
