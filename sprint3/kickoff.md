# Sprint 3 Kickoff - Playwright Executor Service

## Sprint Metadata
- **Sprint Number**: 3
- **Title**: Playwright Executor Service
- **Goal**: Playwright microservice accepts scan/optout jobs, executes all 16 action types, returns structured JobResult with screenshots. All playwright unit tests pass.
- **Duration**: 5 days (May 8 - May 13, 2026)
- **Start Date**: 2026-05-08
- **End Date**: 2026-05-13
- **Status**: IN_PROGRESS

## Sprint 2 Summary
Sprint 2 delivered the complete core API layer: JWT authentication with bcrypt password hashing and Redis rate limiting, full profile CRUD with PII encryption at rest and versioned audit trails, broker registry CRUD with playbook JSON schema validation, n8n webhook integration with HMAC-SHA256 verification, scan management router, and a complete React frontend with 8 pages (Login, Register, Overview, Household, Profile, Brokers, Scans, Requests). 45+ unit tests passing with 80%+ coverage.

**Sprint 2 Score**: 6/6 tasks completed (100%).

## Sprint 3 Tasks (4 tasks, ~20 hours estimated)

| ID | Title | Est. Hours | Status | Dependencies |
|----|-------|-----------|--------|--------------|
| S3-T1 | Browser pool, anti-detection, and startup sequence | 4 | NOT_STARTED | None |
| S3-T2 | Token resolver (SafeDict) and all 16 action handlers | 6 | NOT_STARTED | S3-T1 |
| S3-T3 | PlaybookExecutor — phase loop, confirmation, CAPTCHA, error classification | 6 | NOT_STARTED | S3-T1, S3-T2 |
| S3-T4 | Async job API — submit, poll, cancel, list endpoints | 4 | NOT_STARTED | S3-T1, S3-T3 |

## Sprint Gate Checks
All must pass to close the sprint:

1. `docker compose exec api curl -s http://playwright:8001/health` → `{status: healthy, pool_available: 3}`
2. `POST /jobs/scan` → returns job_id immediately (202)
3. `GET /jobs/{id}` → eventually returns completed result
4. `dry_run=true` → skips submit action, all other steps execute
5. Error auto-captures screenshot at correct structured path
6. `pytest tests/unit/playwright/` → 0 failures, 20+ tests passing

## Critical Implementation Details

### S3-T1: Browser Pool & Anti-Detection
- **BrowserPool**: Launch Chromium with anti-detection flags (`--disable-blink-features=AutomationControlled`)
- **Per-context**: Randomized UA (Chrome 65%, Safari 20%, Firefox 15%), viewport random 1280-1920 x 720-1080
- **init_script**: `navigator.webdriver=undefined`, mock `navigator.plugins.length > 0`, mock `chrome.runtime`
- **Pool size**: From `PLAYWRIGHT_POOL_SIZE` env (default 3)
- **Pydantic models**: ScanJobRequest, OptoutJobRequest, StepResult, ErrorResult, JobResult, ScreenshotRecord

### S3-T2: Token Resolver & Action Handlers
- **SafeDict**: `__missing__` returns empty string + logs warning for missing tokens
- **Derived tokens**: first_name/last_name from full_name, city/state/zip from address_full, dob_month/dob_year from date_of_birth
- **16 action handlers**: navigate, fill_form, click, wait, screenshot, submit, select, hover, scroll, type_text, check_text, uncheck_text, download, conditional, loop, execute_js
- **Screenshot paths**: `/app/screenshots/{profile_id}/{broker_id}/{timestamp}_{step_id}_{type}.png`

### S3-T3: PlaybookExecutor
- **Phase loop**: navigate → execute steps → check confirmation + CAPTCHA after each navigate/submit
- **on_failure handlers**: stop (return error), skip_phase (continue), mark_manual (return requires_manual)
- **Auto-screenshot**: on any exception regardless of step.screenshot flag
- **Error classification**: map playwright exceptions to error_type with recovery_hint
- **Confirmation detection**: check_text patterns, check_url patterns, check_negative patterns

### S3-T4: Async Job API
- **JobManager**: dict[str, JobState], background asyncio task evicts jobs older than 1 hour
- **POST /jobs/scan**: acquire pool context → if None return 503 with retry_after_ms=10000
- **GET /jobs/{id}**: return JobResult or current progress, 404 if evicted
- **DELETE /jobs/{id}**: task.cancel(), release(context), status=cancelled

## Files to Create
```
playwright/__init__.py              # NEW - Sprint 3
playwright/models.py                # NEW - S3-T1, Pydantic models
playwright/pool.py                  # NEW - S3-T1, BrowserPool
playwright/user_agents.json         # NEW - S3-T1, UA pool
playwright/token_resolver.py        # NEW - S3-T2, SafeDict + derived tokens
playwright/actions.py               # NEW - S3-T2, 16 action handlers
playwright/screenshot.py            # NEW - S3-T2, screenshot path utility
playwright/executor.py              # NEW - S3-T3, PlaybookExecutor
playwright/confirmation.py          # NEW - S3-T3, confirmation detection
playwright/error_classifier.py      # NEW - S3-T3, error classification
playwright/job_manager.py           # NEW - S3-T4, JobManager
playwright/routers/__init__.py      # NEW - S3-T4
playwright/routers/jobs.py          # NEW - S3-T4, job API endpoints

tests/unit/playwright/__init__.py   # NEW - S3-T2
tests/unit/playwright/test_token_resolver.py    # NEW - S3-T2
tests/unit/playwright/test_screenshot_path.py   # NEW - S3-T2
tests/unit/playwright/test_confirmation.py      # NEW - S3-T3
tests/unit/playwright/test_error_classifier.py  # NEW - S3-T3
tests/unit/playwright/test_playbook_validator.py # NEW - S3-T3

playwright/main.py                  # UPDATE - existing stub → full FastAPI app
```

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Chromium launch fails in Docker | Medium | High | Pre-installed deps, health check retries |
| Anti-detection bypassed by broker | Medium | Medium | Multiple UA/viewport strategies, init_script patches |
| Playwright context leaks under load | Low | High | Strict acquire/release lifecycle, pool size limits |
| CAPTCHA detection false positives | Medium | Low | Conservative patterns, fallback to mark_manual |

## Notes
- Playwright service runs on port 8001 within Docker network
- Screenshots stored at `/app/screenshots/` (mounted volume)
- Job lifecycle: queued → running → completed/error/requires_manual/cancelled
- Error responses include structured error_type and recovery_hint for upstream handling