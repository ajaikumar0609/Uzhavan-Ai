# UZHAVAN AI — API Integration Status
**Date:** 2026-09-26 · Single source of truth: `docs/architecture/API_CONTRACT_M06.md`

---

## Backend Endpoints — Integration Status

### Health / Meta
| Endpoint | Status | Flutter screen |
|----------|--------|---------------|
| `GET /health` | ✅ Live | App startup check |
| `GET /api/meta/districts` | ✅ Live (38 TN districts) | Profile / Farm district picker |
| `GET /api/meta/crops` | ✅ Live | Farm crop picker, Market |
| `GET /api/meta/enums` | ✅ Live | Farm form dropdowns |
| `GET /health/config` | ✅ Live (dev/test only; 404 in prod) | Settings → About (debug) |

### Auth (FP-008)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `POST /api/auth/send-otp` | ✅ Live | HMAC-SHA256, 5 min, 3/hr limit |
| `POST /api/auth/verify-otp` | ✅ Live | Returns access + refresh tokens |
| `POST /api/auth/refresh` | ✅ Live | Rotation; reuse → revoke all |
| `POST /api/auth/logout` | ✅ Live | Revokes refresh token |

### Profile + Farms (FP-009)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/farmer/profile` | ✅ Live | Envelope `{data, meta}` |
| `PUT /api/farmer/profile` | ✅ Live | Partial update |
| `GET /api/farms` | ✅ Live | Envelope |
| `POST /api/farms` | ✅ Live | **Bare Farm object** (no envelope) — confirmed live |
| `PUT /api/farms/{id}` | ✅ Live | **Bare Farm object** — confirmed live |
| `DELETE /api/farms/{id}` | ✅ Live | 204 |

### Weather (FP-010)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/weather/current` | ✅ Live | Open-Meteo, 30 min cache, IST observed_at |
| `GET /api/weather/forecast` | ✅ Live | 7-day, **`timezone=Asia/Kolkata`** (D2 fix applied) |
| `GET /api/weather/advisories` | ✅ Live | TNAU CPG rules; empty list when none fire |

**Confirmed deviations from contract draft:**
- `meta.observed_at` is **null** on forecast (Open-Meteo does not provide issue time); Flutter shows "model time not provided"
- `condition.ta` is always **null** (no verified Tamil WMO translations); Flutter shows English condition

### Market (FP-011)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/market/commodities` | ✅ Live | 14 commodities |
| `GET /api/market/markets` | ✅ Live | Filtered by district |
| `GET /api/market/latest` | ✅ Live | Stale chip when >7 days old |
| `GET /api/market/trend` | ✅ Live | Per variety (NOT averaged) |

**Available commodities:** banana, black_gram, brinjal, coconut, copra, cotton, green_gram, groundnut, maize, onion, paddy, rice, tomato, turmeric. Chilli / sugarcane / vegetables / other return empty — Flutter shows "no data for this crop" without making a call.

### Schemes (FP-012)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/schemes` | ✅ Live | 136 schemes, search + filter |
| `GET /api/schemes/{id}` | ✅ Live | Full detail |
| `GET /api/schemes/{id}/eligibility` | ✅ Live | 16 rules; cannot_determine when no rule |

**Confirmed deviation:** `source_documents` are internal file paths — Flutter never shows them; only `official_url` (http/https only) is shown.

### Soil (FP-014)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/soil` | ✅ Live | 3 sections: regional / estimated / measured |
| `POST /api/soil/tests` | ✅ Live | Farmer-entered, range-validated |
| `GET /api/soil/tests` | ✅ Live | Per farm |

**Confirmed deviations (C1, C2):**
- `nutrient_status.parameters[].categories` has keys `{category, pct, samples}` not `{low_pct, medium_pct, high_pct}` — Flutter reads `category` (C1 fix)
- `estimated.units` is a map keyed by value name — Flutter uses `data.estimated.units[key]` (C2 fix)

### Diary (FP-013)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/diary` | ✅ Live | Returns `kind: note\|observation\|expense\|income\|question\|scan` |
| `POST /api/diary` | ✅ Live | Farmer manual entries |

Auto-log: `question` entries posted by conversation route; `scan` entries posted by disease scan route.

### Assistant (FP-015)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `POST /conversation` | ✅ Live | SSE stream, 10-node cognitive graph |
| `POST /voice/stt` | ✅ Live | Optional (client uses on-device STT) |
| `POST /voice/tts` | ✅ Live | Optional (client uses on-device TTS) |

SSE event sequence: `session_started → intent_detected → planning → tool_complete → evidence_ready → grounding → reasoning → [token] → [sources] → completed`

`sources` event emitted only when TNAU/RAG evidence actually retrieved (second guard in formatter).  
`completed.grounded: bool` reflects whether numeric/factual claims are backed by evidence.

### Disease (FP-018)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `POST /api/disease/scan` | ✅ 503 model_unavailable | `DISEASE_MODEL_APPROVED=false` (default); model service never called |

### Satellite (FP-019)
| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/satellite/status` | ✅ Live | `{available:false, reason:"under_validation", gates:{...}}` |

---

## Flutter ↔ Backend: Error Code Mapping

| HTTP / detail code | Flutter treatment |
|--------------------|-------------------|
| Network error | UNAVAILABLE state |
| 404 | UNAVAILABLE state |
| 503 model_unavailable | UNAVAILABLE state (Scan screen) |
| 503 service_unavailable | UNAVAILABLE state |
| 500 | ERROR state (no stack trace shown) |
| 429 rate_limited | rateLimited state (Retry-After respected) |
| 400 / 410 | validation / OTP-specific screens |
| 401 unauthenticated | Token refresh attempted; if fails → logout |
