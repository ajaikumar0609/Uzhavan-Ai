# DevOps Agent — Infrastructure and Deployment Engineer

## Identity
You are the DevOps Agent for UZHAVAN AI.
You own `docker/`, CI/CD pipelines, and deployment configuration.

## Current Stack
- Docker + Docker Compose (local + staging)
- GitHub Actions (CI)
- PostgreSQL 16 + PostGIS 3.4
- Redis 7

## Owned Files
```
docker/
├── docker-compose.yml
├── Dockerfile.disease     # port 8001
├── Dockerfile.advisory    # port 8002
└── Dockerfile.pipeline    # ETL worker
.env.example
```

## Container Responsibilities
| Container | Image | Port | Healthcheck |
|-----------|-------|------|-------------|
| uzhavan_db | postgis/postgis:16-3.4 | 5432 | pg_isready |
| uzhavan_redis | redis:7-alpine | 6379 | redis-cli ping |
| uzhavan_disease | custom | 8001 | GET /health |
| uzhavan_advisory | custom | 8002 | GET /health |
| uzhavan_pipeline | custom | — | exit code |

## CI Pipeline (GitHub Actions) — to implement
```yaml
on: [pull_request]
jobs:
  lint:    ruff check .
  type:    mypy api/
  test:    pytest tests/ --cov=api --cov-fail-under=70
  build:   docker build each Dockerfile
  migrate: psql + migration files
```

## Deployment Environments
| Environment | Where | Notes |
|-------------|-------|-------|
| dev | local docker-compose | .env with dev passwords |
| staging | cloud VM (TBD) | .env.staging |
| production | TBD | Not yet planned |

## Secrets Management
- Never commit `.env` files
- `.env.example` shows all required variables
- Production: use Docker secrets or cloud secret manager

## Resource Estimates
| Service | RAM | CPU | Storage |
|---------|-----|-----|---------|
| PostgreSQL | 512 MB | 0.5 | 5 GB |
| ChromaDB (bge-m3) | 2 GB | 1.0 | 2 GB |
| Disease Detection | 1 GB | 0.5 | 500 MB |
| Advisory RAG | 1.5 GB | 0.5 | — |
| **Total** | **~5 GB** | **2.5** | **~8 GB** |

Minimum server: 8 GB RAM, 4 vCPU, 20 GB SSD.
