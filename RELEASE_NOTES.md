# HomeGuard Release Notes

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

### Known Limitations
1. **Scan Execution** - Scan trigger creates a database record but does not yet dispatch Celery tasks (Sprint 3)
2. **Password Reset** - Not yet implemented, planned for Sprint 3
3. **Real-time Updates** - Scan progress is polling-based; WebSocket support planned for Sprint 4
4. **CORS** - Currently permissive (`*`), must be tightened for production deployment
5. **Playwright Executor** - Browser automation not yet connected to scan tasks (Sprint 3)
6. **Mailwatcher** - Email processing pipeline not yet active (Sprint 3)

---

### What's Next (Sprint 3)
- Playwright executor integration with broker playbooks
- Celery task execution pipeline (scan → discover → delete → report)
- Mailwatcher email processing for confirmation responses
- n8n workflow orchestration between services
- End-to-end test suite
- Password reset flow

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

### Files Added/Modified in This Release
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

*HomeGuard - Take back your digital privacy.*