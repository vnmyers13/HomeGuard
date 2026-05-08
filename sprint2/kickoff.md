# Sprint 2 Kickoff - Core API: Auth, Profiles, Brokers & n8n

## Sprint Metadata
- **Sprint Number**: 2
- **Title**: Core API - Auth, Profiles, Brokers & n8n
- **Goal**: Complete the core API layer with authentication, profile management, broker registry CRUD, and n8n webhook integration
- **Duration**: 5 days (May 3 - May 7, 2026)
- **Start Date**: 2026-05-03
- **End Date**: 2026-05-07
- **Status**: IN_PROGRESS

## Sprint 1 Summary
Sprint 1 delivered the project foundation: Docker Compose scaffold with 9 services, init.sh bootstrap script, database migration covering 20 tables across 7 schema domains, 8 API model files, FastAPI scaffold with middleware and health endpoints, 50+ broker playbook JSONs, Celery infrastructure, Playwright executor, and Mailwatcher.

**Sprint 1 Score**: 4/5 tasks completed (S1-T5 API models unit tests deferred to Sprint 2).

## Sprint 2 Tasks (6 tasks, ~19.5 hours estimated)

| ID | Title | Est. Hours | Status | Dependencies |
|----|-------|-----------|--------|--------------|
| S2-T1 | Auth router (register, login, verify) | 3 | NOT_STARTED | None |
| S2-T2 | Auth service (JWT, bcrypt, rate limiting) | 2.5 | NOT_STARTED | None |
| S2-T3 | Profile routers + service (CRUD, encryption, versioning) | 4 | NOT_STARTED | S2-T2 |
| S2-T4 | Broker routers + service (playbook validation, scan trigger) | 3.5 | NOT_STARTED | S2-T3 |
| S2-T5 | n8n webhook router (HMAC verification, schema validation) | 3 | NOT_STARTED | S2-T2 |
| S2-T6 | Init.sh updates + backend unit tests (45+ tests) | 3.5 | NOT_STARTED | S2-T1..T5 |

## Sprint Gate Checks
All must pass to close the sprint:

1. `docker compose up -d` → all 9 services are Up
2. `curl http://localhost:8000/api/system/health` → `{"status": "healthy"}`
3. `curl -X POST /api/auth/register` → 201 + JWT token
4. `curl -X POST /api/auth/login` → 200 + JWT token
5. `curl -X POST /api/profiles` → 201 + profile ID
6. `curl -X POST /api/profiles/{id}/fields` → 201 + field ID
7. `curl -X POST /api/brokers` → 201 + broker ID
8. `curl -X POST /api/webhooks/n8n` → 200 + discovery response
9. `pytest tests/unit/api/ -v --tb=short` → 45+ passed, 0 failed
10. `pytest tests/ --cov=api --cov=workers --cov=mailwatcher --cov=playwright` → TOTAL >= 80%

## Critical Path Requirements (Sprint 2 Impact)
- **CP-10**: JWT never stored in localStorage - auth service must keep tokens in memory only
- **CP-07**: PII encrypted at rest - profile service must use TypeDecorator encryption round-trip
- **CP-08**: Audit log immutability - all profile/broker mutations must create audit_log entries

## Files to Create/Modify
```
api/routers/__init__.py              # NEW - Sprint 2
api/routers/auth.py                  # NEW - Sprint 2, S2-T1
api/routers/profiles.py              # NEW - Sprint 2, S2-T3
api/routers/brokers.py               # NEW - Sprint 2, S2-T4
api/routers/webhooks.py              # NEW - Sprint 2, S2-T5

api/services/__init__.py             # NEW - Sprint 2
api/services/auth_service.py         # NEW - Sprint 2, S2-T2
api/services/profile_service.py      # NEW - Sprint 2, S2-T3
api/services/broker_service.py       # NEW - Sprint 2, S2-T4

api/schemas/__init__.py              # NEW - Sprint 2
api/schemas/auth.py                  # NEW - Sprint 2, S2-T1
api/schemas/profile.py               # NEW - Sprint 2, S2-T3
api/schemas/broker.py                # NEW - Sprint 2, S2-T4

tests/unit/api/__init__.py           # NEW - Sprint 2
tests/unit/api/test_auth.py          # NEW - Sprint 2, S2-T6 (10 tests)
tests/unit/api/test_profiles.py      # NEW - Sprint 2, S2-T6 (12 tests)
tests/unit/api/test_brokers.py       # NEW - Sprint 2, S2-T6 (10 tests)
tests/unit/api/test_webhooks.py      # NEW - Sprint 2, S2-T6 (8 tests)

init.sh                              # UPDATE - Sprint 2, S2-T6
api/main.py                          # UPDATE - Sprint 2 (router includes)
```

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| DB_ENCRYPTION_KEY generation fails on target | Low | High | Fallback to deterministic UUID from .env.example |
| Docker network conflicts on host | Medium | Medium | Use unique compose project name via COMPOSE_PROJECT_NAME |
| Broker playbook schema changes | Low | Low | Schema is stable; validate before each router integration |
| Test coverage gap on profile_service | Medium | Low | Start with baseline tests, expand during S2-T6 sweep |

## Notes
- All API responses follow the standard format: `{"success": bool, "data"?: any, "error_code"?: str}`
- Auth endpoints are rate-limited to 10 req/min per IP using slowapi + Redis
- n8n webhook HMAC uses `N8N_WEBHOOK_SECRET` from environment
- Broker scan triggers Celery task `scanning.scan_broker_task` (worker infrastructure exists from Sprint 1)