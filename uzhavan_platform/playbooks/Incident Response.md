# Incident Response Playbook

**Last updated:** 2026-07-01
**Stack:** FastAPI + LangGraph + Qwen3/Ollama + ChromaDB + PostgreSQL + Redis

---

## Severity Levels

| Level | Definition | Response SLA | Who Is Paged |
|-------|-----------|-------------|-------------|
| P0 | All farmers cannot receive any response; data loss risk | Immediate, 24/7 | On-call engineer |
| P1 | Major feature broken; > 50% of requests failing | 30 min during business hours | On-call engineer |
| P2 | Degraded quality or latency; feature partially working | 4 hours | Team channel |
| P3 | Single farmer, single session issue; no systemic impact | Next business day | Ticket created |

---

## P0: All Farmers Get "No Response" (Service Down)

### Diagnose

```bash
# 1. Check all service health endpoints
curl -s http://localhost:8002/health    # conversation service
curl -s http://localhost:8001/health    # disease service

# 2. Check Docker Compose status
docker compose ps

# 3. Check recent logs across all services
docker compose logs --tail=100 conversation
docker compose logs --tail=100 decision
docker compose logs --tail=100 knowledge

# 4. Check PostgreSQL connectivity
docker compose exec postgres psql -U uzhavan -c "SELECT 1;"

# 5. Check Redis
docker compose exec redis redis-cli ping
```

### Resolution

```bash
# If a container is stopped/crashed — restart it
docker compose restart conversation

# If all containers are down — full restart
docker compose up -d

# If DB is refusing connections — check pg_hba.conf and restart
docker compose restart postgres
sleep 5
docker compose restart conversation decision

# If Redis is down — restart (it's a cache; data loss is acceptable)
docker compose restart redis

# Verify recovery
curl -s http://localhost:8002/health | python3 -m json.tool
```

### Rollback (if restart doesn't resolve)
```bash
# Roll back to previous Docker image tag
docker compose down
# Edit docker-compose.yml: revert image tags to previous version
docker compose up -d
```

---

## P0: LLM Hallucinating (Responding Without TNAU Sources)

### Diagnose

```bash
# Check request_traces — are chunks_retrieved = 0 on recent requests?
docker compose exec postgres psql -U uzhavan -c "
  SELECT trace_id, chunks_retrieved, confidence, created_at
  FROM request_traces
  ORDER BY created_at DESC
  LIMIT 20;
"

# Check ChromaDB collection size
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='rag/chroma')
col = client.get_collection('tnau_knowledge')
print('Count:', col.count())
"

# Check verification node is working — test with known advisory query
curl -s -N -H "Authorization: Bearer $TEST_JWT" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "BPH in rice treatment", "language": "English"}' \
  http://localhost:8002/chat
# Response should contain "type":"sources" event — if missing, guardrail failed
```

### Resolution

**If ChromaDB is empty:**
```bash
# Re-run embedding pipeline
cd data_pipeline
python3 embed_chunks.py --stats          # confirm 0 chunks
python3 embed_chunks.py --reset          # full re-embed from chunks.jsonl
python3 embed_chunks.py --stats          # confirm chunk count restored
```

**If verification node bypassed (code bug):**
```bash
# Check feature_flags.py — ENABLE_STREAMING and guardrail settings
grep -n "ENABLE" backend/feature_flags.py
# Roll back to last known-good commit on develop
git log --oneline -10
git checkout <last-good-sha> -- backend/decision/graph/verification.py
docker compose restart decision
```

**Immediate mitigation:** Set `ENABLE_MARKET=False` and `ENABLE_SATELLITE=False` to reduce tool surface area while investigating.

---

## P1: Ollama Down (Qwen3 Not Serving)

### Diagnose

```bash
# Check Ollama API
curl http://localhost:11434/api/tags

# Check if model is loaded
curl http://localhost:11434/api/show -d '{"name": "qwen3:8b"}'

# Check Ollama process logs
docker compose logs --tail=50 ollama
# or if running as system service:
journalctl -u ollama -n 50
```

### Resolution

```bash
# Restart Ollama (Docker)
docker compose restart ollama
sleep 10
curl http://localhost:11434/api/tags   # verify qwen3:8b in list

# If model is missing — re-pull
docker compose exec ollama ollama pull qwen3:8b

# Immediate fallback — switch to Claude API
export LLM_PROVIDER=claude
export CLAUDE_MODEL=claude-sonnet-4-6
docker compose restart conversation decision
# Verify: next request should use Claude, visible in request_traces.llm_provider
```

---

## P1: ChromaDB Corruption or Empty Collection

### Diagnose

```bash
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='rag/chroma')
try:
    col = client.get_collection('tnau_knowledge')
    print('Count:', col.count())
    # Sample a retrieval
    results = col.query(query_texts=['rice pest treatment'], n_results=3)
    print('Sample distances:', results['distances'])
except Exception as e:
    print('ERROR:', e)
"
```

### Resolution

```bash
# Option 1: Incremental re-embed (preserves existing, adds missing)
python3 data_pipeline/embed_chunks.py

# Option 2: Full reset (use if collection is corrupt)
python3 data_pipeline/embed_chunks.py --reset

# Verify
python3 data_pipeline/embed_chunks.py --stats

# Restore from backup if chunks.jsonl is also lost
aws s3 cp s3://uzhavan-backups/latest/chroma_backup.tar.gz .
tar -xzf chroma_backup.tar.gz -C rag/
docker compose restart knowledge
```

