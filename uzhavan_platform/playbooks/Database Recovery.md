# Database Recovery Playbook

**Last updated:** 2026-07-01
**Databases:** PostgreSQL 16 + PostGIS 3.4 · ChromaDB (local persistent) · Redis 7

---

## Daily Backup Procedure

### PostgreSQL

```bash
#!/bin/bash
# Run via cron: 0 2 * * * /opt/uzhavan/scripts/backup_postgres.sh

BACKUP_DIR="/backups/postgres"
DB_NAME="uzhavan"
DB_USER="uzhavan"
DATE=$(date +%Y%m%d-%H%M)
FILENAME="uzhavan-${DATE}.sql.gz"

mkdir -p $BACKUP_DIR

# Full dump with compression
pg_dump -h localhost -U $DB_USER -d $DB_NAME \
  --format=custom \
  --compress=9 \
  --file="${BACKUP_DIR}/${FILENAME}"

# Upload to S3
aws s3 cp "${BACKUP_DIR}/${FILENAME}" \
  "s3://uzhavan-backups/postgres/${FILENAME}" \
  --storage-class STANDARD_IA

# Verify upload
aws s3 ls "s3://uzhavan-backups/postgres/${FILENAME}"

# Retention: delete local backups older than 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup complete: ${FILENAME}"
```

**Retention policy:**
- Local: 7 days
- S3 STANDARD_IA: 30 days
- S3 Glacier (monthly snapshots): 1 year

### ChromaDB

```bash
#!/bin/bash
# ChromaDB is a directory — tar and upload

CHROMA_DIR="/app/rag/chroma"
DATE=$(date +%Y%m%d-%H%M)
FILENAME="chroma-${DATE}.tar.gz"

# Stop knowledge service briefly to avoid partial-state backup
docker compose stop knowledge

tar -czf "/backups/chroma/${FILENAME}" -C /app/rag chroma/

docker compose start knowledge

# Upload to S3
aws s3 cp "/backups/chroma/${FILENAME}" \
  "s3://uzhavan-backups/chroma/${FILENAME}"

# Keep last 7 local copies
ls -t /backups/chroma/chroma-*.tar.gz | tail -n +8 | xargs -r rm

echo "ChromaDB backup: ${FILENAME}"
```

---

## Point-in-Time Recovery

PostgreSQL does not have WAL archiving enabled by default. For PITR:

```bash
# Enable WAL archiving in postgresql.conf:
# wal_level = replica
# archive_mode = on
# archive_command = 'aws s3 cp %p s3://uzhavan-backups/wal/%f'

# Restore to a specific time:
# 1. Stop PostgreSQL
docker compose stop postgres

# 2. Restore base backup
pg_restore -h localhost -U uzhavan -d uzhavan_restore \
  /backups/postgres/uzhavan-YYYYMMDD-HHMM.sql.gz

# 3. Configure recovery.conf (PostgreSQL < 12) or postgresql.conf (>= 12)
echo "recovery_target_time = '2026-07-01 14:30:00'" >> postgresql.conf
echo "restore_command = 'aws s3 cp s3://uzhavan-backups/wal/%f %p'" >> postgresql.conf

# 4. Start and let WAL replay
docker compose start postgres
# Watch logs until "recovery complete"
docker compose logs -f postgres | grep -i "recovery\|started"
```

---

## `ai_memory` Table Corruption Recovery

`ai_memory` stores structured intent+advice records derived from `chat_messages`. It can be partially rebuilt.

```bash
# Check corruption
psql -U uzhavan -c "SELECT COUNT(*) FROM ai_memory;"
psql -U uzhavan -c "SELECT * FROM ai_memory ORDER BY created_at DESC LIMIT 5;"

# If corrupt — drop and rebuild from chat_messages
psql -U uzhavan << 'SQL'
BEGIN;

TRUNCATE ai_memory;

-- Rebuild intent + advice records from stored assistant messages
INSERT INTO ai_memory (farmer_id, session_id, question, advice, created_at)
SELECT
  cs.farmer_id,
  cm_q.session_id,
  cm_q.content AS question,
  cm_a.content AS advice,
  cm_q.created_at
FROM chat_messages cm_q
JOIN chat_messages cm_a
  ON cm_a.session_id = cm_q.session_id
  AND cm_a.role = 'assistant'
  AND cm_a.created_at = (
    SELECT MIN(created_at) FROM chat_messages
    WHERE session_id = cm_q.session_id
      AND role = 'assistant'
      AND created_at > cm_q.created_at
  )
JOIN chat_sessions cs ON cs.session_id = cm_q.session_id
WHERE cm_q.role = 'user'
ON CONFLICT DO NOTHING;

COMMIT;
SQL

# Note: intent, crop, district fields will be NULL (not recoverable from chat_messages alone)
# These will be populated correctly by new interactions going forward
echo "ai_memory rebuilt from chat_messages. intent/crop/district fields are NULL — will populate on new interactions."
```

