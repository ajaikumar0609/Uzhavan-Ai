# UZHAVAN AI — Screen Flow

**Flutter navigation approach:** GoRouter with nested shell routes for bottom navigation.
**State:** JWT token stored in Flutter Secure Storage. Token validated on cold start.

---

## Flow 1 — App Launch (Cold Start)

### Text Description
1. App opens → Splash screen displays (logo + progress bar)
2. Token check (< 500ms from secure storage)
3. **Token valid and not expired** → navigate to Home
4. **No token or expired** → navigate to Phone Input

### Diagram
```
[App Launch]
      │
      ▼
[Splash Screen]
      │
      ├── (token valid) ──────────────────► [Home Screen]
      │
      └── (no token / expired) ──────────► [Phone Input Screen]
```

---

## Flow 2 — Onboarding (New User)

### Text Description
1. Phone Input: enter 10-digit number → tap "OTP அனுப்பு"
2. OTP Verify: enter 6-digit OTP → auto-submit on 6th digit
3. **New farmer** (`is_new_farmer: true`) → Profile Setup
4. Profile Setup: name + district + crop + language → "தொடரவும்"
5. Farm Setup: area + soil + irrigation → "முடித்தது" OR "பிறகு சேர்க்கலாம்" (skip)
6. Home Screen

### Diagram
```
[Phone Input]
      │
      ▼
[OTP Verify]
      │
      ├── (is_new_farmer = true) ─────────► [Profile Setup]
      │                                            │
      │                                            ▼
      │                                     [Farm Setup]
      │                                            │
      │                                ┌─── "முடித்தது"
      │                                │         │
      └── (existing farmer) ──────────┘         │
                                        │         │
                                        └─────────▼
                                          [Home Screen]
```

**Error flows within onboarding:**
```
[Phone Input] ──(invalid number)──► inline error, stay on screen
[Phone Input] ──(rate limited)───► "45 நிமிடம் பிறகு முயற்சிக்கவும்", stay
[OTP Verify]  ──(wrong OTP)──────► red boxes, "தவறான OTP", stay
[OTP Verify]  ──(expired)────────► "காலாவதி", resend button turns green
[OTP Verify]  ──(network error)──► "இணைப்பு இல்லை" snackbar, retry
```

---

## Flow 3 — Chat Flow

### Text Description
1. Home → tap "கேள்வி கேளுங்கள்" or Chat tab → Chat Screen (new session)
2. Type question → send → SSE stream begins → tokens appear
3. Sources card appears → suggestion chips appear → "done" event
4. Tap suggestion chip → pre-fills input and auto-sends
5. Tap source card → opens browser to TNAU URL
6. Tap history icon (top-right) OR History tab → Chat History Screen
7. Tap a session card → Chat Session Screen (read-only thread)

### Diagram
```
[Home Screen]
      │
      ├── tap "கேள்வி கேளுங்கள்" ──────────► [Chat Screen]
      │                                           │
      │                                    user types + sends
      │                                           │
      │                                    [Streaming response]
      │                                           │
      │                              ┌────────────┴──────────────────┐
      │                              │                               │
      │                      tap suggestion chip              tap source card
      │                              │                               │
      │                      auto-send question              [External Browser]
      │                              │                         (TNAU URL)
      │                              ▼
      │                      [Streaming response]
      │
      └── (Chat tab) ─────────────────────────────► [Chat Screen]

[Chat Screen]
      │
      └── (top-right history / History tab) ──────► [Chat History Screen]
                                                          │
                                                    tap session card
                                                          │
                                                          ▼
                                                   [Chat Session Screen]
                                                   (read-only, full thread)
```

**Error flows within chat:**
```
[Chat Screen] ──(rate limited)───► "அதிக செய்திகள். 1 நிமிடம் காத்திருங்கள்." snackbar
[Chat Screen] ──(no context)─────► Tamil fallback message inline (no error UI, just AI response)
[Chat Screen] ──(LLM unavailable)► "சேவை தற்காலிகமாக இல்லை. மீண்டும் முயற்சிக்கவும்." + retry button
[Chat Screen] ──(network loss)───► "இணைப்பு இல்லை" top banner; queued message shown with ⚠️
```

---

## Flow 4 — Disease Detection Flow

### Text Description
1. Home → tap "நோய் கண்டறி" OR Camera tab → Camera Screen
2. Aim at leaf → tap capture button → brief flash animation
3. Analyzing Screen (2–5 seconds with rotating Tamil tip)
4. Disease Result Screen
   - **Confidence ≥ 40%:** full result (disease name, severity, treatment accordion, source)
   - **Confidence < 40%:** uncertainty message + "வேளாண் அலுவலரிடம் காட்டுங்கள்"
