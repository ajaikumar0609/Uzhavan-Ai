# UZHAVAN AI — Backlog (TODO)

Maintained by: Planning Agent
Last updated: 2026-07-01

Items here are not yet scheduled into a sprint.
Use SPRINT.md for active work.

---

## Critical (must happen before Flutter)
- [ ] Fix API route names (underscores → hyphens)
- [ ] Write test suite foundation (conftest.py, disease + advisory tests)
- [ ] Complete DB seed migrations (003-007)
- [ ] Test Docker Compose stack end-to-end

## Flutter MVP
- [ ] Flutter project scaffold (`mobile/`)
- [ ] Camera → disease detection flow
- [ ] Tamil language UI with Noto Sans Tamil
- [ ] Offline caching with Hive
- [ ] Advisory chat with streaming response

## Advisory Service Improvements
- [ ] Score threshold filter: reject chunks < 0.35 similarity
- [ ] Multi-turn conversation history persistence (Redis)
- [ ] Farmer profile injection (district + crops into RAG filter)
- [ ] Streaming response (SSE) for long advisory answers
- [ ] Usage logging to PostgreSQL (chat_sessions + chat_messages)

## Disease Detection Improvements
- [ ] Confidence threshold: < 0.40 → "uncertain, consult agronomist"
- [ ] Image quality check (blur detection before inference)
- [ ] Tamil disease names in all responses
- [ ] Connect to diseases.csv for richer TNAU data

## LangGraph Orchestration
- [ ] Intent classifier (disease / advisory / market / weather / general)
- [ ] Weather tool (Open-Meteo — free, no key needed)
- [ ] Market price tool (AGMARKNET API)
- [ ] LangGraph multi-step routing workflow
- [ ] Tool call logging (which tools were used per advisory)

## Database
- [ ] Alembic migration management (replace numbered SQL)
- [ ] PostGIS farm boundary import
- [ ] NDVI timeseries table population
- [ ] mandi_prices table AGMARKNET integration

## DevOps / CI
- [ ] GitHub Actions CI (lint + test + build)
- [ ] Environment-specific compose files (dev / staging)
- [ ] Health check dashboard
- [ ] Automated TNAU re-crawl schedule (monthly)

## Satellite (Phase 6)
- [ ] SICKLE dataset loader
- [ ] Satellite AI service scaffold (port 8003)
- [ ] Crop type prediction endpoint
- [ ] NDVI growth curve visualization

## Production (Phase 7)
- [ ] Phone OTP authentication
- [ ] Rate limiting per farmer ID
- [ ] WhatsApp bot integration
- [ ] Tamil TTS for audio advisory
- [ ] Load testing
- [ ] Security audit
