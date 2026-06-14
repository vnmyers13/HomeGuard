# HomeGuard Release Notes

## Version 1.06 - Frontend Pages, E2E Tests & Complete Test Suite (2026-06-14)

### Overview
Sprint 6 delivers all remaining dashboard pages, the Onboarding wizard, reusable component library, full vitest test suite (59 tests), and Playwright E2E tests (7 suites, 30+ tests).

### New Features

#### Dashboard Pages
- **Reports** - Exposure trends chart, broker summary table, removal statistics with Recharts visualizations
- **System Health** - Service status grid, disk usage monitoring, alert display
- **Settings** - Notification preferences, account settings, data retention controls (3 tabs)

#### Onboarding Wizard
- **5-step flow** - Welcome → Household → Profile → Email → First Scan
- **Zustand store** - Persistent wizard state across steps
- **Validation** - Required field validation with error messages
- **Navigation** - Back/Continue buttons, skip option, completion tracking

#### Component Library
- **StatusBadge** - 18+ status types with color-coded badges
- **ScoreGauge** - Circular score display (0-100) with color gradient
- **Card** - Reusable card wrapper with dark mode support
- **Modal** - Backdrop, Escape key, size variants (sm/xl/2xl)
- **EmptyState** - Empty state with optional CTA button
- **DataTable** - Sortable, paginated, searchable table
- **ScanProgress** - Progress bar + step list with WebSocket support

#### Test Suite
- **Vitest config** - jsdom environment, 75% coverage threshold
- **59 unit tests** - All components and stores tested
- **7 E2E suites** - Auth, onboarding, dashboard, profiles, requests, scans, settings
- **Playwright fixtures** - Auth and navigation helpers

### API Endpoints Added
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/reports/exposure-trends | Yes | Exposure trend data |
| GET | /api/reports/broker-summary | Yes | Broker summary data |
| GET | /api/reports/removal-stats | Yes | Removal statistics |
| GET | /api/system/health | Yes | System health status |

### Changes
- **Version bump** - 1.05 → 1.06
- **App routes** - Added Reports, SystemHealth, Settings, Onboarding routes
- **DashboardLayout** - Added Reports, Notifications, System Health nav links
- **Test fixes** - Fixed vitest config, React imports, test assertions

---

## Version 1.04 - Password Reset, Batch Operations & Test Suite Fixes (2026-06-13)

### Overview
Sprint 5.6 completes the password reset flow, batch profile operations, and fixes the test suite. DockerHub images are now available for all services.

---

### New Features

#### Password Reset Flow
- **Forgot password** - POST /auth/forgot-password generates 6-digit reset code
- **Magic link generation** - Creates time-limited reset links with email delivery
- **Code verification** - POST /auth/verify-code validates reset code
- **Password reset** - POST /auth/reset-password sets new password
- **Token model** - PasswordResetToken stored in DB with expiry and usage tracking
- **Session revocation** - All active sessions invalidated on password reset

#### Batch Profile Operations
- **Batch create** - POST /profiles/batch creates up to 100 profiles per request
- **Per-profile tracking** - Success/failure tracking in batch responses
- **Validation** - Full profile validation applied to each profile in batch

#### Test Suite Fixes
- **Import fixes** - pytest.importorskip for mailwatcher/playwright test files
- **81 tests pass** - All unit and integration tests passing
- **162 skipped** - Mailwatcher/playwright tests skipped in API container (separate services)

#### DockerHub Images
- **All services** - API, frontend, playwright, mailwatcher images on DockerHub
- **Versioned tags** - Both 1.04 and latest tags for each image
- **DockerHub repo** - vnmyers13/homeguard-api, vnmyers13/homeguard-frontend, etc.

---

### API Endpoints Added
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/forgot-password | public | Generate password reset code |
| POST | /auth/verify-code | public | Verify reset code |
| POST | /auth/reset-password | public | Reset password with code |
| POST | /profiles/batch | required | Batch create profiles |

---

### Changes
- **docker-compose.yml** - Updated all services to use DockerHub images (`vnmyers13/homeguard-*:1.04`)
- **Test imports** - Fixed mailwatcher/playwright test imports for container compatibility
- **Version bump** - 1.03 → 1.04

---

### Migration Notes
- **Password reset tokens** - New `password_reset_tokens` table added to `auth` schema
- **Batch operations** - Rate limiting: max 100 profiles per batch request

---

## Version 1.02 - Removal Request Tracking & Real-Time Progress (2026-06-13)

