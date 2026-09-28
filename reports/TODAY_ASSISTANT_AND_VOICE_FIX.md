# UZHAVAN AI SHOWCASE — ASSISTANT + TAMIL VOICE + DISEASE UX REPORT

**Date:** 2026-09-26  
**Status:** ✅ Complete & Verified End-to-End  
**Platform:** FastAPI (`127.0.0.1:8000`) + Ollama (`127.0.0.1:11434`) + M4 Server (`127.0.0.1:8001`) + Flutter Android Client (`uzhavan_flutter`)

---

## 1. Local Ollama LLM Setup

- **Model Used:** `qwen2.5:7b-instruct` (Ollama 0.5.x on Apple Silicon)
- **Local Endpoint:** `http://127.0.0.1:11434`
- **Network Boundary:** Flutter Android client connects strictly to FastAPI port 8000 via ADB reverse (`tcp:8000`). Ollama is never directly contacted by the phone.
- **Backend Configuration (`.env` & `settings.py`):**
  - `LLM_PROVIDER=ollama`
  - `OLLAMA_BASE_URL=http://127.0.0.1:11434`
  - `OLLAMA_URL=http://localhost:11434`
  - `OLLAMA_MODEL=qwen2.5:7b-instruct`
- **Generation Parameters:**
  - `temperature: 0.3`
  - `top_p: 0.9`
  - `repeat_penalty: 1.2`
  - `num_predict: 256`

---

## 2. Assistant Queries & Grounded Results

The generic fallback ("Sorry, the information needed to answer this is not available right now") has been completely resolved. Live Open-Meteo weather data and M4 disease scan contexts are fused into the cognitive graph and grounded before LLM generation.

### Test 1 — English Weather
- **Input Question:** `"Will it rain this week?"`
- **Intent Detected:** `weather` (confidence: 0.95, days: 7, district: "Thanjavur")
- **Tools Run:** `weather.current_weather`, `weather.forecast`, `weather.rain_alert` (3 succeeded, 0 failed)
- **Grounded:** `true` (citations: 8, confidence: 0.91, fallback: `false`)
- **LLM Output:**
  > "This week in Thanjavur, there is no forecast of rainfall for 2026-09-26. However, starting from September 27th onwards, light drizzle or slight rain showers are expected with increasing probability.  
  > Based on the weather forecasts:  
  > - On 2026-09-27: There's a possibility of very light rainfall.  
  > - From 2026-09-28 to 2026-10-02, there is an increased chance of rain with probabilities ranging from 76% on September 28th down to about 53%.  
  > For your crops, it might be beneficial to prepare for potential light rainfall starting next week. Keep your fields well-drained and monitor the weather closely.  
  > Actionable recommendation: Check the soil drainage before any expected showers this coming week."

### Test 2 — Tamil Weather
- **Input Question:** `"இந்த வாரம் மழை வருமா?"`
- **Intent Detected:** `weather` (confidence: 0.95, days: 7, district: "Thanjavur")
- **Tools Run:** `weather.current_weather`, `weather.forecast`, `weather.rain_alert`
- **Grounded:** `true` (citations: 8, confidence: 0.91, fallback: `false`)
- **LLM Output (Natural Tamil):**
  > "2026-09-26 இன்று தஞ்சாவூரில் மழை வராது. 27ம் நாள் லேசான சாரல் (0.4 mm) வாய்ப்பு உள்ளது. 28, 29ம் நாட்களில் சாரல் மழையும் (0.6 mm), 30ம் நாள் மிதமான மழையும் (6.6 mm) எதிர்பார்க்கப்படுகிறது. பயிர்களுக்கு தேவையான வடிகால் வசதிகளை முன்கூட்டியே தயார் செய்யவும்."

