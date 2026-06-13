# Sprint 4 Kickoff - Celery Workers & Mailwatcher

## Sprint Metadata
- **Sprint Number**: 4
- **Title**: Celery Workers & Mailwatcher
- **Goal**: Full scan→exposure→removal→verification pipeline end-to-end. Mailwatcher classifying emails with two-stage classifier. All critical paths CP-02 through CP-05 and CP-09 passing.
- **Duration**: 5 days (May 10 - May 15, 2026)
- **Start Date**: 2026-05-10
- **End Date**: 2026-05-15
- **Status**: IN PROGRESS

## Sprint 3 Summary
Sprint 3 delivered the complete Playwright Executor microservice: browser pool with anti-detection flags, SafeDict token resolver with derived tokens, 16 action handlers, PlaybookExecutor with confirmation/CAPTCHA/error classification, async job API on port 8001. Mailwatcher email processing pipeline with IMAP client, AI classifier, webhook notifier on port 8003. Celery task integration wiring run_scan_task to Playwright via HTTP. n8n workflow orchestration with 4 workflow definitions. E2E test suite with 41 tests across 3 files. 151 Playwright unit tests + 45 API unit tests = 192 total tests.

**Sprint 3 Score**: 9/9 tasks completed (100%).

## Sprint 4 Tasks (5 tasks, ~22 hours estimated)

| ID | Title | Est. Hours | Status | Dependencies |
|----|-------|-----------|--------|--------------|
| S4-T1 | Celery app config, Beat schedule, task infrastructure | 2 | NOT STARTED | None |
| S4-T2 | Scan tasks — dispatch chain, scan_broker, analytics chord callback | 6 | NOT STARTED | S4-T1 |
| S4-T3 | Removal request tasks — web form, email, legal letter, follow-up | 6 | NOT STARTED | S4-T2 |
| S4-T4 | Mailwatcher — two-stage classifier, patterns.yml, link extractor, request matcher | 6 | NOT STARTED | None |
| S4-T5 | Maintenance, registry, notification tasks + test coverage | 2 | NOT STARTED | S4-T1 |

## Sprint Gate Checks
All must pass to close the sprint:

1. `pytest tests/integration/test_scan_to_removal.py -m critical` — all pass
2. `pytest tests/unit/mailwatcher/` — 0 failures, 15+ tests
3. CP-02 test_full_scan_to_web_form_removal passes
4. CP-03 test_email_confirmed_removal_triggers_verification_schedule passes
5. CP-04 test_verification_scan_detects_relisting passes
6. CP-05 test_followup_escalates_after_3_attempts passes
7. CP-09 all 3 classifier tests pass
8. `docker compose logs mailwatcher` shows poll_completed every 15 minutes

## Critical Implementation Details

### S4-T1: Celery App Config & Beat Schedule
- **celery_app.py**: Already exists from Sprint 3. Need to add:
  - Worker config per DOC-7: task_acks_late=True, worker_prefetch_multiplier=1, result_expires=3600
  - Beat schedule: 4 entries — daily_full_scan (0 2 * * *), nightly_screenshot_purge (0 3 * * *), weekly_broker_health_check (0 4 * * 0), hourly_followup_check (0 * * * *)
  - Base task class that writes to audit.system_events on success/failure
- **Key**: All tasks must be idempotent — check for existing records before creating duplicates

### S4-T2: Scan Tasks (Dispatch Chain)
- **scan_broker(profile_id, broker_id, scan_run_id)**: Fetch playbook + decrypt fields → POST playwright /jobs/scan → poll every 5s → on found: create exposure row + dispatch execute_removal_request.delay() → publish Redis SSE event → update scan_run counters
- **compute_post_scan_analytics(results, profile_id, scan_run_id)**: Chord callback — compute exposure score formula — insert exposure_scores + daily_broker_snapshots rows — create new_exposure notifications
- **dispatch_profile_scan(profile_id, scan_run_id)**: chord(group([scan_broker.s(p,b,r) for b in brokers_batches_10]) | compute_post_scan_analytics.s(p,r))
- **dispatch_daily_scan()**: Create scan_run row — group([dispatch_profile_scan.s(p,r) for active non-paused profiles])
- **dispatch_verification_scan(profile_id, broker_id, request_id, vscan_id)**: Targeted scan — on still_listed: create relisting_events + new removal_request(parent_request_id=original)
- **fake_playwright_service fixture**: FastAPI server on random port, set_next_outcome(outcome, fields=[]) configures next response

### S4-T3: Removal Request Tasks
- **execute_removal_request**: Route by removal_method. Write audit_log BEFORE dispatch. Schedule followup ETA = now() + broker.estimated_response_days * 86400
- **submit_web_form_optout**: Call playwright /jobs/optout. Poll. On confirmed: status=pending_confirmation. On captcha: status=requires_manual + flag broker
- **send_removal_email**: Render Jinja2 (broker template first, generic fallback). SMTP send. Store Message-ID. audit_log=removal_email_sent BEFORE smtp.sendmail()
- **generate_and_send_legal_letter**: Render HTML template. WeasyPrint PDF. Save to /app/screenshots/legal/{request_id}.pdf. audit_log=legal_letter_generated BEFORE send
- **followup_removal_request**: Skip if status in (confirmed_removed, verified_removed, requires_manual, failed). INSERT followups row. Re-dispatch method task. If followup_number==3: status=requires_manual + notification
- **process_email_classification**: confirmed_removal → schedule verification ETA 14 days. rejection → failed. info_requested → requires_manual. verification_link → dispatch click_verification_link