---

## P1: PostgreSQL Connection Pool Exhausted

### Diagnose

```bash
docker compose exec postgres psql -U uzhavan -c "
  SELECT count(*) as total_connections,
         state,
         wait_event_type,
         wait_event
  FROM pg_stat_activity
  GROUP BY state, wait_event_type, wait_event
  ORDER BY total_connections DESC;
"

# Check max_connections setting
docker compose exec postgres psql -U uzhavan -c "SHOW max_connections;"
```

### Resolution

```bash
# Immediately terminate idle connections
docker compose exec postgres psql -U uzhavan -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle'
    AND state_change < NOW() - INTERVAL '5 minutes'
    AND datname = 'uzhavan';
"

# Restart services to release pool (non-destructive)
docker compose restart conversation backend

# If recurring: reduce pool size in asyncpg create_pool calls
# backend/conversation/main.py: min_size=1, max_size=5 (from max_size=10)
```

---

## P2: Weather API Timeout > 300ms

### Diagnose

```bash
# Check request_traces for weather tool latency
docker compose exec postgres psql -U uzhavan -c "
  SELECT AVG(tool_ms), MAX(tool_ms), COUNT(*)
  FROM request_traces
  WHERE 'weather' = ANY(tools_used)
    AND created_at > NOW() - INTERVAL '1 hour';
"

# Test Open-Meteo directly
time curl -s "https://api.open-meteo.com/v1/forecast?latitude=10.79&longitude=79.13&daily=precipitation_sum&forecast_days=7"

# Check Redis weather cache hit rate
docker compose exec redis redis-cli info stats | grep keyspace_hits
```

### Resolution

```bash
# Extend Redis weather cache TTL (default 3600s → 7200s)
# Edit backend/knowledge/weather/open_meteo.py: TTL constant

# Verify cache is being used — check Redis keys
docker compose exec redis redis-cli keys "weather:*"

# If Open-Meteo is globally slow: enable warning in VerificationGraph
# Set feature flag to add "weather data may be delayed" warning
```

---

## P2: SSE Stream Dropping Connections

### Diagnose

```bash
# Check nginx buffering (if behind nginx)
grep -i "proxy_buffering\|proxy_read_timeout" /etc/nginx/sites-enabled/uzhavan

# Check FastAPI keepalive settings
docker compose logs conversation | grep -i "disconnect\|timeout\|connection"

# Test SSE directly — should stay open for duration of response
curl -v -N -H "Authorization: Bearer $TEST_JWT" \
  -H "Accept: text/event-stream" \
  -d '{"message": "test", "language": "English"}' \
  http://localhost:8002/chat
```

### Resolution

```bash
# nginx fix — add to location block:
# proxy_buffering off;
# proxy_read_timeout 120s;
# proxy_cache off;
# X-Accel-Buffering: no header must be set in FastAPI response

# FastAPI fix — ensure StreamingResponse has correct headers:
# "Cache-Control": "no-cache"
# "X-Accel-Buffering": "no"
# "Connection": "keep-alive"
```

---

## P3: Single Farmer Reporting Wrong Advice

### Diagnose

```bash
# Find farmer's recent traces using their farmer_id (from support ticket)
docker compose exec postgres psql -U uzhavan -c "
  SELECT trace_id, intent, tools_used, chunks_retrieved, confidence, total_ms, created_at
  FROM request_traces
  WHERE farmer_id = '<farmer_id>'
  ORDER BY created_at DESC
  LIMIT 10;
"

# Find the specific ai_memory record
docker compose exec postgres psql -U uzhavan -c "
  SELECT question, intent, crop, district, advice, confidence, created_at
  FROM ai_memory
  WHERE farmer_id = '<farmer_id>'
  ORDER BY created_at DESC
  LIMIT 5;
"

# Reproduce the issue — send the same question manually
curl -s -N -H "Authorization: Bearer $TEST_JWT" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "<farmers_question>", "language": "Tamil"}' \
  http://localhost:8002/chat
```

### Resolution

If the advice is factually wrong: update the relevant TNAU chunk in the knowledge base (not the LLM prompt). Re-embed. Respond to farmer with corrected advice manually.

If the advice is correct but farmer misunderstood: Product Quality Agent review for Tamil clarity.

---

## Escalation Path

```
P3 → Create ticket → Assigned agent investigates next business day
P2 → Post in #uzhavan-incidents → On-call engineer reviews within 4h
P1 → Page on-call → 30-minute response SLA
P0 → Page on-call + team lead → Immediate response
```

## Communication Template (P0/P1)

```
INCIDENT REPORT — UZHAVAN AI
Time: [UTC]
Severity: P[0/1]
Impact: [X% of requests affected / specific feature down]
Symptom: [What farmers are seeing]
Status: Investigating / Mitigated / Resolved
Next update: [time]
```

## Post-Mortem Process

Within 48h of any P0/P1:
1. Timeline of events (UTC timestamps)
2. Root cause (not "human error" — the system that allowed it)
3. Immediate fix applied
4. Long-term fix (ADR if architectural change needed)
5. Detection gap (why didn't monitoring catch it sooner?)
6. Prevention (what process or code change prevents recurrence)

File as `docs/incidents/YYYY-MM-DD-short-title.md`.