### Test 3 — Disease Result Explanation in Tamil
- **Input Question:** `"இந்த இலைக்கு என்ன நோய் என்று மாடல் சொல்கிறது?"`
- **Context Supplied:** Banana Sigatoka Leaf Spot (M4 v1 EfficientNetV2-S, 93.4% confidence, demo mode)
- **Grounded:** `true` (citation: `UZHAVAN M4 v1 Research Checkpoint`, confidence: 0.90, fallback: `false`)
- **LLM Output (Tamil Grounded Advisory):**
  > "இந்த இலைக்கு Sigatoka Leaf Spot என்னும் நோயை மாடல் கண்டறிந்துள்ளது (கணிப்பு நம்பிக்கை: 93.4%). இது ஆய்வக மாதிரி (M4 v1 Research Demo) கணிப்பாகும்; கள உற்பத்திக்கான சான்றளிக்கப்படவில்லை. இலைகளில் மஞ்சள் நிற விளிம்புகளுடன் கூடிய பழுப்பு நிறப் புள்ளிகள் காணப்படும். வேளாண் அலுவலர் அல்லது TNAU பரிந்துரைப்படி மேங்கோசெப் அல்லது காப்பர் பூஞ்சாணக்கொல்லி தெளிக்கலாம்."

---

## 3. Text-to-Speech (TTS) Implementation

### Dynamic Language Detection
- Rather than relying on the UI locale, `_SpeakButton` in `assistant_screen.dart` inspects the message text using `RegExp(r'[\u0B80-\u0BFF]')`:
  - Contains Tamil Unicode characters → **`ta-IN`**
  - English characters only → **`en-IN`**

### Settings & Audio Engine
- **Engine Priority:** `com.google.android.tts` / `com.samsung.SMT`
- **Speech Settings:**
  - Speech Rate: `0.5` (natural pacing)
  - Pitch: `1.0`
  - Volume: `1.0`
- **Lifecycle Management:**
  - Calls `stop()` before initiating new speech.
  - Tapping speaker while speaking toggles playback off.
- **Logcat Verification:**
  ```text
  GoogleTTSServiceImpl: currentLocale = ta-IN
  GoogleTTSServiceImpl: For default lang ta-in is name ta-IN-language (ta-in-x-tac-server)
  GoogleTTSServiceImpl: Synthesis request for locale tam-IND and name ta-IN-language
  GoogleTTSServiceImpl: TTS dispatch: ta-in-x-tac-server
  ```
- **Fallback UI:** If the device lacks offline Tamil voice data, a SnackBar gracefully guides the presenter to Android TTS settings (`Settings → Accessibility → Text-to-speech output → Install voice data`).

---

## 4. Disease Scan UX & Real M4 Inference

- **Frozen Checkpoint:** `uzhavan_ml/runs_m4/UZ-M4-v1.0-a898475e-s1/checkpoint_best.pt`
- **Architecture:** `EfficientNetV2-S` (Multi-crop multi-head)
- **Showcase Image:** `demo_banana_sigatoka.png` (verified real leaf photo)
- **Standalone Verification Output:**
  ```text
  Crop:               banana
  Input Image:        demo_banana_sigatoka.png
  Predicted Class:    banana__sigatoka_leaf_spot
  Confidence:         93.39% (0.9339)
  Top-3 Probabilities:
    1. banana__sigatoka_leaf_spot       :  93.39%
    2. banana__cordana_leaf_spot        :   1.23%
    3. banana__moko_wilt                :   0.99%
  Inference Latency:  38.78 ms
  ```
- **Safety Disclaimers Retained:**
  - `"M4 v1 RESEARCH DEMO"`
  - `"NOT PRODUCTION CERTIFIED"`
- **Scan-to-Assistant Flow:** Added button `"உதவியாளரிடம் இந்த முடிவு பற்றி கேட்கவும்"` ("Ask Assistant about this result") under the M4 demo result card. Clicking it injects the scan metadata into the assistant session and navigates directly to `/assistant`.

---

## 5. Files Changed

1. **`uzhavan_platform/backend/shared/settings.py`**
   - Added `OLLAMA_BASE_URL`, defaulted `OLLAMA_MODEL` to `qwen2.5:7b-instruct`.
2. **`uzhavan_platform/backend/shared/models/version.py`**
   - Set default LLM model name to `qwen2.5:7b-instruct`.
3. **`uzhavan_platform/backend/cognitive/llm/service.py`**
   - Configured Ollama chat generation options (`repeat_penalty: 1.2`, `top_p: 0.9`, `temperature: 0.3`, `num_predict: 256`).
4. **`uzhavan_platform/backend/shared/models/conversation.py`**
   - Added `disease_context: dict[str, Any] | None` to `ConversationState` TypedDict.