### Overview
Sprint 5 delivers the removal request lifecycle tracking system, legal letter PDF generation, and real-time scan progress via WebSockets. Users can now create removal requests, track their status through the confirmation pipeline, generate CCPA/GDPR legal letters, and monitor scan progress in real-time.

---

### New Features

#### Removal Request CRUD API
- **Request schemas** - Pydantic models for RemovalRequest, RequestStatusLog, Followup, VerificationScan
- **Full CRUD endpoints** - GET/POST /api/requests, GET/PATCH/DELETE /api/requests/:id
- **Status logs** - Track status changes with /api/requests/:id/logs
- **Follow-up management** - Create and track follow-up attempts with /api/requests/:id/followups
- **Verification scans** - Schedule and track verification scans with /api/requests/:id/verification-scans
- **Pagination** - All list endpoints support limit/offset pagination (default 50, max 200)

#### Legal Letter PDF Generation
- **CCPA letters** - California Consumer Privacy Act deletion demand letters
- **GDPR letters** - General Data Protection Regulation erasure requests
- **reportlab rendering** - Professional PDF output with formatted headers, body text, and signatures
- **Fallback rendering** - Graceful text-based PDF if reportlab unavailable
- **Download endpoint** - GET /api/requests/:id/pdf?letter_type=ccpa|gdpr

#### WebSocket Scan Progress
- **Real-time updates** - WebSocket endpoint at ws://host/ws/scans/{scan_id}
- **Connection manager** - Singleton WebSocketManager with async lock for thread safety
- **Step-by-step progress** - Each scan step pushes updates to connected clients
- **Automatic cleanup** - Connections cleaned up on scan completion or client disconnect

#### Frontend Requests Page
- **List view** - Filterable table with status badges, method icons, pagination
- **Detail view** - Request status, follow-up timeline, verification scan history
- **Status actions** - One-click status updates (submitted, confirmed_removed, still_listed, failed)
- **Follow-up creation** - Add email or legal follow-ups from detail view
- **PDF download** - Download legal letters directly from the UI
- **Create modal** - New request form with profile/broker/method selection
- **Navigation** - Added to sidebar with document icon

#### Celery Task Dispatch Fix
- **ScanRun model reference** - Fixed DeletionScan → ScanRun in scans.py
- **Celery integration** - Connected scan triggering to run_scan_task.delay()
- **Async context fix** - Proper single-async-context for execute_removal_request/followup_removal_request

---

### API Endpoints Added
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/requests | Yes | List removal requests (paginated) |
| POST | /api/requests | Yes | Create new removal request |
| GET | /api/requests/:id | Yes | Get request detail |
| PATCH | /api/requests/:id | Yes | Update request (status, confirmation) |
| DELETE | /api/requests/:id | Yes | Delete removal request |
| GET | /api/requests/:id/logs | Yes | Get request status logs |
| GET | /api/requests/:id/followups | Yes | Get follow-up attempts |
| POST | /api/requests/:id/followups | Yes | Create follow-up |
| GET | /api/requests/:id/verification-scans | Yes | Get verification scans |
| POST | /api/requests/:id/verification-scans | Yes | Schedule verification scan |
| GET | /api/requests/:id/pdf | Yes | Download legal letter PDF |
| WS | /api/ws/scans/{scan_id} | Yes | Real-time scan progress |

---

### Files Added (6)
- `api/schemas/request.py` - Removal request Pydantic schemas
- `api/routers/requests.py` - Full CRUD router for removal requests
- `api/services/websocket_manager.py` - WebSocket connection manager
- `api/routers/ws.py` - WebSocket endpoint
- `api/services/pdf_service.py` - Legal letter PDF generation
- `frontend/src/pages/Requests.jsx` - Removal requests frontend page

### Files Modified (6)
- `api/main.py` - Registered requests and ws routers
- `api/routers/scans.py` - Fixed DeletionScan→ScanRun, connected Celery dispatch
- `frontend/src/App.jsx` - Added /requests route
- `frontend/src/components/DashboardLayout.jsx` - Added Requests nav, fixed paths
- `frontend/src/lib/api.js` - Added requestsApi, connectScanProgress
- `frontend/package.json` - Version 1.01 → 1.02

---

## Version 1.01 - Critical Bug Fixes & Release Readiness (2026-06-13)

### Overview
First production-ready release of HomeGuard (formerly OpenDataRemoval). This release fixes 8 critical bugs that prevented the platform from running reliably, adds the missing alerts API, resolves the project name transition from OpenDataRemoval to HomeGuard, and establishes a complete release pipeline with Gitea publishing and Docker image support.

---

