# UZHAVAN AI — Production Environment Guide
**Date:** 2026-09-26

---

## 1. Backend Environment Variables

All variables are read by `backend/shared/settings.py` at startup. Missing or invalid settings cause a clear startup error (never a silent default). Copy `.env.example` and fill in all required values.

### Required in all environments

| Variable | Description | Example |
|----------|-------------|---------|
| `ENV` | Runtime environment | `development` / `test` / `production` |
| `JWT_SECRET` | HS256 signing key (≥ 32 chars, not a known placeholder) | see §1.1 |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/uzhavan` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |

### Required in production only

| Variable | Description |
|----------|-------------|
| `CORS_ORIGINS` | Comma-separated allowed origins (must be https://) |
| `ALLOW_ANONYMOUS` | Must be `false` in production |
| `OTP_HMAC_KEY` | Key for HMAC-SHA256 OTP hashing (≥ 32 chars) |

### Optional — AI / LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama` / `claude` / `openai` |
| `ANTHROPIC_API_KEY` | — | Required when `LLM_PROVIDER=claude` |
| `CLAUDE_MODEL` | `claude-opus-5-5` | Anthropic model ID |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `OLLAMA_HOST` / `OLLAMA_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `llama3.2` | Model tag |
| `LLM_TIMEOUT_S` | `30.0` | LLM call timeout (seconds) |

### Optional — Knowledge / RAG

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_PATH` | `./rag/chroma` | ChromaDB data directory (520 TNAU chunks pre-loaded) |
| `EMBED_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `TOP_K_RETRIEVAL` | `5` | RAG top-K chunks per query |
| `RAG_SCORE_THRESHOLD` | `0.4` | Minimum cosine similarity |

### Optional — Disease / Satellite

| Variable | Default | Description |
|----------|---------|-------------|
| `DISEASE_MODEL_APPROVED` | `false` | Must be `false` until G1–G5 gates pass |
| `DISEASE_SERVICE_URL` | — | ML inference service (not yet connected) |
| `DISEASE_TIMEOUT_S` | `15.0` | ML call timeout |

### Optional — Voice

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_PROVIDER` | `local` | STT provider (`local` uses Whisper via Ollama) |
| `TTS_PROVIDER` | `local` | TTS provider |
| `GOOGLE_APPLICATION_CREDENTIALS` | — | Path to Google SA JSON (if using Google TTS/STT) |

### Development-only

| Variable | Default | Description |
|----------|---------|-------------|
| `OTP_DEV_LOG` | `false` | Set `true` to log OTP codes to console in `ENV=development` |

---

## 1.1 Generating JWT_SECRET

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Store the output in `.env` as `JWT_SECRET=<value>`. Never commit `.env` to git (it is in `.gitignore`).

---

## 2. Starting the Backend

```bash
cd uzhavan_platform
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Copy and fill in .env
cp .env.example .env
# edit .env

# Apply migrations
psql "$DATABASE_URL" -f database/migrations/001_create_farmers.sql
psql "$DATABASE_URL" -f database/migrations/002_create_farms.sql
psql "$DATABASE_URL" -f database/migrations/003_otp_and_refresh.sql
psql "$DATABASE_URL" -f database/migrations/004_knowledge.sql
psql "$DATABASE_URL" -f database/migrations/005_market_mandi_prices.sql
psql "$DATABASE_URL" -f database/migrations/006_government_schemes.sql
psql "$DATABASE_URL" -f database/migrations/007_soil_tests.sql
psql "$DATABASE_URL" -f database/migrations/008_diary_entries.sql

# Load data
python scripts/load_mandi_prices.py   # 1,068,236 rows
python scripts/load_schemes.py        # 136 schemes

# Start server
uvicorn backend.conversation.main:app --host 0.0.0.0 --port 8000
```

---

## 3. Flutter Frontend Profiles

The Flutter app reads `API_BASE_URL` at build time via `--dart-define`. There is no runtime `.env` file.

### Profile 1 — Android Emulator (no `adb reverse`)
```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```
`10.0.2.2` is the emulator's loopback alias for the host machine's `localhost`.

### Profile 2 — Android Emulator (with `adb reverse`)
```bash
adb reverse tcp:8000 tcp:8000
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

### Profile 3 — Physical Device on LAN
```bash
# Find your Mac's LAN IP: ifconfig | grep 192.168
flutter run --dart-define=API_BASE_URL=http://192.168.x.x:8000
```

### Profile 4 — Production
```bash
flutter build apk --release --dart-define=API_BASE_URL=https://api.uzhavan.ai
flutter build appbundle --release --dart-define=API_BASE_URL=https://api.uzhavan.ai
```
Production builds reject `http://` URLs at startup (requires `https://` unless `ALLOW_INSECURE_API=true` is also passed).

---

## 4. Running Tests

### Backend
```bash
cd uzhavan_platform
pip install -r requirements-dev.txt
pytest tests/ -q          # 241 tests, ~38 s
```

### Flutter
```bash
cd uzhavan_flutter
flutter test              # 144 tests, exit 0
```

---

## 5. Security Checklist Before Production Launch

- [ ] `JWT_SECRET` generated with `secrets.token_urlsafe(48)`, stored in `.env`  
- [ ] `ENV=production` in server environment  
- [ ] `OTP_DEV_LOG` not set (or `false`) in production  
- [ ] `ALLOW_ANONYMOUS=false` in production  
- [ ] SMS provider configured (`ANTHROPIC_API_KEY` or Twilio/MSG91)  
- [ ] `LLM_PROVIDER=claude` with valid `ANTHROPIC_API_KEY` (or `openai`)  
- [ ] `DISEASE_MODEL_APPROVED=false` (never changed until G1–G5 gates pass)  
- [ ] `.env` not committed to git (`git status` shows it as untracked or ignored)  
- [ ] CORS_ORIGINS set to your production domain only  
- [ ] HTTPS termination on the load balancer / reverse proxy  
- [ ] PostgreSQL: connection string uses SSL (`?sslmode=require`)  
