# FP-004 — RAG Quality

**Status:** `PLANNING`
**Sprint:** Sprint-004
**Milestone:** M-07 — RAG Quality

---

## 1. Requirement
The current advisory RAG returns chunks regardless of relevance score. Low-score chunks make the LLM generate poor answers. This FP improves retrieval quality: reject low-confidence chunks, show the source URL with every answer, use the farmer's district to filter relevant TNAU content, and always show a Tamil fallback when no relevant content is found.

---

## 2. User Story
```
As a Tamil Nadu farmer using UZHAVAN AI
I want every answer to come with its TNAU source
So that I can trust the advice and verify it if needed
```

---

## 3. Acceptance Criteria

- [ ] AC-1: Chunks with cosine score < 0.35 are excluded from LLM context
- [ ] AC-2: Every advisory answer includes at least one source URL (or Tamil fallback if none found)
- [ ] AC-3: When farm_id provided in /chat, retrieval filters by farmer's district first
- [ ] AC-4: "No results found" → Tamil message (not LLM hallucination): "மன்னிக்கவும்..."
- [ ] AC-5: Confidence band shown in Flutter UI: green (> 0.7), yellow (0.5-0.7), orange (0.35-0.5)
- [ ] AC-6: /search endpoint returns scores visible to admins for debugging

---

## 4. API Contract
```
POST /ask (updated)
Response now includes:
{
  "answer":        "...",
  "sources":       [{ "url": "...", "score": 0.82, "excerpt": "...", "category": "Plant Protection" }],
  "chunks_used":   4,
  "min_score":     0.35,
  "retrieval_ms":  145
}
```

---

## 5. Database Changes
```
No new tables.
knowledge_chunks.embedded_at updated when re-embedded.
```

---

## 6. AI / RAG Changes
```
rag_engine.py:
  - Add score threshold filter (> 0.35 only)
  - Add district metadata filter when farm context provided
  - Return retrieval_ms timing

advisory/main.py:
  - Pass farm's district to retrieval when farm_id in JWT
  - Include sources in response
  - Tamil fallback when chunks=0

embed_chunks.py:
  - Add --min-words 50 flag (skip very short chunks)
```

---

## 7. Flutter Screens
```
Modified:
  - ChatScreen: source URL shown below each AI message
  - Source confidence indicator: colored dot (green/yellow/orange)
  - Tapping source URL → opens browser to TNAU page
```

---

## 8. Tests
```
Unit:
  - test_score_threshold_filters_low_chunks()
  - test_district_filter_applied_when_farm_provided()

Integration:
  - test_advisory_includes_sources()
  - test_no_chunks_returns_tamil_fallback()
  - test_retrieval_ms_included_in_response()
Coverage: 75%
```

---

## 9. Security Review
```
No new security surface.
Source URLs displayed as tappable links — validate they are agritech.tnau.ac.in or known safe domains.
```

---

## 10. Documentation
```
README: Update /ask response format with sources
Data dictionary: No change
Changelog: Yes
```

---

## 11. Demo Checklist
```
[ ] Ask about rice blast → answer cites TNAU URL
[ ] Ask about something not in TNAU → Tamil fallback (no hallucination)
[ ] Source confidence indicator visible in Flutter UI
[ ] Tap source → TNAU page opens in browser
[ ] Retrieval ms logged for monitoring
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
