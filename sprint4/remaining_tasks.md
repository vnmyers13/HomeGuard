# Sprint 4 - Remaining Tasks

## What's Done
- [x] S4-T1: Celery app config, Beat schedule, task infrastructure
- [x] S4-T2: Scan tasks — dispatch chain, scan_broker, analytics chord callback
- [x] S4-T3: Removal request tasks (execute_removal_request, send_removal_email, generate_and_send_legal_letter, followup_removal_request, process_email_classification)
- [x] S4-T5: Maintenance, registry, notification tasks

## What Remains
### S4-T4: Mailwatcher Two-Stage Classifier ✅ COMPLETE
- [x] Basic classifier with regex patterns ✅
- [x] link_extractor.py ✅
- [x] request_matcher.py ✅
- [x] patterns.yml - COMPLETE (externalized with prefilter_keywords + patterns)
- [x] Two-stage prefilter_keywords enhancement - COMPLETE
- [x] Patterns hot-reload on mtime change - COMPLETE

### Templates (VERIFY)
- [ ] api/templates/email/generic_removal.html - verify content
- [ ] api/templates/email/generic_removal.txt - verify content
- [ ] api/templates/legal/ccpa_letter.html - verify content
- [ ] api/templates/legal/gdpr_letter.html - verify content

### Tests (RUN & FIX)
- [ ] tests/integration/test_scan_to_removal.py - CP-02/03/04/05
- [ ] tests/unit/mailwatcher/test_classifier.py - CP-09 (15+ tests)
- [ ] Additional mailwatcher test coverage

## Sprint Gate Checks (ALL must pass)
1. `pytest tests/integration/test_scan_to_removal.py -m critical` — all pass
2. `pytest tests/unit/mailwatcher/` — 0 failures, 15+ tests
3. CP-02 test_full_scan_to_web_form_removal passes
4. CP-03 test_email_confirmed_removal_triggers_verification_schedule passes
5. CP-04 test_verification_scan_detects_relisting passes
6. CP-05 test_followup_escalates_after_3_attempts passes
7. CP-09 all 3 classifier tests pass
8. `docker compose logs mailwatcher` shows poll_completed every 15 minutes