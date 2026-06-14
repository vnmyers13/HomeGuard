# Sprint 6 Kickoff - Frontend Pages, E2E Setup & Complete Test Suite

## Sprint Metadata
- **Sprint Number**: 6
- **Title**: Frontend Pages, E2E Setup & Complete Test Suite
- **Goal**: All dashboard pages complete. Full test suite passing. All 13 critical paths green.
- **Duration**: 5 days
- **Start Date**: 2026-06-14
- **End Date**: 2026-06-18
- **Status**: IN PROGRESS

## Sprint 5 Summary
Sprint 5 delivered the removal request lifecycle tracking system, legal letter PDF generation (CCPA/GDPR), real-time scan progress via WebSockets, and a full frontend Requests page. Sprint 5.5 added test suite fixes, migration fixes, and password reset schemas. Sprint 5.6 completed password reset flow, batch profile operations, test import fixes, and DockerHub image publishing (v1.04).

**Sprint 5 Score**: All deliverables complete (v1.04 released).

## Sprint 6 Tasks (6 tasks, ~24 hours estimated)

| ID | Title | Est. Hours | Status | Dependencies |
|----|-------|-----------|--------|--------------|
| S6-T1 | Common components + scan progress components | 3 | NOT STARTED | None |
| S6-T2 | Reports, System Health, Settings pages | 4 | NOT STARTED | None |
| S6-T3 | Onboarding wizard + update Login/Register | 4 | NOT STARTED | S6-T1 |
| S6-T4 | Frontend vitest setup + component tests | 3 | NOT STARTED | S6-T1 |
| S6-T5 | Playwright E2E infrastructure | 4 | NOT STARTED | None |
| S6-T6 | Write and run E2E tests | 4 | NOT STARTED | S6-T5 |

## Sprint Gate Checks
All must pass to close the sprint:

1. **All 13 critical paths CP-01 through CP-13 pass** — all critical user flows functional
2. **pytest tests/ coverage >= 80%** — backend test coverage
3. **cd frontend && npx vitest run coverage >= 75%** — frontend component test coverage
4. **All pages load without console errors** — no React warnings or errors
5. **Onboarding wizard 5-step flow completes without error** — new user flow tested
6. **Scan progress bar animates during active scan** — WebSocket integration verified
7. **cd e2e && npx playwright test — passes on Chromium** — E2E tests green

## Implementation Details

### S6-T1: Common Components
Extract inline components from Overview.jsx, Requests.jsx, Scans.jsx, etc. into reusable shared components:

- **`src/components/StatusBadge.jsx`** — Extracted from Overview.jsx, used across all pages
- **`src/components/ScoreGauge.jsx`** — Circular score display for exposure scores
- **`src/components/DataTable.jsx`** — Generic table with sorting, pagination, filtering
- **`src/components/ScanProgress.jsx`** — Progress bar + step list for active scans (WebSocket-driven)
- **`src/components/EmptyState.jsx`** — Empty state with illustration + CTA
- **`src/components/Modal.jsx`** — Reusable modal dialog (replaces inline modals)
- **`src/components/Card.jsx`** — Card wrapper (replaces repeated `bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6`)

### S6-T2: New Pages

**Reports Page (`src/pages/Reports.jsx`)**
- Exposure score trends over time (line chart using Recharts)
- Broker exposure breakdown (bar chart)
- Removal success rate (pie/donut chart)
- Date range filter (7d, 30d, 90d, custom)
- Data from `/api/reports/exposure-trends`, `/api/reports/broker-summary`, `/api/reports/removal-stats`
- Export to CSV button

**System Health Page (`src/pages/SystemHealth.jsx`)**
- Service status cards (API, Playwright, Mailwatcher, n8n, DB, Redis)
- Each shows: status indicator, uptime, last check time
- Disk usage bar
- Recent alerts list
- Data from `/api/system/health` (existing endpoint)
- Manual "Check Now" button to refresh

**Settings Page (`src/pages/Settings.jsx`)**
- Notification preferences (email alerts, scan notifications, removal updates)
- Account settings (display name, email, change password)
- Data retention policy (how long to keep screenshots, scan data)
- API key management (list, create, revoke)
- Uses existing `homeguard_prefs` localStorage pattern from api.js
- Save/Cancel buttons with confirmation

### S6-T3: Onboarding Wizard
5-step wizard for new households:

1. **Welcome** — Overview of HomeGuard, "Get Started" button
2. **Create Household** — Name household, add description
3. **Add First Profile** — Name, DOB, address (same form as Profile creation)
4. **Connect Email** — Optional email connection for mailwatcher
5. **First Scan** — Trigger first scan, show success state

- Uses `<Stepper>` component with progress indicator
- Steps stored in Zustand store (`onboardingStore.js`)
- Completes by creating household + profile via API
- Can be skipped, revisited from Settings
- Route: `/onboarding` (redirect if household already exists)

### S6-T4: Frontend Tests (Vitest)
- Install vitest, @testing-library/react, @testing-library/jest-dom
- Configure `vitest.config.js`
- Create test utilities (`src/test-utils.jsx`)
- Write component tests for:
  - `StatusBadge` — renders correct color per status
  - `ScoreGauge` — renders score value and percentage
  - `ScanProgress` — shows steps, updates on prop change
  - `Modal` — open/close, backdrop click closes
  - `DataTable` — renders rows, handles pagination
  - `authStore` — login/logout state transitions

### S6-T5: Playwright E2E Infrastructure
- Install `@playwright/test` in e2e/
- Create `e2e/playwright.config.ts`
- Create `e2e/fixtures/` — auth fixture, navigation fixture
- Create `e2e/fixtures/fakeBrokerServer.ts` — mock broker website
- Create `e2e/docker-compose.e2e.yml` — test compose with fake broker
- Setup: spin up stack, create test user, run E2E, tear down

### S6-T6: E2E Tests
Write Playwright E2E test suite:

- **`e2e/tests/auth.spec.ts`** — Login, register, logout, token refresh
- **`e2e/tests/onboarding.spec.ts`** — 5-step wizard flow
- **`e2e/tests/dashboard.spec.ts`** — Overview loads, stats display
- **`e2e/tests/profiles.spec.ts`** — Create, edit, delete profile
- **`e2e/tests/requests.spec.ts`** — Create request, update status, download PDF
- **`e2e/tests/scans.spec.ts`** — Trigger scan, view progress, cancel scan
- **`e2e/tests/settings.spec.ts`** — Update notification preferences

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Recharts not installed | Medium | Medium | Add as dependency or use simple CSS charts |
| WebSocket tests flaky | Medium | Medium | Use polling fallback in tests |
| Onboarding wizard complexity | Low | Medium | Keep steps minimal, defer advanced features |
| E2E test flakiness | High | Medium | Add retries, use stable selectors |
