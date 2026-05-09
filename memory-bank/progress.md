# Progress

## Sprint 1 (Completed)
- Project scaffolding, documentation, directory structure
- Core design specs and architecture documents

## Sprint 2 (Completed) - Authentication, Core API, Frontend Dashboard
All Sprint 2 deliverables have been implemented and verified.

### What Works
- **Authentication**: JWT-based auth with register, login, refresh, logout
- **Profiles API**: Full CRUD for household profiles with UUID primary keys
- **Brokers API**: List/detail broker playbooks from JSON directory
- **Webhooks API**: Create/list/delete webhook endpoints with token auth
- **Scans API**: List/detail/trigger/cancel deletion scans
- **Frontend dashboard**: 6 pages with protected routing, auth store, API client
- **Docker Compose**: 5 services (api, frontend, postgres, redis, celery-worker)
- **Database migrations**: Alembic initial schema with all tables
- **Unit tests**: Auth, profiles, brokers, webhooks test suites

### API Endpoints Implemented
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/auth/register | No | Create account |
| POST | /api/auth/login | No | Get JWT tokens |
| POST | /api/auth/refresh | No | Refresh access token |
| POST | /api/auth/logout | Yes | Invalidate refresh token |
| GET | /api/profiles | Yes | List household profiles |
| POST | /api/profiles | Yes | Create profile |
| GET | /api/profiles/:id | Yes | Get profile detail |
| PUT | /api/profiles/:id | Yes | Update profile |
| DELETE | /api/profiles/:id | Yes | Delete profile |
| GET | /api/brokers | No | List broker playbooks |
| GET | /api/brokers/:slug | No | Get broker detail |
| POST | /api/webhooks | Yes | Create webhook endpoint |
| GET | /api/webhooks | Yes | List webhook endpoints |
| DELETE | /api/webhooks/:id | Yes | Delete webhook endpoint |
| GET | /api/scans | Yes | List deletion scans |
| GET | /api/scans/:id | Yes | Get scan detail |
| POST | /api/scans | Yes | Trigger new scan |
| POST | /api/scans/:id/cancel | Yes | Cancel running scan |

### Frontend Pages
| Route | Page | Auth Required | Description |
|-------|------|---------------|-------------|
| /login | Login | No | Sign in form |
| /register | Register | No | Create account form |
| / | Overview | Yes | Dashboard home with stats and activity feed |
| /profile | Profile | Yes | Manage household members (CRUD) |
| /household | Household | Yes | Household management view |
| /brokers | Brokers | Yes | Data broker list with status badges |
| /scans | Scans | Yes | Scan history and controls |

### Files Created/Modified in Sprint 2
**Backend (30+ files):**
- `api/main.py` - FastAPI app with all routers registered
- `api/security.py` - JWT auth, password hashing, require_auth dependency
- `api/database.py` - SQLAlchemy engine/session with .env config
- `api/routers/auth.py` - Auth endpoints
- `api/routers/profiles.py` - Profile CRUD
- `api/routers/brokers.py` - Broker catalog
- `api/routers/webhooks.py` - Webhook management
- `api/routers/scans.py` - Scan lifecycle
- `api/services/auth_service.py` - Auth business logic
- `api/services/profile_service.py` - Profile service layer
- `api/services/broker_service.py` - Broker JSON loader
- `api/services/webhook_service.py` - Webhook CRUD
- `api/schemas/auth.py` - Auth Pydantic models
- `api/schemas/profile.py` - Profile Pydantic models
- `api/schemas/broker.py` - Broker Pydantic models
- `api/schemas/webhook.py` - Webhook Pydantic models
- `api/schemas/scan.py` - Scan Pydantic models
- `docker-compose.yml` - 5-service orchestration
- `scripts/init.sh` - First-run setup script
- `tests/conftest.py` - Pytest fixtures
- `tests/unit/api/test_auth.py` - Auth tests
- `tests/unit/api/test_profiles.py` - Profile tests
- `tests/unit/api/test_brokers.py` - Broker tests
- `tests/unit/api/test_webhooks.py` - Webhook tests

**Frontend (14 files):**
- `frontend/src/App.jsx` - Root with BrowserRouter + protected routes
- `frontend/src/main.jsx` - Entry with QueryClient + Zustand provider
- `frontend/src/stores/authStore.js` - Zustand auth store
- `frontend/src/lib/api.js` - Axios client + API helpers
- `frontend/src/pages/Login.jsx` - Login form
- `frontend/src/pages/Register.jsx` - Registration form
- `frontend/src/components/DashboardLayout.jsx` - Sidebar nav + top bar layout
- `frontend/src/pages/Overview.jsx` - Dashboard home
- `frontend/src/pages/Profile.jsx` - Profile CRUD page
- `frontend/src/pages/Household.jsx` - Household management
- `frontend/src/pages/Brokers.jsx` - Broker catalog view
- `frontend/src/pages/Scans.jsx` - Scan history page

### Sprint 3 Progress - Playwright Executor Service
**Completed:**
- [x] Browser pool with anti-detection, startup sequence, health monitoring
- [x] Token resolver with template engine and variable substitution
- [x] 16 action handlers (navigate, fill_form, click, wait, screenshot, submit, select, hover, scroll, type_text, check_text, uncheck_text, download, conditional, loop, execute_js)
- [x] PlaybookExecutor with confirmation system, CAPTCHA detection, error classification
- [x] FastAPI integration with health check, job submission, job status endpoints
- [x] Clean Pydantic models (ExecutionState, JobRequest, PlaybookStep, StepResult, etc.)

**Remaining:**
- [ ] Unit tests for executor
- [ ] Celery task execution (run_scan_task, maintenance tasks)
- [ ] Mailwatcher email processing pipeline
- [ ] n8n workflow orchestration
- [ ] E2E test suite
- [ ] Real-time scan progress via WebSocket

### Known Issues / Decisions
- JWT secret uses env variable `JWT_SECRET` - must be set in production
- CORS allows all origins (`*`) - tighten for production deployment
- Scan trigger creates record but does NOT dispatch Celery task yet (Sprint 3)
- Logout calls Redis to blacklist refresh token - requires Redis connectivity
- Password reset not yet implemented (planned for Sprint 3)