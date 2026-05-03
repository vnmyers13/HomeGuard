# HomeGuard Privacy Platform

Automated personal data removal and monitoring platform. Discovers your personal data across data broker sites and submits removal requests automatically.

## Architecture

- **API**: FastAPI backend with async PostgreSQL
- **Frontend**: React + Vite + Tailwind CSS served via Nginx
- **Worker**: Celery distributed task queue with Redis broker
- **Playwright**: Headless browser microservice for broker site automation
- **Mailwatcher**: IMAP poller for email-based removal confirmations
- **n8n**: Workflow automation for broker discovery

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your secrets

# 2. Initial setup (generates secrets, runs migrations, seeds brokers)
chmod +x init.sh
./init.sh

# 3. Access services
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
api/              FastAPI backend
frontend/         React + Vite frontend
playwright/       Headless browser microservice
mailwatcher/      IMAP email poller
migrations/       Alembic database migrations
playbooks/        Broker automation playbooks
workflows/        n8n workflow exports
scripts/          Utility scripts
docker/           Docker configuration
tests/            Test suites
e2e/              End-to-end tests
```

## Testing

```bash
# Backend tests
pytest tests/ -v

# Frontend tests
cd frontend && npx vitest run

# E2E tests
cd e2e && npx playwright test
```

## Security

- All PII encrypted at rest using pgcrypto
- Append-only audit logging
- JWT-based authentication
- Rate limiting on all endpoints
- Network isolation between internal and external services

## License

Private - All rights reserved