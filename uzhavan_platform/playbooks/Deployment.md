# Deployment Playbook

**Last updated:** 2026-07-01
**Stack:** Docker Compose · FastAPI · PostgreSQL 16 · Redis · Ollama · Flutter

---

## Pre-Deployment Checklist

Complete every item before deploying. No exceptions.

```
[ ] pytest passes locally: pytest --tb=short
[ ] Black passes: black --check backend/
[ ] Ruff passes: ruff check backend/
[ ] MyPy passes: mypy backend/
[ ] All FP release gates signed off in docs/feature-packs/FP-XXX.md
[ ] CHANGELOG.md updated with this version's changes
[ ] Release notes written for each FP in this version
[ ] New migrations reviewed for reversibility
[ ] Feature flags reviewed — new flags default to False
[ ] docker compose build succeeds locally
[ ] Secrets confirmed in .env (not committed)
[ ] Team notified: "Deploying v0.X in 15 minutes"
```

---

## Environment Files

```
.env.staging    — staging environment variables
.env.production — production environment variables (never committed)

Required variables:
  DATABASE_URL=postgresql://uzhavan:password@postgres:5432/uzhavan
  REDIS_URL=redis://redis:6379/0
  JWT_SECRET=<32+ char random string>
  OLLAMA_BASE_URL=http://ollama:11434
  OLLAMA_MODEL=qwen3:8b
  LLM_PROVIDER=ollama              # or "claude"
  CLAUDE_API_KEY=<key>             # required if LLM_PROVIDER=claude
  EMBED_MODEL=BAAI/bge-m3
  CHROMA_PATH=/app/rag/chroma
  ENV=staging                      # or "production"
```

---

## Staging Deployment

### 1. Build images

```bash
cd /path/to/uzhavan_platform

# Build all services
docker compose -f docker-compose.yml -f docker-compose.staging.yml build

# Verify build — all services should show "Successfully built"
docker compose -f docker-compose.yml -f docker-compose.staging.yml config --services
```

### 2. Run database migrations

```bash
# Take a backup first
pg_dump -h localhost -U uzhavan -d uzhavan_staging > backups/pre-deploy-$(date +%Y%m%d-%H%M).sql

# Run pending migrations in order
docker compose exec postgres psql -U uzhavan -d uzhavan_staging \
  -f /migrations/001_initial_schema.sql
docker compose exec postgres psql -U uzhavan -d uzhavan_staging \
  -f /migrations/002_seed_data.sql
docker compose exec postgres psql -U uzhavan -d uzhavan_staging \
  -f /migrations/003_auth_tables.sql
docker compose exec postgres psql -U uzhavan -d uzhavan_staging \
  -f /migrations/004_observability_memory.sql

# Verify schema
docker compose exec postgres psql -U uzhavan -d uzhavan_staging -c "\dt"
```

### 3. Start services

```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Wait for all services to be healthy
docker compose ps   # all should show "healthy" or "running"

# Check logs for errors during startup
docker compose logs --tail=30 conversation
docker compose logs --tail=30 ollama
```

### 4. Health checks

```bash
# Conversation service
curl -s http://staging.uzhavan.ai:8002/health | python3 -m json.tool
# Expected: {"status": "ok", "ollama": "ok", "chroma": "ok", "db": "ok"}

# Disease service
curl -s http://staging.uzhavan.ai:8001/health | python3 -m json.tool
```

### 5. Smoke tests

```bash
# Get test JWT
TEST_JWT=$(curl -s -X POST http://staging.uzhavan.ai:8002/auth/verify-otp \
  -d '{"phone": "9999999999", "otp": "000000"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Send a test chat message — verify SSE events arrive
curl -s -N \
  -H "Authorization: Bearer $TEST_JWT" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "rice pest treatment", "language": "English"}' \
  http://staging.uzhavan.ai:8002/chat \
  | head -20

# Verify request_traces written
docker compose exec postgres psql -U uzhavan -c \
  "SELECT trace_id, total_ms, chunks_retrieved FROM request_traces ORDER BY created_at DESC LIMIT 1;"
```

### 6. Rollback trigger conditions

Immediately roll back if any of the following:
- `/health` returns non-200 after 3 restart attempts
- Smoke test receives no SSE events within 15 seconds
- `request_traces` shows `total_ms > 20000` (2× budget) on 3+ consecutive requests
- Any database migration fails (restore from pre-deploy backup)

---

## Production Deployment

Same as staging with these differences:

```bash
# Use production compose override
docker compose -f docker-compose.yml -f docker-compose.production.yml build
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d

# Take production backup before migration
pg_dump -h prod-db-host -U uzhavan -d uzhavan_prod \
  > backups/prod-pre-deploy-$(date +%Y%m%d-%H%M).sql
aws s3 cp backups/prod-pre-deploy-*.sql s3://uzhavan-backups/pre-deploy/
```

