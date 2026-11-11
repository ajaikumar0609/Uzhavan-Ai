# FP-005 — Disease Detection Flutter Integration

**Status:** `PLANNING`
**Sprint:** Sprint-004
**Milestone:** M-08 — Disease Camera Flow
**Owner:** TL Agent

---

## 1. Requirement
A Tamil Nadu farmer spots unusual spots on their crop leaves. They open UZHAVAN AI, tap the camera icon, photograph the affected leaf, and within 5 seconds see the disease name in Tamil, the severity level, and exactly what to spray (product name, dose, dilution) — all sourced from TNAU. If confidence is below 40%, the app says "Uncertain — show this photo to your agriculture officer" in Tamil.

---

## 2. User Story
```
As a Tamil Nadu farmer
I want to photograph a diseased plant leaf
So that I immediately know what disease it is and how to treat it in Tamil
```

---

## 3. Acceptance Criteria

- [ ] AC-1: Given a photo of a diseased leaf, when uploaded, then disease name appears in Tamil within 5 seconds
- [ ] AC-2: Given confidence < 0.40, when result shown, then Tamil message: "நிச்சயமில்லை — உங்கள் வேளாண் அலுவலரிடம் இந்த படத்தைக் காட்டுங்கள்"
- [ ] AC-3: Given a healthy plant photo, when result shown, then Tamil message: "இலை ஆரோக்கியமாக இருக்கிறது" with preventive care tips
- [ ] AC-4: Given a disease detected, treatment screen shows: chemical name + dose + biological alternative + cultural practice (all in Tamil)
- [ ] AC-5: Given image > 500 KB, when selected, then app compresses before upload (user sees no delay)
- [ ] AC-6: Given no internet, when photo taken, then Tamil message: "இணைப்பு இல்லை — Wi-Fi அல்லது மொபைல் டேட்டா இயக்கவும்"

**Out of Scope (v1):**
- Batch photo upload (single leaf only)
- History of past diagnoses (Sprint 5)
- Satellite-linked disease mapping
- Auto-detection of crop type (manual crop selection in v1)

---

## 4. API Contract
```
POST /predict          (existing — port 8001)
POST /batch-predict    (existing — port 8001)

Response format (with Tamil additions):
{
  "disease": "Tomato With Early Blight",
  "disease_tamil": "தக்காளி ஆரம்ப கருகல் நோய்",
  "crop": "Tomato",
  "confidence": 0.87,
  "severity": "High",
  "tnau_guidance": {
    "chemical":    "மாங்கோஸேப் 75 WP @ 2.5 g/L ...",
    "biological":  "ட்ரைக்கோடர்மா விரிடி ...",
    "cultural":    "நேர்மாறு பயிர் சுழற்சி ..."
  }
}
```
*Note: Tamil translations to be added to tnau_guidance.py by Vision Agent*

---

## 5. Database Changes
```
New tables:   disease_scans (farmer_id, image_hash, disease, confidence, created_at)
              — images NOT stored, only hash + result
Migration:    004_disease_scans.sql
Notes:        Images discarded after inference (privacy)
```

---

## 6. AI / RAG Changes
```
Vision Agent: Add confidence threshold 0.40 → "uncertain" response
Vision Agent: Add Tamil disease names to tnau_guidance.py
RAG Agent:    No change (treatment guidance already in tnau_guidance.py)
```

---

## 7. Flutter Screens
```
New screens:
  - DiseaseHomeScreen     (camera button + recent scan history placeholder)
  - CameraScreen          (full-screen camera with capture button)
  - AnalyzingScreen       (loading animation with Tamil farming tip)
  - DiseaseResultScreen   (disease name in Tamil + severity chip + treatment accordion)
  - TreatmentDetailScreen (chemical / biological / cultural tabs — all Tamil)

Navigation:
  HomeScreen → DiseaseHomeScreen → CameraScreen → AnalyzingScreen → DiseaseResultScreen
                                                                    → TreatmentDetailScreen

Key UI notes:
  - Camera button: 80dp circular, high-contrast green
  - Severity chip: red (Very High), orange (High), yellow (Medium), green (None)
  - Treatment accordion: expandable sections (அரசாங்க வழிகாட்டுதல் / இயற்கை முறை / பண்ணை முறை)
```

---

## 8. Tests
```
Unit:
  - test_confidence_threshold_uncertain()
  - test_image_compression_under_500kb()

Integration:
  - test_disease_detection_end_to_end()
  - test_batch_predict_endpoint()
  - test_low_confidence_response()
  - test_healthy_plant_response()

Flutter widget tests:
  - test_camera_screen_renders()
  - test_result_screen_shows_tamil_name()

Coverage target: 75%
```

---

## 9. Security Review
```
Auth required:    Optional in v1 (logged if authenticated)
File upload:      Yes — MIME validation (image/jpeg, image/png only), max 10 MB before compression
SQL queries:      Parameterized (disease_scans inserts)
Prompt injection: N/A (no LLM in disease flow)
Privacy:          Images NOT stored — only hash + result stored
Verdict:          Pending Security Agent review
```

---

## 10. Documentation
```
README updated:    Yes (disease detection section)
API docs:          Disease API endpoint descriptions updated
Changelog:         Yes
```

---

## 11. Demo Checklist
```
[ ] Murugan photographs a tomato leaf with spots
[ ] Disease detected within 5 seconds: "தக்காளி ஆரம்ப கருகல் நோய்"
[ ] Severity shown: High (சிவப்பு சிப்)
[ ] Treatment shown in Tamil (chemical + biological + cultural)
[ ] Compressed image (< 500 KB) confirmed in network log
[ ] Low-confidence test: uploads blurry image → uncertainty message in Tamil
[ ] Offline test: airplane mode → Tamil error message shown
[ ] Works on Redmi 10 (low-end test device)
```

---

## 12. Release Notes
```
## FP-005 — Disease Detection (v0.4.0)

What farmers can now do:
- Photograph a diseased plant leaf
- See the disease name in Tamil within 5 seconds
- Get official TNAU treatment guidance — what to spray, how much, safe alternatives

How to use:
- Tap the camera icon → photograph the affected leaf → wait 5 seconds → read your result
```

---

## Sign-offs

| Agent | Sign-off | Date |
|-------|----------|------|
| PM Agent | [ ] | |
| SA Agent | [ ] | |
| Testing Agent | [ ] | |
| Security Agent | [ ] | |
| Documentation Agent | [ ] | |
| Standards Agent | [ ] | |
| **Master Agent** | [ ] | |