5. **`uzhavan_platform/backend/conversation/routes/conversation.py`**
   - Added `disease_context` to `ConversationRequest` and passed it into initial graph state.
   - Enhanced `_apply_farm` to resolve district from farm, farmer profile, or "Thanjavur".
6. **`uzhavan_platform/backend/cognitive/graph/nodes/intent.py`**
   - Added Tamil weather keywords (`வானிலை`, `வெதர்`, `மழை வருமா`, `மழை பெய்யுமா`, etc.).
   - Parsed time horizon ("வாரம்" → 7 days, "நாளை" → 2 days, "இன்று" → 1 day).
   - Extracted crop from `disease_context` when present.
7. **`uzhavan_platform/backend/cognitive/graph/nodes/evidence_fusion.py`**
   - Extracted human-readable weather summary string for `EvidenceBundle`.
   - Injected disease scan context and citation into evidence bundle.
8. **`uzhavan_platform/backend/cognitive/graph/nodes/formatter.py`**
   - Fixed missing `import logging`.
   - Added diagnostic logging for any fallback triggers.
9. **`uzhavan_flutter/lib/features/assistant/data/voice_services.dart`**
   - Improved `DeviceSpeaker` with rate, pitch, stop-before-speak, and language matching (`ta-IN`, `ta_IN`, `tam`).
10. **`uzhavan_flutter/lib/features/assistant/presentation/assistant_screen.dart`**
    - Dynamic language detection via Unicode regex (`[\u0B80-\u0BFF]`) for `_SpeakButton`.
    - Added missing voice SnackBar guidance.
11. **`uzhavan_flutter/lib/features/assistant/data/assistant_repository.dart` & `chat_controller.dart`**
    - Added `diseaseContext` support to API requests.
12. **`uzhavan_flutter/lib/features/scan/presentation/scan_screen.dart`**
    - Added "Ask Assistant about this result" button linking disease scan to Assistant.

---

## 6. Test Verification Summary

- **FastAPI / Python Tests:**
  - Command: `.venv/bin/pytest tests/api/ -q`
  - Result: **187 passed in 2.21s**
- **Flutter Unit & Widget Tests:**
  - Command: `flutter test`
  - Result: **145 passed** (0 failures)
- **Flutter Static Analysis:**
  - Command: `flutter analyze`
  - Result: **No issues found** (0 errors, 0 warnings)
- **M4 Standalone Real Inference:**
  - Verified on `demo_banana_sigatoka.png`: **Sigatoka Leaf Spot 93.39%**
- **End-to-End ADB Physical Reverse Setup:**
  - `adb reverse tcp:8000 tcp:8000` (FastAPI)
  - `adb reverse tcp:8001 tcp:8001` (M4 Inference Server)

---

## 7. Showcase Demo Instructions

1. **Verify Services:**
   - FastAPI: `http://127.0.0.1:8000/docs`
   - Ollama: `curl http://127.0.0.1:11434/api/tags`
   - M4 Server: `curl http://127.0.0.1:8001/health`
2. **Reverse Ports for Phone:**
   ```bash
   adb reverse tcp:8000 tcp:8000
   adb reverse tcp:8001 tcp:8001
   ```
3. **Demo Sequence:**
   - **Login:** Phone `9876543210`, OTP `123456`.
   - **Weather Question:** Tap Assistant tab → Tap `"இந்த வாரம் மழை பெய்யுமா?"` → View real 7-day weather answer in Tamil → Tap Speaker icon to hear Tamil TTS.
   - **English Assistant:** Ask `"Will it rain this week?"` → Receive English weather forecast → Tap Speaker icon to hear English TTS.
   - **Disease Scan:** Tap Scan tab → Select crop `வாழை` (Banana) → Upload `demo_banana_sigatoka.png` → View real M4 inference: `Sigatoka Leaf Spot (93.4%)` with `"M4 v1 RESEARCH DEMO — NOT PRODUCTION CERTIFIED"` badge.
   - **Disease Explanation:** Tap `"உதவியாளரிடம் இந்த முடிவு பற்றி கேட்கவும்"` → Assistant explains the prediction, states research demo status, and provides TNAU-grounded management advice in Tamil.
