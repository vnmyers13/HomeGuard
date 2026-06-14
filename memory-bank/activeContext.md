# Active Context

**Last Updated**: 2026-06-14

## Current Sprint: Sprint 6 (COMPLETED ✅)

**Sprint 6 Goal**: All dashboard pages complete. Full test suite passing. All 13 critical paths green.

### Sprint 6 Task Breakdown (6 tasks) - ALL COMPLETE
| # | Task | Status | Notes |
|---|------|--------|-------|
| S6-T1 | Common components (StatusBadge, ScoreGauge, DataTable, ScanProgress, EmptyState, Modal, Card) | COMPLETE ✅ | Extracted from inline page components |
| S6-T2 | Reports, SystemHealth, Settings pages | COMPLETE ✅ | Recharts charts, service status, preferences |
| S6-T3 | Onboarding wizard + routing updates | COMPLETE ✅ | 5-step wizard, onboarding store, new routes |
| S6-T4 | Frontend vitest setup + component tests | COMPLETE ✅ | vitest config, 8 test files, 59 tests |
| S6-T5 | Playwright E2E infrastructure | COMPLETE ✅ | playwright.config.ts, auth/navigation fixtures |
| S6-T6 | E2E tests (7 test suites) | COMPLETE ✅ | auth, onboarding, dashboard, profiles, requests, scans, settings |

**Current Version: 1.06**

## Sprint 6 Status: COMPLETE ✅
Sprint 6 delivered all dashboard pages (Reports, SystemHealth, Settings), the Onboarding wizard (5-step), 7 reusable components, full vitest test suite (50+ tests), and Playwright E2E tests (7 suites, 30+ tests). Version bumped to 1.05.

**Sprint 6 Score**: 6/6 tasks completed (100%).

## Sprint 5 Status: COMPLETE ✅
Sprint 5 delivered the removal request lifecycle tracking system, legal letter PDF generation (CCPA/GDPR), real-time scan progress via WebSockets, and a full frontend Requests page. Sprint 5.5 added test suite fixes, migration fixes, and password reset schemas. Sprint 5.6 completed password reset flow, batch profile operations, test import fixes, and DockerHub image publishing (v1.04).

**Sprint 5 Score**: All deliverables complete (v1.04 released).

## Sprint 4 Status: COMPLETE ✅
Sprint 4 delivered the full scan→exposure→removal→verification pipeline end-to-end. Mailwatcher classifying emails with two-stage classifier. All critical paths CP-02 through CP-05 and CP-09 passing.

**Sprint 4 Score**: 5/5 tasks completed (100%).

## Sprint 3 Status: COMPLETE ✅
Sprint 3 delivered the complete Playwright Executor microservice with browser pool, 16 action handlers, playbook execution engine, async job API. Mailwatcher email pipeline with IMAP client, classifier, notifier. Celery integration wiring run_scan_task to Playwright. 192 total tests (151 Playwright + 41 E2E).

**Sprint 3 Score: 9/9 tasks completed (100%)**

## Sprint 2 Status: COMPLETE
Sprint 2 delivered authentication, core REST API (auth, profiles, brokers, webhooks, scans), and React dashboard with 6 pages. All code written, routers registered, frontend routing configured. 45+ unit tests passing with 80%+ coverage.

**Sprint 2 Score: 6/6 tasks completed (100%)**

## Sprint 1 Status: COMPLETE
Sprint 1 delivered the project foundation: Docker Compose scaffold with 9 services, init.sh bootstrap script, database migration covering 20 tables across 7 schema domains, 8 API model files, FastAPI scaffold with middleware and health endpoints, 50+ broker playbook JSONs, Celery infrastructure, Playwright executor, and Mailwatcher.

---

## Important Patterns & Preferences
- **API responses**: Always wrapped in `{ success: bool, data?: ..., error_code?: string, message?: string }`
- **Auth**: JWT access tokens (short-lived) + refresh tokens (stored in Redis for blacklisting)
- **Database**: PostgreSQL with SQLAlchemy async, UUID primary keys, RowVersioned mixin for optimistic locking
- **Frontend**: React + Vite + Tailwind, Zustand for state, react-query for data fetching
- **Task queue**: Celery with Redis broker
- **Browser automation**: Playwright with JSON playbook-driven navigation
- **Testing**: pytest for backend, vitest for frontend components, Playwright for E2E

## Key Learnings
- npm not available on host machine - frontend builds inside Docker containers
- Scan trigger API creates DB record but Celery task dispatch was deferred to Sprint 3
- Logout requires Redis connectivity for token blacklisting
- Playwright service runs on port 8001 within Docker network
- Components should be extracted early for reusability
- vitest config needs jsdom environment for React component testing
- All JSX source files need `import React from 'react'` for vitest/jsdom compatibility
- vitest include pattern must exclude e2e/ directory (use `tests/unit/**/*.test.{js,jsx,ts,tsx}`)
- Test fixes: use `../../../src/` import paths from deeply nested test files, use `@testing-library/jest-dom` matchers via test-utils setupFile

## Next Immediate Steps - Sprint 7 (Final Sprint)
**Sprint 6 is complete** — all dashboard pages, Onboarding wizard, component library, test suite, and v1.06 release are done.

- **S7-T1**: Apply host security hardening — UFW, fail2ban, GPG backup
- **S7-T2**: Run all 12 security verification checks
- **S7-T3**: Configure backup schedule and verify restore
- **S7-T4**: Final test suite run — all 13 critical paths
- **S7-T5**: Onboard first household member and complete sign-off