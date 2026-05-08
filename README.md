# HomeGuard Privacy Platform

Automated personal data removal and monitoring platform. Discovers your personal data across data broker sites and submits removal requests automatically.

> **Status:** Sprint 1 Complete — Backend API foundation delivered. Sprint 2 (Frontend & Production Hardening) in progress.

---

## Architecture

```
┌───────────┐     ┌──────────┐     ┌──────────────┐
│  Frontend │────▶│   API    │────▶│   PostgreSQL │
│  (React)  │     │(FastAPI) │     │              │
└───────────┘     └────┬─────┘     └──────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌───────────┐ ┌────────┐ ┌────────────┐
    │  Celery   │ │ Redis  │ │ Playwright │
    │  Workers  │ │ Broker │ │ Executor   │
    └───────────┘ └────────┘ └────────────┘
          │
          ▼
    ┌───────────┐
    │Mailwatcher│
    │  (IMAP)   │
    └───────────┘
```

- **API**: FastAPI backend with async PostgreSQL
- **Frontend**: React + Vite + Tailwind CSS served via Nginx
- **Worker**: Celery distributed task queue with Redis broker
- **Playwright**: Headless browser microservice for broker site automation
- **Mailwatcher**: IMAP poller for email-based removal confirmations
- **n8n**: Workflow automation for broker discovery

## Services & Ports

| Service       | Port  | URL                                  | Description                |
|---------------|-------|--------------------------------------|----------------------------|
| Frontend      | 3000  | http://localhost:3000                | React dashboard            |
| API           | 8000  | http://localhost:8000                | FastAPI REST API           |
| API Docs      | 8000  | http://localhost:8000/docs           | Swagger/OpenAPI docs       |
| Redis         | 6379  | internal                             | Celery message broker      |
| PostgreSQL    | 5432  | internal                             | Primary database           |
| Playwright    | 8001  | internal                             | Browser automation         |
| Mailwatcher   | 8002  | internal                             | Email monitoring           |
| n8n           | 5678  | http://localhost:5678                | Workflow automation        |

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your secrets

# 2. Initial setup (generates secrets, runs migrations, seeds brokers)
chmod +x scripts/init.sh
./scripts/init.sh

# 3. Start all services
docker compose up -d

# 4. Access services
# Dashboard:  http://localhost:3000
# API Docs:   http://localhost:8000/docs
# n8n UI:     http://localhost:5678
```

## Common Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# View service logs
docker compose logs -f api

# Run database migrations
docker compose run --rm api alembic upgrade head

# Database shell
docker compose exec db psql -U homeguard homeguard

# Health check
curl http://localhost:8000/api/system/health

# Backup
./scripts/backup.sh
```

## Project Structure

```
HomeGuard/
├── api/                    # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── database.py         # Async SQLAlchemy setup
│   ├── security.py         # JWT auth, password hashing
│   ├── models/             # Database models (8 entities)
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic layer
│   ├── routers/            # API route handlers
│   └── workers/            # Celery task queue
│       └── tasks/          # Scanning, maintenance tasks
├── frontend/               # React + Vite frontend
│   ├── src/                # React components
│   ├── Dockerfile          # Frontend container
│   └── nginx.conf          # Nginx reverse proxy config
├── playwright/             # Headless browser microservice
│   ├── main.py             # Playwright API server
│   └── Dockerfile          # Browser container
├── mailwatcher/            # IMAP email poller
│   ├── main.py             # Email monitoring service
│   └── Dockerfile          # Mailwatcher container
├── migrations/             # Alembic database migrations
│   └── versions/           # Migration scripts
├── playbooks/              # Broker automation playbooks
│   ├── schema.json         # Playbook JSON Schema
│   └── brokers/            # 21 broker playbooks
├── workflows/              # n8n workflow exports
├── scripts/                # Utility scripts
│   ├── init.sh             # One-command setup
│   └── seed_brokers.py     # Broker data seeder
├── docker/                 # Docker configuration
│   └── postgres/           # PostgreSQL init scripts
├── tests/                  # Test suites
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── e2e/                    # End-to-end tests (Playwright)
├── memory-bank/            # Project documentation & context
└── docker-compose.yml      # Multi-service orchestration
```

## API Overview

