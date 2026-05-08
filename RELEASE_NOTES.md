# HomeGuard Release Notes

## v0.1.0 — Sprint 1: Backend API Foundation (May 8, 2026)

### Overview
This release delivers the complete backend API foundation for HomeGuard, an automated personal data removal and monitoring platform. The system discovers personal data across 21 data broker sites and provides the infrastructure for automated removal requests.

### What's Included
- Full REST API with 4 core resource endpoints (auth, profiles, brokers, webhooks)
- 8 database models with relationships and constraints
- JWT authentication with password hashing
- Celery distributed task queue for background scanning
- Docker multi-service orchestration (6 services)
- Database migrations with Alembic
- Unit test suite for all services and routers
- 21 data broker playbooks

### New Features

#### Authentication System
- User registration with email validation
- JWT-based authentication (access + refresh tokens)
- Password hashing using bcrypt
- Token-based session management

#### Profile Management
- Create and manage monitoring profiles for individuals
- Link profiles to identities (persons being monitored)
- Configure scan frequency and broker scope per profile
- CRUD operations with full audit trail

#### Broker Discovery
- 21 pre-configured data broker playbooks
- Broker metadata API (domain, category, support status)
- JSON Schema validation for playbooks
- Extensible playbook format for adding new brokers

#### Webhook Integration
- Event-driven notifications to external endpoints
- Configurable event filtering (scan_complete, request_created, etc.)
- HMAC signature verification for webhook payloads
- Automatic retry with exponential backoff

#### Background Tasks
- Celery worker queue for async scan execution
- Scheduled maintenance tasks (cleanup, reporting)
- Scan lifecycle management (pending → running → complete/failed)
- Redis-backed task broker

### Technical Details

#### Database Schema
| Table      | Purpose                          | Key Features              |
|------------|----------------------------------|---------------------------|
| users      | Platform authentication          | email, hashed_password    |
| identities | Persons being monitored           | PII fields, encrypted     |
| profiles   | Monitoring configurations        | identity_ref, status      |
| brokers    | Data broker definitions          | domain, playbook JSON     |
| scans      | Scan execution records           | profile_ref, findings     |
| findings   | Discovered data points           | broker_ref, data_type     |
| requests   | Removal request tracking         | finding_ref, status       |
| webhooks   | Event notification endpoints     | url, events, secret       |
| audit_logs | Immutable audit trail            | append-only, indexed      |

#### API Endpoints
- `POST /api/auth/register` — Create new user account
- `POST /api/auth/login` — Authenticate and receive JWT token
- `GET /api/profiles/` — List user profiles (paginated)
- `POST /api/profiles/` — Create new monitoring profile
- `GET /api/profiles/{id}` — Get profile details
- `PUT /api/profiles/{id}` — Update profile configuration
- `DELETE /api/profiles/{id}` — Delete profile (soft delete)
- `GET /api/brokers/` — List available data brokers
- `GET /api/brokers/{id}` — Get broker details and playbook
- `POST /api/webhooks/` — Create webhook subscription
- `GET /api/webhooks/` — List webhooks
- `DELETE /api/webhooks/{id}` — Delete webhook
- `GET /api/system/health` — Health check endpoint

#### Architecture
```
Frontend (React) ──▶ API (FastAPI) ──▶ PostgreSQL
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
      Celery Workers   Redis    Playwright Executor
           │
           ▼
      Mailwatcher (IMAP)
```

### Dependencies
- Python 3.11
- FastAPI 0.104+
- SQLAlchemy 2.0 (async)
- PostgreSQL 15
- Redis 7
- Celery 5
- Pydantic 2.0
- Playwright Python
- Alembic migrations

### Security
- All PII encrypted at rest using pgcrypto
- Append-only audit logging for compliance
- JWT authentication with refresh tokens
- Rate limiting on all endpoints
- Network isolation between internal services
- OWASP Top 10 mitigation patterns

### Testing
- Unit tests for all service layer functions
- Unit tests for all API routers
- Test fixtures and conftest setup
- pytest with coverage reporting

### Known Limitations
- Frontend dashboard not yet implemented (Sprint 2)
- Playwright executor needs production hardening
- Mailwatcher using IMAP (Gmail API migration planned)
- No end-to-end test suite yet
- Performance benchmarks not established

### Breaking Changes
None — this is the first release.

### Migration Notes
No migrations needed for first deployment. Use `scripts/init.sh` for one-command setup:
```bash
cp .env.example .env
# Edit .env with your secrets
chmod +x scripts/init.sh
./scripts/init.sh
docker compose up -d
```

### Upgrade Guide
N/A — first release.

---

## Changelog

### v0.1.0 (2026-05-08)

#### Added
- Complete FastAPI backend with 4 resource routers
- 8 database models with full relationships
- JWT authentication system
- Celery task queue for background scanning
- Docker multi-service orchestration (6 services)
- Database migrations with Alembic
- 21 data broker playbooks
- Webhook notification system
- Unit test suite (services + routers)
- Memory Bank documentation
- Project scaffolding and configuration

#### Changed
- N/A

#### Fixed
- N/A

---

## Upcoming (Sprint 2)
- React frontend dashboard
- End-to-end test suite with Playwright
- Playwright executor production hardening
- Mailwatcher Gmail API integration
- Performance benchmarking
- Security audit

## Upcoming (Sprint 3)
- Broker automation execution engine
- Removal request workflow processing
- Email confirmation processing
- Reporting and analytics dashboard

---

## Support
For issues or questions, please refer to the project documentation in `memory-bank/` or consult the API docs at `http://localhost:8000/docs`.

## License
Private - All rights reserved