---

## `request_traces` Table Cleanup

```bash
# Archive rows older than 90 days to S3 before deleting

# 1. Export to CSV
psql -U uzhavan -c "
COPY (
  SELECT * FROM request_traces
  WHERE created_at < NOW() - INTERVAL '90 days'
) TO '/backups/traces/traces-archive-$(date +%Y%m%d).csv' CSV HEADER;
"

# 2. Upload archive
aws s3 cp /backups/traces/traces-archive-*.csv \
  s3://uzhavan-backups/traces/

# 3. Delete archived rows
psql -U uzhavan -c "
DELETE FROM request_traces
WHERE created_at < NOW() - INTERVAL '90 days';
"

# 4. VACUUM to reclaim space
psql -U uzhavan -c "VACUUM ANALYZE request_traces;"

echo "Archived and cleaned request_traces older than 90 days"
```

Run via cron monthly: `0 3 1 * * /opt/uzhavan/scripts/archive_traces.sh`

---

## Redis Recovery

Redis is a cache. Complete data loss is acceptable — all source data lives in PostgreSQL and ChromaDB.

```bash
# If Redis is corrupted or in a bad state — flush and restart
docker compose exec redis redis-cli FLUSHALL

# Or restart the container (Redis will start empty)
docker compose restart redis

# Verify it's empty and responsive
docker compose exec redis redis-cli ping       # → PONG
docker compose exec redis redis-cli DBSIZE     # → 0

# Cache will repopulate automatically:
# - Weather cache: on next /weather request (TTL 3600s)
# - OTP rate limits: reset (acceptable — farmers can request OTPs again)
# - Chat rate limits: reset (acceptable — briefly higher limit, then normalizes)
```

---

## PostGIS Index Rebuild

Needed if spatial queries become slow or after bulk data import.

```bash
psql -U uzhavan << 'SQL'
-- Check spatial indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('farms', 'district_profiles')
  AND indexdef LIKE '%gist%';

-- Rebuild GIST indexes
REINDEX INDEX CONCURRENTLY idx_farms_geom;
REINDEX INDEX CONCURRENTLY idx_districts_geom;

-- Update statistics for query planner
ANALYZE farms;
ANALYZE district_profiles;

-- Verify spatial queries work
SELECT district_name, ST_AsText(geom)
FROM district_profiles
WHERE ST_DWithin(geom, ST_Point(79.13, 10.79)::geography, 50000)
LIMIT 3;
SQL
```

---

## Test Restore Procedure (Quarterly)

Run every 3 months to verify backups are valid and restores actually work.

```bash
#!/bin/bash
# Run in a separate test environment — never on production

echo "=== QUARTERLY RESTORE TEST $(date) ==="

# 1. Download latest backup from S3
aws s3 cp \
  $(aws s3 ls s3://uzhavan-backups/postgres/ | sort | tail -1 | awk '{print $4}') \
  /tmp/test_restore.sql.gz

# 2. Create test database
psql -U postgres -c "CREATE DATABASE uzhavan_restore_test;"

# 3. Restore
pg_restore -h localhost -U postgres -d uzhavan_restore_test /tmp/test_restore.sql.gz

# 4. Verify row counts match production
echo "--- Row counts ---"
psql -U postgres -d uzhavan_restore_test -c "
SELECT 'farmers' as table_name, COUNT(*) FROM farmers
UNION ALL SELECT 'chat_sessions', COUNT(*) FROM chat_sessions
UNION ALL SELECT 'ai_memory', COUNT(*) FROM ai_memory
UNION ALL SELECT 'request_traces', COUNT(*) FROM request_traces;
"

# 5. Verify PostGIS extensions
psql -U postgres -d uzhavan_restore_test -c "SELECT PostGIS_Version();"

# 6. ChromaDB restore test
mkdir -p /tmp/chroma_restore_test
aws s3 cp \
  $(aws s3 ls s3://uzhavan-backups/chroma/ | sort | tail -1 | awk '{print $4}') \
  /tmp/chroma_test.tar.gz
tar -xzf /tmp/chroma_test.tar.gz -C /tmp/chroma_restore_test/
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='/tmp/chroma_restore_test/chroma')
col = client.get_collection('tnau_knowledge')
print('ChromaDB chunk count:', col.count())
assert col.count() > 0, 'FAIL: collection is empty'
print('ChromaDB restore: PASS')
"

# 7. Cleanup
psql -U postgres -c "DROP DATABASE uzhavan_restore_test;"
rm -rf /tmp/chroma_restore_test /tmp/test_restore.sql.gz /tmp/chroma_test.tar.gz

echo "=== RESTORE TEST COMPLETE ==="
```

File the test result in `docs/incidents/restore-test-YYYY-MM.md`.