### Bug Fixes

#### Critical Fixes (Prevent Runtime Failures)
- **Missing alerts router** - `api/routers/alerts.py` was referenced but did not exist, causing API startup crash. Created with list, detail, and acknowledge endpoints for security alert management.
- **__init__.py import failures** - `api/workers/tasks/__init__.py` imported 10 non-existent symbols, crashing any module that imported from the tasks package. Fixed to reference actual function names.
- **Circular import (scanning ↔ requests)** - `scanning.py` and `requests.py` imported from each other at module level, causing one module to receive `None`. Resolved with lazy imports inside function bodies.
- **Undefined schedule_follow_up_check** - Function was defined but never imported due to circular dependency. Now properly imported in both scanning.py and requests.py.

#### Celery Worker Fixes
- **Nested asyncio.run()** - `execute_removal_request` and `followup_removal_request` called `asyncio.run()` inside an already-running event loop, causing `RuntimeError`. Restructured to use single async context.
- **autodiscover_packages argument format** - Received tuples instead of flat string list, preventing task discovery. Fixed argument unpacking.
- **Missing @celery_app.task decorators** - `check_broker_opt_out_urls` and `upsert_broker_from_discovery` in `registry.py` were plain functions, not registered as Celery tasks. Added decorators.

#### Mailwatcher Fixes
- **Wrong env var prefix** - Used `HOMEGUARD_*` instead of `MAILWATCHER_*`, causing config loading failures. Fixed all references.
- **Non-static method** - `_build_config_dict` was an instance method but called without an instance. Made it a `@staticmethod`.

### Improvements
- **Project name** - Officially renamed from OpenDataRemoval to HomeGuard across API title, startup logs, and frontend package name
- **Release pipeline** - Established Gitea publishing workflow with automated tag-based releases
- **Release checklist** - Comprehensive 9-phase release process documented in `release_checklist.json`

---

## Version 0.3.0 - Sprint 3 Complete (2026-05-09)

### Overview
Sprint 3 delivers the Playwright executor microservice, Celery task integration, Mailwatcher email processing pipeline, n8n workflow orchestration, and a comprehensive test suite with 237 total tests (45 API + 151 Playwright unit + 41 E2E). The system can now execute end-to-end deletion scan campaigns: discovering profiles on data brokers, navigating deletion flows, handling CAPTCHAs and confirmations, and processing email responses.

---

### New Features

#### Playwright Executor Service
- **Browser Pool** - Anti-detection Chromium contexts with randomized UA (Chrome 65%, Safari 20%, Firefox 15%), viewport randomization, and `navigator.webdriver` patching
- **Token Resolver** - SafeDict template engine with derived tokens (first_name/last_name from full_name, city/state/zip from address, dob_month/dob_year from DOB)
- **16 Action Handlers** - navigate, fill_form, click, wait, screenshot, submit, select, hover, scroll, type_text, check_text, uncheck_text, download, conditional, loop, execute_js
- **Playbook Executor** - Phase-loop engine with confirmation detection, CAPTCHA handling, error classification, and automatic screenshot capture on failure
- **Async Job API** - Submit/poll/cancel endpoints with job lifecycle management (queued → running → completed/error/requires_manual/cancelled)
- **Error Classification** - Maps Playwright exceptions to structured error_type with recovery_hint (captcha, timeout, element_not_found, navigation_failed, etc.)

#### Celery Task Integration
- **Scan Task Execution** - `run_scan_task` now dispatches jobs to Playwright service via HTTP
- **Per-Broker Results** - Structured results stored with status, error_type, recovery_hint, and evidence URLs
- **Graceful Cancel** - Running scans can be cancelled via API, propagating to Playwright job cancellation

#### Mailwatcher Email Processing
- **IMAP Polling** - Configurable mailbox monitoring with TLS support
- **Email Parsing** - AI-assisted classification of broker confirmation responses
- **Webhook Notifications** - Automatic notifications on processed emails
- **Health & Status API** - FastAPI endpoints for monitoring and integration

#### n8n Workflow Orchestration
- **Scan Orchestration** - End-to-end workflow coordinating API → Celery → Playwright → Mailwatcher
- **Opt-Out Orchestration** - Automated opt-out request processing across brokers
- **Email Processing** - Workflow for handling and classifying broker email responses
- **Error Handling** - Centralized error recovery and retry workflows

#### Comprehensive Test Suite
- **151 Playwright Unit Tests** - 6 test files covering token_resolver, actions, executor, pool, error_classifier, playbook_validator
- **41 E2E Tests** - 3 test files covering API integration, Playwright service, and full scan flows
- **237 Total Tests** - 45 API + 151 Playwright + 41 E2E = 100% coverage of Sprint 2 + Sprint 3 code