Monitor for 30 minutes after production deployment:
```bash
# Watch request_traces for latency anomalies
watch -n 10 'docker compose exec postgres psql -U uzhavan -c \
  "SELECT AVG(total_ms), MAX(total_ms), COUNT(*) FROM request_traces WHERE created_at > NOW() - INTERVAL '\''5 minutes'\'';"'
```

---

## Database Migration Procedure

### Running `004_observability_memory.sql`

```bash
# 1. Backup
pg_dump -U uzhavan uzhavan > backups/before-004-$(date +%Y%m%d-%H%M).sql

# 2. Dry run — check for syntax errors
psql -U uzhavan -d uzhavan \
  --dry-run -f database/migrations/004_observability_memory.sql 2>&1

# 3. Run
psql -U uzhavan -d uzhavan \
  -f database/migrations/004_observability_memory.sql

# 4. Verify tables created
psql -U uzhavan -d uzhavan -c "\d request_traces"
psql -U uzhavan -d uzhavan -c "\d ai_memory"

# 5. Verify indexes
psql -U uzhavan -d uzhavan -c "\di idx_traces_*"
```

### Migration Rollback

```bash
# If migration fails or causes issues:
psql -U uzhavan -d uzhavan -c "DROP TABLE IF EXISTS request_traces;"
psql -U uzhavan -d uzhavan -c "DROP TABLE IF EXISTS ai_memory;"

# Or restore full backup:
psql -U uzhavan -d uzhavan < backups/before-004-YYYYMMDD-HHMM.sql
```

---

## Ollama Model Update (Qwen3 Version Bump)

```bash
# 1. Pull new model version (don't delete old one yet)
docker compose exec ollama ollama pull qwen3:8b-q4_K_M   # example: switching quantization

# 2. Test new model
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:8b-q4_K_M",
  "prompt": "Rice BPH treatment in Tamil Nadu",
  "stream": false
}'

# 3. Run LLM evaluation against ground truth
python3 evaluation/llm_eval.py --model qwen3:8b-q4_K_M

# 4. If evaluation passes (accuracy >= current baseline):
# Update OLLAMA_MODEL in .env
# docker compose restart conversation decision

# 5. Delete old model only after 24h of stable production
docker compose exec ollama ollama rm qwen3:8b
```

---

## Embedding Model Update (bge-m3 Version Bump)

**Warning:** Changing the embedding model requires re-embedding ALL chunks. This is a significant operation.

```bash
# 1. Backup ChromaDB
tar -czf backups/chroma-before-$(date +%Y%m%d).tar.gz rag/chroma/
aws s3 cp backups/chroma-before-*.tar.gz s3://uzhavan-backups/chroma/

# 2. Run evaluation with new model on sample queries BEFORE changing anything
# Edit a test script with new model name, test retrieval quality

# 3. If evaluation passes — update EMBED_MODEL in .env
# Then reset and re-embed
python3 data_pipeline/embed_chunks.py --reset

# 4. Verify
python3 data_pipeline/embed_chunks.py --stats

# 5. Run RAG evaluation
python3 evaluation/rag_eval.py

# 6. Restart services
docker compose restart knowledge conversation
```

---

## Flutter App Release

```bash
# 1. Update version in pubspec.yaml
# version: 0.3.0+3   (semver+build-number)

# 2. Build release APK
cd apps/farmer
flutter build apk --release --target-platform android-arm,android-arm64

# 3. Run on Redmi 10 (or equivalent test device)
adb install -r build/app/outputs/flutter-apk/app-release.apk
# Manual test: complete Murugan irrigation scenario

# 4. Test on additional low-end device if available
# Check: Tamil rendering, SSE streaming, camera, offline states

# 5. Build App Bundle for Play Store
flutter build appbundle --release

# 6. Upload to Play Store (internal testing track first)
# Use Play Console or fastlane
```

---

## Rollback Procedure by Service

### Conversation / Decision / Knowledge services
```bash
# Identify last stable image tag
docker image ls | grep uzhavan

# Edit docker-compose.yml to pin previous tag
# Then:
docker compose down conversation decision knowledge
docker compose up -d conversation decision knowledge
```

### Database (schema rollback)
```bash
# Restore from pre-deployment backup
docker compose stop conversation decision knowledge
psql -U uzhavan -c "DROP DATABASE uzhavan;"
psql -U uzhavan -c "CREATE DATABASE uzhavan;"
psql -U uzhavan uzhavan < backups/pre-deploy-YYYYMMDD-HHMM.sql
docker compose start conversation decision knowledge
```

### ChromaDB (embedding rollback)
```bash
docker compose stop knowledge
rm -rf rag/chroma/
tar -xzf backups/chroma-before-YYYYMMDD.tar.gz
docker compose start knowledge
```

### Flutter app rollback
```bash
# Upload previous APK to Play Store
# Or sideload previous APK to test devices for verification
```
