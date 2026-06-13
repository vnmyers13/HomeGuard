# OpenDataRemoval / HomeGuard

Monorepo for an automated PII removal platform.

## Quick start

```bash
cp .env.example .env          # fill in secrets
./scripts/init.sh             # builds images, starts infra, migrates, seeds, starts all services
```

## Services

| Service       | Port  | Entrypoint                       |
|---------------|-------|----------------------------------|
| API           | 8000  | `api/main.py:app` (FastAPI)      |
| Frontend      | 3000  | `frontend/` (Vite, dev on 5173)  |
| Playwright    | 8001  | `gw_playwright/main.py`          |
| Mailwatcher   | 8002  | `mailwatcher/main.py`            |
| Worker        | —     | Celery `workers.celery_app`      |
| Beat          | —     | Celery Beat scheduler            |
| n8n           | 5678  | Workflow automation              |

## Commands

```bash
docker compose up -d                               # start everything
docker compose up -d db redis                      # infra only (faster for dev)
docker compose logs -f api                         # watch a service
docker compose run --rm api alembic upgrade head   # migrations
docker compose run --rm api python scripts/seed_brokers.py
docker compose down
```

## Tests

```bash
# Backend (all)
pytest tests/ -v

# Backend (focused)
pytest tests/unit/api/test_auth.py -v
pytest tests/unit/api/test_profiles.py -v
pytest tests/integration/test_scan_to_removal.py -v

# Coverage
pytest --cov=api --cov-report=term-missing

# Frontend
cd frontend && npx vitest run
```

## Architecture

- **9 Docker services** across two networks: `opendataremoval_net` (internal) and `opendataremoval_egress` (bridge to outside).
- **Multi-schema PostgreSQL**: 9 schemas (auth, identity, registry, scanning, requests, audit, mail, reporting, archive). PII encrypted at rest via `pgcrypto` (`pgp_sym_encrypt`/`pgp_sym_decrypt`). The `EncryptedText` TypeDecorator in `api/models/__init__.py` handles this.
- **Celery pipeline**: `scan_broker → execute_removal_request → followup_removal_request`. Beat schedules daily scans at 2am, nightly screenshot purge at 3am, weekly broker health check, hourly followup checks.
- **Playbook-driven**: broker automation defined as JSON in `playbooks/brokers/`, validated against `playbooks/schema.json`.
- **HMAC webhooks**: n8n → API uses `X-Homeguard-Signature: HMAC-SHA256(body, N8N_WEBHOOK_SECRET)`.

## Key conventions

- **Import pattern** — modules use `try: from api.database import Base; except ImportError: from database import Base` to work both inside Docker (`/app`) and locally. The test `conftest.py` adds both project root and `api/` to `sys.path`.
- **JWT** — two security modules exist. `api/security.py` uses `SECRET_KEY`/`ACCESS_TOKEN_EXPIRE_MINUTES` (env). `api/services/auth_service.py` uses `JWT_SECRET`/`JWT_EXPIRY_MINUTES` (env). Both use bcrypt.
- **Integration tests** use an **in-memory SQLite** engine (class-scoped). The conftest replaces PostgreSQL `JSONB` columns with generic `JSON` and strips schemas from table metadata. Tests run inside a transaction that rolls back per class.
- **Unit tests** use `unittest.mock.MagicMock` with `pytest`. The `api/` import pattern is `from services.x_service import X` (no `api.` prefix needed because conftest adds `api/` to path).
- **Frontend** proxied in dev: `vite.config.js` forwards `/api → http://api:8000`. Tech: React 18, Zustand (state), TanStack Query (data), MSW (mock service worker for tests), Recharts, Tailwind CSS.
- **Playwright executor** lives in `gw_playwright/` (not `playwright/` as the README project tree suggests).
- **`play/`** is a standalone screenshot utility module — not a service.
- **No linter or typechecker config** found (no ruff, mypy, black in `pyproject.toml`).
- **Env vars** — 28+ vars in `.env.example`. Minimum required: `POSTGRES_DB/USER/PASSWORD`, `REDIS_PASSWORD`, `JWT_SECRET` (≥32 chars), `DB_ENCRYPTION_KEY` (64 hex chars), `ADMIN_USERNAME/PASSWORD`.

## Directory map

```
api/               → FastAPI backend (main.py, database.py, security.py)
  routers/         → auth, brokers, profiles, scans, webhooks
  models/          → SQLAlchemy models (9 schema modules)
  schemas/         → Pydantic request/response schemas
  services/        → Business logic layer
  workers/         → Celery app + tasks (scanning, maintenance, registry, requests)
frontend/          → React + Vite app
gw_playwright/     → Playwright microservice (executor, pool, actions)
mailwatcher/       → IMAP email poller + classifier
migrations/        → Alembic versions
playbooks/brokers/ → JSON broker automation playbooks
workflows/         → n8n workflow exports
play/              → standalone screenshot utility (not a service)
e2e/               → pytest-based e2e tests (not Playwright test runner)
scripts/           → init.sh, seed_brokers.py
memory-bank/       → project documentation (projectbrief, systemPatterns, techContext, etc.)
```

## Watching for reference documents

Root-level `OpenDataRemoval_*.json` files are architecture/planning/spec documents, not executable code. Trust `docker-compose.yml`, `pyproject.toml`, `api/*.py`, and other runnable sources instead.
