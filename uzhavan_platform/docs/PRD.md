# UZHAVAN AI — Product Requirements Document

**Version:** 1.0
**Date:** 2026-07-01
**Status:** Approved
**Owner:** Product Agent
**Audience:** All contributors, stakeholders, investors

> This is the business document. It answers *what* we are building and *why*.
> For *how*, see `docs/PROJECT_BIBLE.md`, `docs/architecture/`, and `docs/feature-packs/`.

---

## 1. Vision

**UZHAVAN AI is the AI operating system for Tamil Nadu agriculture.**

Every Tamil Nadu farmer — regardless of education, income, or smartphone literacy — deserves the same quality of agricultural guidance that a large commercial farm gets from a team of agronomists. UZHAVAN AI delivers that guidance: instant, grounded in official knowledge, in Tamil, at the cost of a data connection.

We are not building a chatbot. We are building infrastructure — the layer that sits between six million farming households and the knowledge they need to make better decisions every day.

---

## 2. Problem Statement

### Scale
Tamil Nadu has approximately **6.07 million farming households** (Agriculture Census 2020–21). Of these, **83% are small or marginal farmers** holding less than 2 hectares. These farmers grow rice, banana, cotton, sugarcane, groundnut, and dozens of other crops that feed both the state and national export markets.

### The Guidance Gap
A farmer making planting, irrigation, spraying, and harvesting decisions relies on:
- Personal experience (limited by what they've seen before)
- Neighbors' advice (often as uninformed as their own)
- Input dealers (incentivized to sell, not advise)
- Government extension officers (understaffed: 1 officer per ~800 farmers in most districts)

**The result:** Decisions are made with inadequate information. Wrong irrigation timing reduces yield. Missed pest identification turns a manageable infestation into a crop loss. Wrong fertilizer dosage wastes money and harms soil. In a bad kharif season, these errors cost a farmer months of income.

### Why Existing Solutions Fail Tamil Nadu Farmers
- Government portals (Kisan Suvidha, TNAU website) are in English and require browser navigation
- Agri-tech platforms (AgroStar, DeHaat) focus on Hindi-belt markets; Tamil content is thin
- General AI assistants (ChatGPT, Gemini) hallucinate crop recommendations without citing sources
- SMS-based services provide generic alerts, not personalized farm-level advice

### The Opportunity
The same farmer who has no access to an agronomist:
- Carries a ₹8,000–₹15,000 Android smartphone
- Spends 3–4 hours/day on WhatsApp and YouTube (in Tamil)
- Trusts TNAU as the authority on agriculture
- Has Jio or BSNL 4G coverage for most of the working day

**UZHAVAN AI closes this gap.** It delivers TNAU-grounded, Tamil-first, personalized agricultural guidance through a mobile interface Murugan can use without training.

---

## 3. Target Users

### Primary: Small and Marginal Tamil Nadu Farmers

| Attribute | Profile |
|-----------|---------|
| Geography | Tamil Nadu (38 districts); primarily rural and peri-urban |
| Farm size | 0.1 – 2.0 hectares (small/marginal) |
| Crops | Paddy, banana, cotton, sugarcane, groundnut, vegetables, pulses |
| Language | Tamil (first); basic English reading only |
| Device | Low-end Android (Redmi, Samsung Galaxy A-series, LAVA); 2–4 GB RAM |
| Connectivity | Jio/BSNL 4G; intermittent; limited data budget |
| Tech comfort | WhatsApp daily; camera use; voice calls; rarely types long text |
| Income | ₹50,000–₹2,00,000 annual farm income |
| Decision frequency | 3–5 major decisions/week during growing season |

### Secondary: Agricultural Extension Officers
Government officers managing 500–1,000 farmers. Use case: quick reference during field visits; escalation tool when farmer query exceeds officer's expertise.

### Tertiary (Post-MVP): Government Administrators
District Collectors, Agriculture Department officials. Use case: district-level dashboards showing crop health, pest alerts, scheme uptake.

---

## 4. Personas

### Persona 1 — Murugan (Primary Persona)

> "I know paddy. But I don't know if tomorrow's rain will ruin my spray."

| Field | Detail |
|-------|--------|
| Age | 42 |
| Location | Papanasam block, Thanjavur district |
| Farm | 1.8 hectares — 1.2 ha paddy (Samba season), 0.6 ha banana (Nendran) |
| Device | Redmi 10 (3 GB RAM, Helio G85, Android 11) |
| Connectivity | Jio 4G; drops to 3G in the fields; no WiFi at home |
| Language | Tamil — reads Tamil script fluently; basic English (numbers, product names) |
| Tech use | WhatsApp (sends voice notes); YouTube (farming videos); calls his input dealer |
| Pain points | Doesn't know when to irrigate around monsoon rains; misidentifies pests until they spread; misses government scheme deadlines |
| Goals | Maximize paddy yield; reduce chemical spend; know about PM-Kisan installments |
| Behavior | Checks phone 3–4 times/day; rarely types long sentences; prefers voice and camera |

**The Murugan Test:** If Murugan cannot use a feature on his first try, the feature is not ready.

---

### Persona 2 — Lakshmi

> "I saw spots on my banana leaves. By the time I got an answer, half the plants were affected."

| Field | Detail |
|-------|--------|
| Age | 38 |
| Location | Pollachi block, Coimbatore district |
| Farm | 1.2 hectares banana (Grand Naine variety) |
| Device | Samsung Galaxy A14 (4 GB RAM, Android 13) |
| Connectivity | BSNL 4G; good signal near home, weak in far fields |
| Language | Tamil first; reads English product labels |
| Tech use | WhatsApp Power User; sends and receives photos frequently; part of a women's SHG group chat |
| Pain points | Disease identification is slow (nearest KVK is 40 km away); doesn't know organic alternatives to pesticides; worries about residue affecting export quality |
| Goals | Keep banana plants disease-free; find organic treatment options; check if her bananas qualify for GI export certification |
| Behavior | Photographs her plants regularly; shares on WhatsApp groups for advice; acts quickly on visual symptoms |

**Lakshmi's primary flow:** Camera → disease detection → Tamil treatment recommendation with chemical + organic options → nearby scheme for subsidized bio-inputs.

---

### Persona 3 — Selvam

> "Every year I guess what to plant. Last year I planted cotton when everyone else planted groundnut and made more."

| Field | Detail |
|-------|--------|
| Age | 55 |
| Location | Sholavandan block, Madurai district |
| Farm | 3.0 hectares (medium farmer); red loam soil; well irrigation |
| Device | LAVA Agni 2 (4 GB RAM, Android 12) — bought by son |
| Connectivity | Jio 4G; moderate signal |
| Language | Tamil; uses son to read English content |
| Tech use | Basic — calls, WhatsApp (voice only), no social media |
| Pain points | Crop selection before sowing season is pure guesswork; doesn't track market prices; doesn't know government MSP announcements |
| Goals | Choose the most profitable crop for the upcoming season; reduce risk of price crash at harvest |
| Behavior | Makes big decisions once per season; consults older farmers in the village; skeptical of new technology until he sees proof |

**Selvam's primary flow:** Crop recommendation → weather + market + soil → profit estimate → government MSP/scheme crosscheck → decision.

---

## 5. User Journey

### Stage 1: Discovery
- Hears about UZHAVAN AI from another farmer, village WhatsApp group, or KVK demonstration
- Downloads app from Play Store (target: free, < 30 MB APK size)
- Sees Tamil language UI on first launch — no English required

### Stage 2: Onboarding (< 2 minutes)
- Enters mobile number → receives OTP → verifies
- Sets name, district, primary crop in Tamil
- Optionally adds farm: area, soil type, irrigation source
- Sees Home screen with weather card for their district

### Stage 3: First Question
- Taps chat → types or speaks first question in Tamil
- Receives answer within 8 seconds with TNAU citation
- Sees source: "மூலம்: TNAU நெல் சாகுபடி கையேடு"
- Outcome: either acts on advice immediately, or asks follow-up

### Stage 4: Disease Detection (Lakshmi flow)
- Taps camera icon on Home screen
- Photographs affected leaf
- Sees disease name in Tamil within 5 seconds
- Views chemical + organic treatment options
- Optionally: checks linked government scheme for bio-input subsidy

### Stage 5: Regular Use (Week 2–4)
- Opens app during morning irrigation decisions
- Checks weather card → asks irrigation question if rain expected
- Receives proactive alerts (rain warning, pest season approaching)
- Builds trust as advice proves accurate

### Stage 6: Trust and Habit (Month 2+)
- UZHAVAN AI becomes first reference point, not last resort
- Farmer shares app with other farmers in the village
- AI memory personalizes advice over time (farm history, past questions)
- Farmer provides outcome feedback ("I followed this advice — yield was good")

---

## 6. Competitor Analysis

| Platform | Strengths | Weaknesses | UZHAVAN Advantage |
|----------|-----------|------------|-------------------|
| **Kisan Suvidha** (GoI) | Official, free, wide distribution | English-heavy, no AI, no Tamil personalization, static content | Tamil-first, AI-powered, personalized by farm profile |
| **AgroStar** | Large Hindi-belt user base, e-commerce, vet services | Tamil content sparse, focused on product sales, no TNAU grounding | Not incentivized to sell; purely advisory; TNAU-grounded |
| **DeHaat** | Full-stack model (inputs + advisory + market), strong in UP/Bihar | Not in Tamil Nadu, no Tamil language support | Built for Tamil Nadu districts, language, and crops from day one |
| **Fasal** | IoT sensor integration, disease forecasting, good science | Requires sensor hardware (₹15,000+), too expensive for small farmers | Works on any Android phone with camera, zero hardware cost |
| **iFarm / Ninjacart** | Market linkage, direct-to-buyer pricing | Supply chain focus, not agronomic advisory | Agronomic depth first; market tool added as complement |
| **ChatGPT/Gemini** | General intelligence, any language | Hallucinates crop dosages, no TNAU grounding, no citation, no offline | No hallucination by design; every answer cites a verifiable source |

**Core differentiation:**
1. **Tamil-first** — not translated, natively Tamil
2. **Grounded** — every answer cites TNAU or official source; no AI invention
3. **Personalized** — knows your district, your soil, your crop, your history
4. **Free at point of use** — no hardware, no subscription for core features
5. **Offline-capable** — core flows degrade gracefully without internet

---

## 7. Success Metrics

### North Star Metric
**Weekly Active Farmers (WAF):** Farmers who ask at least one question or check one weather forecast per week.

### Acquisition
| Metric | Target (pilot) | Target (v1.0) |
|--------|---------------|---------------|
| Play Store installs | 500 | 10,000 |
| OTP completion rate | ≥ 85% | ≥ 90% |
| Profile setup completion | ≥ 75% | ≥ 80% |
| Registration time (p90) | < 2 min | < 2 min |

### Engagement
| Metric | Target |
|--------|--------|
| Questions per farmer per week (active) | ≥ 3 |
| D7 retention | ≥ 40% |
| D30 retention | ≥ 20% |
| Farmers who use disease detection | ≥ 30% within 30 days |

### AI Quality
| Metric | Target |
|--------|--------|
| Answer has TNAU citation | 100% |
| Hallucination rate (eval set) | < 2% |
| Groundedness score (eval set) | > 90% |
| Farmer actionability rating (in-app 👍/👎) | ≥ 80% thumbs up |
| Disease detection accuracy (38-class) | > 85% top-1 |

### Performance
| Metric | Target |
|--------|--------|
| Time to first token (p50) | < 2 seconds |
| Full response time (p90) | < 8 seconds |
| Disease detection (p90) | < 1 second |
| Weather fetch (p90) | < 300 ms |
| RAG retrieval (p90) | < 500 ms |
| App crash rate | < 0.5% sessions |

---

## 8. Non-Functional Requirements

### Availability
- API uptime: ≥ 99.5% monthly (excluding scheduled maintenance)
- Scheduled maintenance window: Sundays 2:00–4:00 AM IST
- Graceful degradation: app remains usable for weather and cached chat history when backend is unavailable

### Performance
See KPIs (Section 12). All latency targets are p90 (90th percentile), not average.

### Offline Behavior
| Feature | Online | Offline |
|---------|--------|---------|
| AI chat | Full | Show last 5 conversations from local cache |
| Weather | Live data | Show cached data with "updated X hours ago" label |
| Disease detection | Full (cloud inference) | Show Tamil message: "இணைப்பு தேவை — Wi-Fi அல்லது மொபைல் டேட்டா இயக்கவும்" |
| Farm profile | Read/write | Read only from local cache; sync when online |

### Device Compatibility
- Minimum Android version: Android 10 (API 29)
- Minimum RAM: 2 GB
- Target device class: Redmi 10, Samsung Galaxy A14, LAVA Agni 2
- Tamil Unicode rendering: validated on all target devices
- Storage: < 80 MB installed APK + assets

### Accessibility
- WCAG 2.1 AA compliance for all UI components
- Minimum font size: 16sp (no UI element below 14sp)
- Minimum touch target: 48×48 dp
- Color contrast ratio: ≥ 4.5:1 for body text
- Screen reader (TalkBack) support for primary flows

### Security
- DPDPA 2023 (Digital Personal Data Protection Act) compliant
  - Explicit consent before collecting personal data
  - Data minimization: only collect what is necessary
  - Right to erasure: farmer can delete their account and all data
  - Data localization: all personal data stored on India-based infrastructure
- No raw Aadhaar storage (SHA-256 hash only if used)
- JWT with 15-minute access tokens and 7-day refresh tokens
- OTP expires in 5 minutes; maximum 3 requests per hour
- All API endpoints require authentication except `/auth/*` and `/weather/{district}`
- HTTPS only in production; HSTS headers set

### Data Retention
- Chat messages: 12 months
- AI memory: 24 months
- Request traces (observability): 6 months
- OTP records: 24 hours (purged by scheduled job)
- Farmer profile: until account deletion request

### Localization
- Default language: Tamil (`ta-IN`)
- Secondary language: English (`en-IN`)
- All error messages available in both languages
- Numbers follow Indian numbering system (lakhs, crores)
- Units: hectares (primary) with acres shown in parentheses

---

## 9. MVP Scope (v1.0)

The MVP is defined by nine complete, end-to-end user flows. All nine must work reliably on a Redmi 10 before v1.0 is declared.

| # | Flow | Primary Actor |
|---|------|--------------|
| 1 | Register using OTP — phone number only, no password | Murugan |
| 2 | Create a farm profile in Tamil — district, crop, area, soil type | Murugan |
| 3 | Ask a question in Tamil, English, or Tanglish | Murugan |
| 4 | Receive a grounded TNAU answer with source citation | Murugan |
| 5 | Check weather and get irrigation advice for their district | Murugan |
| 6 | Photograph a diseased plant leaf and identify the disease | Lakshmi |
| 7 | View TNAU treatment recommendations in Tamil (chemical + organic) | Lakshmi |
| 8 | Discover relevant government scheme eligibility | Selvam |
| 9 | View a simple dashboard showing farm, weather, and recent activity | All three |

Each flow is validated by the corresponding Golden User Story E2E test (see Section 12).

---

## 10. Future Scope (Post v1.0)

These features are explicitly **not in scope** until all 9 MVP flows work reliably with real Tamil Nadu farmer users.

| Feature | Phase | Sprint |
|---------|-------|--------|
| Voice input and output (Tamil TTS/STT) | Phase 1 | Sprint 6 |
| WhatsApp integration (send questions via WhatsApp) | Phase 4 | Post-MVP |
| Farm Diary (expense tracking, income, profit) | Phase 2 | Sprint 7 |
| AI Memory reasoning (Farmer Memory Agent) | Phase 2 | Sprint 7 |
| Satellite intelligence (NDVI, crop health from SICKLE) | Phase 3 | Sprint 8 |
| Yield and profit prediction | Phase 3 | Sprint 8 |
| Marketplace (input buying, crop selling) | Phase 4 | Post-MVP |
| Expert video consultation | Phase 4 | Post-MVP |
| Government portal (district dashboards) | Phase 4 | Post-MVP |
| IoT sensor integration | Phase 5 | Post-MVP |
| Drone advisory | Phase 5 | Post-MVP |
| Carbon credit tracking | Phase 5 | Post-MVP |
| Community forum | Phase 4 | Post-MVP |

**Engineering Directive ED-001 governs scope:** No new features are added until the existing farmer journey is complete, tested, and usable by a real Tamil Nadu farmer.

---

## 11. Risks

### AI / Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| LLM hallucination of crop recommendations | Medium | Critical | No-hallucination guardrail: LLM never called without retrieved sources; VerificationGraph blocks empty-context calls |
| TNAU knowledge base becomes stale | Medium | High | Quarterly RAG re-crawl pipeline; TNAU publication date tracked in chunk metadata |
| bge-m3 Tamil quality degraded by Tanglish | Low | Medium | Evaluation suite with Tamil + Tanglish test questions; monthly benchmark run |
| Qwen3 Ollama too slow on low-end server | Medium | High | Claude API fallback; streaming makes latency perceptible earlier; response budget < 8s enforced |
| ChromaDB corruption on server restart | Low | High | Persistent volume mount; daily backup to S3; recovery playbook in `playbooks/Database Recovery.md` |

### Product / Market Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Low farmer adoption (tech skepticism) | High | Critical | KVK partnerships for live demonstrations; word-of-mouth from pilot farmers; Tamil-first UI removes language barrier |
| Rural connectivity prevents real-time AI | High | Medium | Offline graceful degradation; weather cached 1 hour; chat history cached locally |
| Tamil NLP quality insufficient for agricultural jargon | Medium | High | TNAU vocabulary used in prompts; product quality review of Tamil terminology per FP; farmer feedback loop |
| Competing platform launches Tamil AI first | Low | Medium | Speed to market; TNAU data advantage; district-level personalization |

### Regulatory Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| DPDPA 2023 enforcement on AI recommendations | Medium | High | Data minimization; explicit consent; no Aadhaar storage; privacy policy in Tamil |
| India AI governance framework restricts LLM use in agriculture | Low | Medium | All recommendations cite official government sources (TNAU/ICAR); not financial advice |
| TNAU content licensing challenge | Low | Medium | RAG cites public-domain TNAU publications; legal review before commercial launch |

---

## 12. KPIs

### AI Performance KPIs

| KPI | Target | Measurement |
|-----|--------|-------------|
| Average AI response time (p50) | < 2 seconds | `request_traces.total_ms` |
| AI response time (p90) | < 8 seconds | `request_traces.total_ms` |
| RAG retrieval time (p90) | < 500 ms | `request_traces.retrieval_ms` |
| Weather API response (p90) | < 300 ms | `request_traces.tool_ms` where tools_used contains 'weather' |
| Disease prediction time (p90) | < 1 second | Disease service response time |
| Chat accuracy (grounded, no hallucination) | > 90% | `evaluation/benchmark.py` groundedness score |
| Citation rate (% answers with ≥1 TNAU source) | 100% | `request_traces.chunks_retrieved > 0` |
| RAG confidence (mean score on cited chunks) | > 0.65 | `request_traces.confidence` |
| Fallback rate (no context found) | < 15% | `request_traces.chunks_retrieved == 0` |

### Product KPIs

| KPI | Target | Measurement |
|-----|--------|-------------|
| Registration completion time (p90) | < 2 minutes | Time from app open to HomeScreen |
| Disease detection taps to result | ≤ 3 taps | Home → camera → result (no intermediate screens) |
| Question to answer (end-to-end) | < 10 seconds | Time from send tap to last SSE event |
| D7 retention | ≥ 40% | Farmers who return within 7 days of install |
| Questions per active farmer per week | ≥ 3 | `chat_messages` count grouped by farmer, week |
| Farmer actionability rating | ≥ 80% positive | In-app 👍/👎 on AI responses |
| Disease detection accuracy | > 85% | MobileNetV2 top-1 on PlantVillage validation set |

### Golden User Story E2E KPIs (must all pass before v1.0)

| Story | Actor | Pass Criteria |
|-------|-------|--------------|
| **GUS-1:** Irrigation decision | Murugan | "நாளைக்கு தண்ணீர் விடலாமா?" → weather + TNAU irrigation advice → cited Tamil answer ≤ 8s → stored in ai_memory |
| **GUS-2:** Disease detection | Lakshmi | Banana leaf photo → disease identified → Tamil treatment (chemical + organic) → linked scheme — all within 5s |
| **GUS-3:** Crop recommendation | Selvam | "இந்த சீசனில் என்ன விளைவிக்கலாம்?" → weather + market + soil → ranked crops with profit estimate → TNAU cultivation advice |

---

## 13. Launch Criteria

UZHAVAN AI v1.0 is ready for public launch when **all** of the following are true:

### Technical Criteria
- [ ] All 9 MVP flows (Section 9) work end-to-end on a Redmi 10
- [ ] All 3 Golden User Stories (GUS-1, GUS-2, GUS-3) pass as automated E2E tests
- [ ] AI hallucination rate < 2% on `evaluation/questions.json` benchmark (100 questions)
- [ ] Citation rate = 100% (no answer returned without at least one source)
- [ ] All 10 release gates passed for every Sprint 4–5 Feature Pack
- [ ] OWASP API Top 10 security review complete with no Critical/High findings
- [ ] Dependency audit (SBOM) complete; no known CVE-CRITICAL dependencies
- [ ] Performance targets met on Redmi 10-class hardware (p90 < 8s full response)

### Product Criteria
- [ ] All user-facing strings have Tamil translations; no English-only error messages
- [ ] Product Quality Agent Murugan walkthrough passes for every feature
- [ ] Offline degradation tested: app remains functional without connectivity
- [ ] Accessibility: primary flows usable with TalkBack screen reader

### Compliance Criteria
- [ ] Privacy policy published in Tamil and English
- [ ] DPDPA 2023 consent flow implemented: explicit opt-in before data collection
- [ ] Account deletion ("right to erasure") implemented and tested
- [ ] Data localization verified: all personal data stored on India-region infrastructure

### Pilot Criteria
- [ ] 50-farmer pilot completed in at least 3 Tamil Nadu districts
- [ ] ≥ 70% of pilot farmers rate the app as "useful" or "very useful"
- [ ] ≥ 60% of pilot farmers report acting on at least one AI recommendation
- [ ] Pilot incident log reviewed; all P0/P1 incidents resolved

### Operations Criteria
- [ ] Monitoring and alerting configured (API latency, error rate, Ollama health)
- [ ] Incident response playbook (`playbooks/Incident Response.md`) tested in tabletop exercise
- [ ] Database backup and recovery tested (`playbooks/Database Recovery.md`)
- [ ] Release checklist (`playbooks/Release Checklist.md`) completed for v1.0 build

---

## Document History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-01 | Initial PRD — approved by Product Agent and Master Agent |