5. Tap "AI-யிடம் மேலும் கேளுங்கள்" → Chat Screen with disease context pre-loaded
6. Tap source card → external browser
7. Back → Camera Screen (camera resets, ready for another photo)

### Diagram
```
[Home Screen]
      │
      ├── tap "நோய் கண்டறி" ─────────────► [Camera Screen]
      │                                           │
      └── (Camera tab) ────────────────────────────┘
                                                   │
                                           tap capture button
                                                   │
                                                   ▼
                                         [Analyzing Screen]
                                         (2-5 sec progress ring)
                                                   │
                                     ┌─────────────┴──────────────┐
                                     │                            │
                              confidence ≥ 0.40            confidence < 0.40
                                     │                            │
                                     ▼                            ▼
                            [Disease Result Screen]     [Low Confidence Screen]
                                     │                   "அலுவலரிடம் காட்டுங்கள்"
                                     │
                          ┌──────────┴──────────────┐
                          │                         │
                  tap "AI-யிடம்..."           tap source card
                          │                         │
                          ▼                         ▼
                [Chat Screen]              [External Browser]
                (disease context           (TNAU URL)
                 pre-loaded)
```

**Error flows:**
```
[Camera Screen] ──(no permission)────► "கேமரா அனுமதி தேவை" + settings button
[Analyzing Scr] ──(network error)────► "இணைப்பு இல்லை" + retry / cancel buttons
[Analyzing Scr] ──(service down)─────► "சேவை இல்லை. கொஞ்சம் பிறகு முயற்சிக்கவும்."
```

---

## Flow 5 — Weather Flow

### Text Description
1. Home → WeatherCard shows summary (district, temp, rain forecast, advisory)
2. Tap WeatherCard → Weather Detail Screen (7-day forecast, hourly, irrigation advice)
3. In Chat → ask weather question → weather answer rendered in chat bubble

### Diagram
```
[Home Screen]
      │
      └── tap WeatherCard ──────────────────► [Weather Detail Screen]
                                                      │
                                              (7-day forecast,
                                               irrigation advice,
                                               rain alert banner)
                                                      │
                                              tap "AI-யிடம்..."
                                                      │
                                                      ▼
                                              [Chat Screen]
                                              ("தாத்தாவூர் நாளை மழை?" pre-loaded)
```

---

## Flow 6 — Settings Flow

```
[Profile tab]
      │
      └── [Settings Screen]
                │
                ├── tap farm edit (✏️) ─────────► [Farm Edit Screen]
                │                                       │
                │                                 "சேமி" → back to Settings
                │
                ├── tap "+ நிலம் சேர்க்கவும்" ──► [Farm Setup Screen]
                │
                └── tap "வெளியேறு" ──────────────► [Confirm Dialog]
                                                          │
                                                   confirm → clear token
                                                          │
                                                          ▼
                                                   [Phone Input Screen]
```

---

## Flow 7 — No-Answer / Fallback State

This is a designed flow, not an error — it happens when RAG returns no relevant chunks.

```
[Chat Screen]
      │
      user asks question outside TNAU knowledge
      │
      ▼
[AI bubble shows:]
"மன்னிக்கவும், இந்த கேள்விக்கு TNAU
தரவுத்தளத்தில் பதில் கிடைக்கவில்லை.
உங்கள் வட்டார வேளாண் அலுவலர் (BAO)
அல்லது KVK-ஐ தொடர்பு கொள்ளுங்கள்."

[Below: grey info chip — "📞 BAO தொலைபேசி"]
(tappable → shows district BAO number from DB)
```

---

## Full App Screen Inventory

| Screen Name | Route | Tab | Stack Level |
|-------------|-------|-----|-------------|
| Splash | `/splash` | — | root |
| Phone Input | `/auth/phone` | — | modal stack |
| OTP Verify | `/auth/otp` | — | modal stack |
| Profile Setup | `/onboarding/profile` | — | modal stack |
| Farm Setup | `/onboarding/farm` | — | modal stack |
| Home | `/home` | 🏠 Home | L1 |
| Weather Detail | `/home/weather` | 🏠 Home | L2 |
| Chat | `/chat` | 💬 Chat | L1 |
| Chat History | `/chat/history` | 📋 History | L1 |
| Chat Session | `/chat/session/:id` | 📋 History | L2 |
| Camera | `/camera` | 📷 Camera | L1 |
| Disease Analyzing | `/camera/analyzing` | 📷 Camera | L2 |
| Disease Result | `/camera/result` | 📷 Camera | L3 |
| Settings | `/profile/settings` | 👤 Profile | L1 |
| Farm Edit | `/profile/farm/:id` | 👤 Profile | L2 |