---

## Version 0.2.0 - Sprint 2 Complete (2026-05-08)

### Overview
Sprint 2 delivers a fully functional authentication system, core REST API for household management, and a React-based dashboard frontend. Users can now register accounts, manage household profiles, browse data broker playbooks, and prepare for deletion scan campaigns.

---

### New Features

#### Authentication System
- **User Registration** - Create account with email + password, automatic household creation
- **JWT Login** - Access token (15min) + Refresh token (7day) with Redis-backed token blacklisting
- **Token Refresh** - Seamless access token renewal without re-login
- **Secure Logout** - Refresh token blacklisting prevents reuse after logout

#### Household Profiles API
- Full CRUD operations for household member profiles
- UUID-based identifiers for privacy and security
- Support for name, date of birth, address history, email aliases, phone aliases
- Optimistic concurrency control via RowVersioned mixin

#### Data Broker Catalog API
- List all available broker playbooks from JSON directory
- Detailed broker view including navigation steps, search selectors, deletion instructions
- 28 broker playbooks pre-loaded (Spokeo, Whitepages, Radaris, InstantCheckMate, etc.)

#### Webhook Endpoints API
- Create webhook endpoints for external integrations (n8n, Zapier, etc.)
- Token-based authentication for webhook deliveries
- List and delete existing endpoints

#### Deletion Scans API
- List all deletion scan records with status tracking
- Detailed scan view with per-broker results and evidence URLs
- Trigger new scans for a profile against all or specific brokers
- Cancel running scans gracefully

#### React Dashboard Frontend
- **Login Page** - Email/password form with API integration
- **Register Page** - Account creation with auto-login on success
- **Dashboard Overview** - Stats cards, activity feed, quick actions
- **Profile Management** - Add/edit/delete household members with form validation
- **Household View** - Household-level management page
- **Broker Catalog** - Browse 28 data brokers with status badges and details
- **Scan History** - View scan results, trigger new scans, cancel running ones
- **Protected Routing** - Unauthenticated users redirected to login
- **Persistent Sessions** - Auto-refresh tokens on storage recovery

---

### Technical Architecture

#### Backend Stack
| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python 3.11) |
| Database | PostgreSQL 15 (async via asyncpg) |
| ORM | SQLAlchemy 2.0 with UUID primary keys |
| Auth | JWT (access + refresh tokens) |
| Passwords | bcrypt via Passlib |
| Cache/Queue | Redis 7 |
| Task Queue | Celery 5.3 |
| Migrations | Alembic |
| Validation | Pydantic v2 |

#### Frontend Stack
| Component | Technology |
|-----------|------------|
| Framework | React 18 |
| Build Tool | Vite 5 |
| Styling | Tailwind CSS 3.4 |
| State Management | Zustand 4.4 |
| Data Fetching | TanStack React Query 5.17 |
| HTTP Client | Axios 1.6 |
| Charts | Recharts 2.10 |
| Routing | React Router DOM 6.21 |

#### Infrastructure
- **Docker Compose** orchestration with 5 services:
  - `api` - FastAPI application (Uvicorn)
  - `frontend` - React SPA served via Nginx
  - `postgres` - PostgreSQL 15 database
  - `redis` - Redis 7 for cache and task broker
  - `celery-worker` - Celery worker for background tasks

---

### API Endpoints

#### Authentication (`/api/auth`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /register | No | Create new account |
| POST | /login | No | Get JWT tokens |
| POST | /refresh | No | Refresh access token |
| POST | /logout | Yes | Invalidate refresh token |

#### Profiles (`/api/profiles`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | / | Yes | List household profiles |
| POST | / | Yes | Create new profile |
| GET | /{id} | Yes | Get profile detail |
| PUT | /{id} | Yes | Update profile |
| DELETE | /{id} | Yes | Delete profile |

#### Brokers (`/api/brokers`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | / | No | List broker playbooks |
| GET | /{slug} | No | Get broker detail |

#### Webhooks (`/api/webhooks`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | / | Yes | Create webhook endpoint |
| GET | / | Yes | List webhook endpoints |
| DELETE | /{id} | Yes | Delete webhook endpoint |

#### Scans (`/api/scans`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | / | Yes | List deletion scans |
| GET | /{id} | Yes | Get scan detail |
| POST | / | Yes | Trigger new scan |
| POST | /{id}/cancel | Yes | Cancel running scan |