### Core Endpoints

| Method | Endpoint                | Description              |
|--------|-------------------------|--------------------------|
| POST   | `/api/auth/register`    | Create new user account  |
| POST   | `/api/auth/login`       | Authenticate & get token |
| GET    | `/api/profiles/`        | List user profiles       |
| POST   | `/api/profiles/`        | Create new profile       |
| GET    | `/api/brokers/`         | List data brokers         |
| POST   | `/api/webhooks/`        | Create webhook           |
| GET    | `/api/system/health`    | Health check             |

### Authentication

All endpoints except `/auth/register`, `/auth/login`, and `/system/health` require a Bearer token:

```bash
curl -H "Authorization: Bearer <your_jwt_token>" \
  http://localhost:8000/api/profiles/
```

### HATEOAS Support

All list responses include `_links` metadata for API discoverability:

```json
{
  "data": [...],
  "total": 10,
  "_links": {
    "self": "/api/profiles/",
    "next": "/api/profiles/?page=2"
  }
}
```

## Data Models

| Model      | Description                          | Key Fields                    |
|------------|--------------------------------------|-------------------------------|
| User       | Platform users                       | email, hashed_password        |
| Identity   | Persons being monitored              | first_name, last_name, dob    |
| Profile    | Monitoring configurations            | identity_id, status           |
| Broker     | Data broker definitions              | domain, playbook              |
| Scan       | Scan execution records               | profile_id, status, findings  |
| Finding    | Discovered data points               | broker_id, data_type          |
| Request    | Removal request records              | finding_id, status            |
| Webhook    | Event notification endpoints         | url, events, secret           |
| AuditLog   | Immutable audit trail                | action, entity_type, details  |

## Broker Playbooks

HomeGuard supports **21 data brokers** out of the box:

- Spokeo, Whitepages, BeenVerified, InstantCheckMate
- PeopleFinder, Radaris, TruthFinder, Intelius
- PublicRecords, FastPeopleSearch, USSearch
- And 10 more...

Each broker has a JSON playbook defining automation steps for discovery and removal. See `playbooks/brokers/` for details.

## Testing

```bash
# Backend unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=api --cov-report=term-missing

# Frontend tests (when implemented)
cd frontend && npx vitest run

# E2E tests (when implemented)
cd e2e && npx playwright test
```

## Security

- All PII encrypted at rest using pgcrypto
- Append-only audit logging for compliance
- JWT-based authentication with refresh tokens
- Rate limiting on all endpoints
- Network isolation between internal and external services
- OWASP Top 10 mitigation patterns

## Development

### Tech Stack

| Layer       | Technology                              |
|-------------|-----------------------------------------|
| API         | Python 3.11, FastAPI, SQLAlchemy 2.0    |
| Frontend    | React 18, Vite, Tailwind CSS            |
| Database    | PostgreSQL 15                           |
| Cache/Queue | Redis 7                                 |
| Tasks       | Celery 5                                |
| Browser     | Playwright Python                       |
| Workflows   | n8n                                     |

### Memory Bank

Project context and decisions documented in `memory-bank/`:

- `projectbrief.md` — Project scope and requirements
- `productContext.md` — Why this project exists
- `systemPatterns.md` — Architecture decisions
- `techContext.md` — Technology choices and constraints
- `activeContext.md` — Current work focus
- `progress.md` — What works, what's left

## Roadmap

### Sprint 1 ✅ COMPLETE
- [x] All API models (8 entities)
- [x] Pydantic schemas (auth, profile, broker, webhook)
- [x] Business logic services (4 services)
- [x] API routers with authentication
- [x] Celery worker tasks (scanning, maintenance)
- [x] Unit tests for all services and routers
- [x] Docker infrastructure
- [x] Database migrations

### Sprint 2 🚧 IN PROGRESS
- [ ] React frontend dashboard
- [ ] End-to-end test suite
- [ ] Playwright executor hardening
- [ ] Mailwatcher Gmail API integration
- [ ] Performance benchmarking
- [ ] Security audit

### Sprint 3 (Planned)
- [ ] Broker automation execution
- [ ] Removal request workflows
- [ ] Email confirmation processing
- [ ] Reporting and analytics dashboard

## License

Private - All rights reserved