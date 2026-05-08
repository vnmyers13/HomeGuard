# Technical Context

## Technologies Used
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy async, Alembic migrations
- **Database**: PostgreSQL 15 with pgcrypto for PII encryption (pgp_sym_encrypt/pgp_sym_decrypt)
- **Message Queue**: Redis 7
- **Task Runner**: Celery 5.x with Beat scheduler
- **Browser Automation**: Playwright (Chromium) with browser pool
- **Frontend**: React 18, Vite, Tailwind CSS, Zustand, TanStack Query, MSW
- **Email**: aiosmtpd (testing), production SMTP for removal emails
- **PDF Generation**: WeasyPrint
- **Containerization**: Docker Compose (9 services)

## Development Setup
```bash
# Prerequisites
- Docker + Docker Compose
- Python 3.12+
- Node.js 18+

# Quick Start (Sprint 2+)
./init.sh          # Full stack setup with secrets, migrations, seeding

# Manual Setup
cp .env.example .env && chmod 600 .env          # Generate secrets
docker compose up -d db redis                   # Start infra first
sleep 10 && docker compose up -d                # Then rest
docker compose run --rm api alembic upgrade head  # Migrate DB
docker compose run --rm api python scripts/seed_brokers.py  # Seed brokers
```

## Key Technical Decisions
1. **PII Encryption**: All PII columns use SQLAlchemy TypeDecorator calling pgp_sym_encrypt/decrypt at the database level
2. **Audit Immutability**: `audit.audit_log` model overrides delete()/update() to raise NotImplementedError
3. **Auth**: JWT tokens stored in memory ( NEVER localStorage ), bcrypt password hashing, session tracking in `auth.sessions`
4. **Rate Limiting**: slowapi Limiter on FastAPI, 10 req/min per IP for auth endpoints
5. **Webhook Security**: HMAC-SHA256 signature verification with constant-time comparison

## Dependencies
- `fastapi`, `uvicorn[standard]` - Web framework
- `sqlalchemy[asyncio]`, `asyncpg` - Async database
- `alembic` - Migrations
- `pyjwt`, `passlib[bcrypt]` - Auth
- `celery[redis]`, `redis` - Task queue
- `playwright` - Browser automation
- `jinja2`, `weasyprint` - Template/PDF generation
- `pydantic` - Validation
- `httpx`, `jsonschema` - HTTP/JSON validation

## Testing
- **Backend**: pytest, pytest-asyncio, pytest-cov, testcontainers[postgres], aiosmtpd
  - `pytest tests/ --cov=api --cov=workers --cov=mailwatcher --cov=playwright`
- **Frontend**: Vitest, @testing-library/react, MSW
  - `cd frontend && npx vitest run`
- **E2E**: Playwright Test (TypeScript)
  - `cd e2e && npx playwright test`

## File Paths
- API: `api/` (main.py, models/, routers/, services/, schemas/, workers/)
- Frontend: `frontend/` (src/pages/, src/components/, src/stores/, src/hooks/)
- Playwright: `playwright/` (main.py, pool.py, executor.py, actions.py)
- Mailwatcher: `mailwatcher/` (main.py, imap_client.py, classifier.py)
- Migrations: `migrations/` (alembic.ini, env.py, versions/)
- Playbooks: `playbooks/brokers/*.json` (validated against playbooks/schema.json)
- Workflows: `workflows/` (n8n workflow JSON exports)