---

### Response Format
All API responses follow a consistent envelope:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional human-readable message"
}
```

Error responses include an `error_code` field:
```json
{
  "success": false,
  "error_code": "INVALID_CREDENTIALS",
  "message": "Invalid email or password"
}
```

---

### Security Considerations
- JWT secret must be configured via `JWT_SECRET` environment variable (32+ character random string)
- Passwords hashed with bcrypt (default rounds: 12)
- CORS currently allows all origins (`*`) - **must be restricted for production**
- Refresh tokens stored in Redis for blacklisting on logout
- Token expiry: 15 minutes for access tokens, 7 days for refresh tokens

---

### Known Limitations (Version 0.2.0)
1. **Scan Execution** - Scan trigger creates a database record but does not yet dispatch Celery tasks
2. **Password Reset** - Not yet implemented
3. **Real-time Updates** - Scan progress is polling-based; WebSocket support planned for Sprint 4
4. **CORS** - Currently permissive (`*`), must be tightened for production deployment
5. **Playwright Executor** - Browser automation not yet connected to scan tasks
6. **Mailwatcher** - Email processing pipeline not yet active

---

### Known Limitations (Version 0.3.0)
1. **Password Reset** - Not yet implemented, planned for Sprint 4
2. **Real-time Updates** - Scan progress is polling-based; WebSocket support planned for Sprint 4
3. **CORS** - Currently permissive (`*`), must be tightened for production deployment
4. **Concurrent Scan Limits** - Browser pool size defaults to 3; may need tuning for high-volume deployments
5. **CAPTCHA Solving** - CAPTCHAs are detected and flagged but not automatically solved; requires manual intervention
6. **Email Verification** - Registration does not yet require email confirmation

---

### What's Next (Sprint 4)
- Real-time scan progress via WebSocket
- Password reset flow with email verification
- Production CORS configuration and HTTPS setup
- Performance optimization for concurrent scan execution
- Advanced reporting and analytics dashboard
- Multi-household support
---

### Getting Started

#### Prerequisites
- Docker Desktop installed and running
- Docker Compose v2+

#### Quick Start
```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env to set JWT_SECRET and other values

# 2. Run init script (builds, migrates, seeds)
./scripts/init.sh

# 3. Access the application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

#### Development
```bash
# Start all services
docker compose up --build

# Run API tests
docker compose exec api pytest tests/ -v

# View logs
docker compose logs -f api
```

---

### Files Added/Modified in This Release (Version 0.3.0)
**55+ new files created across Playwright executor, Mailwatcher, workflows, and tests.**

Key additions:
- `playwright/models.py` - Pydantic models (21 model classes)
- `playwright/pool.py` - BrowserPool with anti-detection
- `playwright/token_resolver.py` - SafeDict template engine
- `playwright/actions.py` - 16 action handlers
- `playwright/executor.py` - PlaybookExecutor engine
- `playwright/main.py` - FastAPI service (port 8001)
- `playwright/screenshot.py` - Screenshot path utility
- `playwright/user_agents.json` - UA pool
- `api/services/playwright_service.py` - HTTP client for Playwright
- `mailwatcher/imap_client.py` - IMAP polling client
- `mailwatcher/classifier.py` - AI email classification
- `mailwatcher/repository.py` - Email storage repository
- `mailwatcher/notifier.py` - Webhook notifications
- `workflows/scan_orchestration.json` - n8n scan workflow
- `workflows/opt_out_orchestration.json` - n8n opt-out workflow
- `workflows/email_processing.json` - n8n email workflow
- `workflows/error_handling.json` - n8n error handling
- `e2e/` - 41 E2E tests across 3 files
- `tests/unit/playwright/` - 151 unit tests across 6 files

---

### Files Added/Modified in Version 0.2.0
**45+ new files created across backend, frontend, tests, and infrastructure.**

Key additions:
- `api/routers/` - 5 router modules (auth, profiles, brokers, webhooks, scans)
- `api/services/` - 4 service modules (auth, profile, broker, webhook)
- `api/schemas/` - 5 Pydantic schema modules
- `api/security.py` - JWT auth and password hashing
- `frontend/src/pages/` - 6 React page components
- `frontend/src/stores/authStore.js` - Zustand auth state
- `frontend/src/lib/api.js` - Axios API client
- `docker-compose.yml` - 5-service orchestration
- `scripts/init.sh` - First-run setup automation
- `tests/unit/api/` - 4 test modules with pytest fixtures

---

*OpenDataRemoval - Take back your digital privacy.*