### S4-T4: Mailwatcher Two-Stage Classifier
- **classifier.py**: Already exists from Sprint 3. Need to enhance with:
  - Stage 1 — prefilter_keywords = union of all keywords across all types
  - Stage 2 — regex per type in priority: verification_link first, then confirmed_removal, info_requested, rejection
  - patterns.yml hot-reload: stat() each poll, if mtime changed re-read + recompile all regex patterns
- **patterns.yml**: Define keyword sets and regex patterns for each email classification type
- **link_extractor.py**: Score each URL — positive for /verify /confirm /optout in path, domain matches from_domain. Negative for tracking pixels, mailchimp domains
- **request_matcher.py**: Match incoming emails to existing removal requests via Message-ID, subject patterns, sender domain
- **repository.py**: Already exists from Sprint 3. Need to add deduplication: SELECT id FROM mail.inbound_messages WHERE message_id_header = %s

### S4-T5: Maintenance, Registry, Notification Tasks
- **purge_expired_screenshots**: SELECT WHERE purge_at <= now() AND purged_at IS NULL. os.remove() each. UPDATE purged_at
- **compute_disk_usage**: shutil.disk_usage() per volume. SET Redis opendataremoval:disk_usage TTL=4200
- **check_broker_opt_out_urls**: HTTP HEAD each active web_form broker. Flag unreachable: PATCH broker notes + create notification
- **upsert_broker_from_discovery**: Validate schema. Upsert brokers. Insert playbook if present
- **create_notification**: INSERT auth.notifications. redis.publish(opendataremoval:notifications:{household_id}, json.dumps(notification))

## Files to Create/Update
```
api/workers/celery_app.py              # UPDATE - S4-T1, add Beat schedule + worker config
api/workers/tasks/scanning.py          # UPDATE - S4-T2, full dispatch chain + analytics chord
api/workers/tasks/requests.py          # NEW - S4-T3, removal request tasks
api/workers/tasks/maintenance.py       # UPDATE - S4-T5, add purge, disk usage, broker health
api/workers/tasks/registry.py          # UPDATE - S4-T5, upsert from discovery
api/workers/tasks/notifications.py     # NEW - S4-T5, notification creation + Redis publish
api/templates/email/generic_removal.html   # NEW - S4-T3, email template
api/templates/email/generic_removal.txt    # NEW - S4-T3, plain text fallback
api/templates/legal/ccpa_letter.html       # NEW - S4-T3, CCPA legal letter
api/templates/legal/gdpr_letter.html       # NEW - S4-T3, GDPR legal letter

mailwatcher/classifier.py              # UPDATE - S4-T4, two-stage classifier
mailwatcher/patterns.yml               # NEW - S4-T4, keyword/regex patterns
mailwatcher/link_extractor.py          # NEW - S4-T4, URL scoring
mailwatcher/request_matcher.py         # NEW - S4-T4, match emails to requests
mailwatcher/repository.py              # UPDATE - S4-T4, deduplication

tests/unit/workers/test_scan_tasks.py  # NEW - S4-T2, scan task tests
tests/unit/workers/test_maintenance_tasks.py  # NEW - S4-T5, maintenance tests
tests/integration/test_scan_to_removal.py     # NEW - S4-T2, CP-02/03/04/05 tests
tests/integration/test_email_response_flow.py # NEW - S4-T3, email flow tests
tests/unit/mailwatcher/test_classifier.py     # NEW - S4-T4, CP-09 classifier tests
tests/unit/mailwatcher/test_link_extractor.py # NEW - S4-T4, link scoring tests
tests/unit/mailwatcher/test_request_matcher.py # NEW - S4-T4, matcher tests
tests/unit/mailwatcher/test_patterns.py       # NEW - S4-T4, pattern matching tests
tests/unit/mailwatcher/test_email_parser.py   # NEW - S4-T4, parser tests
```

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Celery tasks create duplicate exposures | Medium | High | Idempotency checks on all task entries, unique constraints in DB |
| Mailwatcher misclassifies emails | Medium | Medium | Two-stage classifier with keyword prefilter, conservative regex patterns |
| Playwright job polling times out | Low | High | Configurable poll timeout, retry with exponential backoff |
| SMTP failures for removal emails | Medium | Low | Retry logic, fallback to generic template, audit logging |
| Legal letter PDF generation fails | Low | Medium | WeasyPrint error handling, fallback to HTML email |

## Current State (What Already Exists from Sprint 3)
- `api/workers/celery_app.py` — Basic Celery app exists, needs Beat schedule + worker config
- `api/workers/tasks/scanning.py` — Basic run_scan_task exists, needs full dispatch chain
- `api/workers/tasks/maintenance.py` — Basic stub exists, needs purge/disk/health tasks
- `api/workers/tasks/registry.py` — Exists, needs upsert from discovery
- `mailwatcher/main.py` — FastAPI service exists on port 8003
- `mailwatcher/imap_client.py` — IMAP polling client exists
- `mailwatcher/classifier.py` — Basic classifier exists, needs two-stage enhancement
- `mailwatcher/notifier.py` — Webhook notifier exists
- `mailwatcher/repository.py` — Basic repository exists, needs deduplication

## Notes
- Celery broker: Redis at `redis://redis:6379/0`
- Celery backend: Redis at `redis://redis:6379/1`
- Playwright service: HTTP at `http://playwright:8001`
- Mailwatcher service: FastAPI on port 8003, IMAP polling every 15 minutes
- SSE events published to Redis channel `opendataremoval:scan:{scan_run_id}`
- Notifications published to Redis channel `opendataremoval:notifications:{household_id}`
- Exposure score formula: `(exposed_brokers / total_active_brokers) * 100`
- Follow-up scheduling: broker.estimated_response_days * 86400 seconds from creation