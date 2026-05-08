# System Patterns

## Architecture Overview
HomeGuard follows a microservices architecture via Docker Compose with 9 services connected by two networks:
- `homeguard_net` (internal): db, redis, beat only
- `homeguard_egress` (bridge): api, worker, playwright, mailwatcher, n8n

## Key Design Patterns

### 1. Repository Pattern (Models)
Each database schema has its own module (`api/models/*.py`) containing SQLAlchemy async models. Models use `TypeDecorator` for PII encryption at the database level via pgp_sym_encrypt/decrypt.

### 2. Service Layer Pattern
Routers delegate to service modules (`api/services/*.py`) which contain business logic. Services interact with models and external services (Playwright, SMTP, Celery).

### 3. Playbook-Driven Execution
Broker behavior is configured via JSON playbooks (`playbooks/brokers/*.json`) validated against `playbooks/schema.json`. Each playbook defines phases, steps, action types, and error handlers.

### 4. Async Task Pipeline
Celery workers orchestrate a multi-stage pipeline:
`scan_broker → (found) → execute_removal_request → followup_removal_request`
Chords and groups enable parallel broker scanning per profile.

### 5. Event-Driven Dashboard
Real-time updates via:
- **SSE** (`/api/scans/{id}/progress`): Redis-published scan progress events
- **WebSocket** (`/api/ws/notifications`): Redis-subscribed notification fan-out

### 6. HMAC Webhook Security
n8n discovery pipeline posts to `/api/webhooks/n8n` with `X-Homeguard-Signature: HMAC-SHA256(body, N8N_WEBHOOK_SECRET)`. Server verifies with `hmac.compare_digest()` (constant-time).

### 7. Archive-on-Delete Pattern
Deleting a profile triggers an 8-step atomic transaction: copies data to archive.* tables, creates two audit_log entries. Ensures complete removal from active tables while preserving compliance history.

### 8. Field Versioning
Profile fields use `effective_to` timestamp + `is_current` flag. Updating a field stamps the old row's `effective_to=now()` and inserts new row with `is_current=True`.

## Critical Paths
- CP-01: Docker stack health (all 9 services Up)
- CP-02: Full scan to web form removal end-to-end
- CP-03: Email confirmed removal triggers verification schedule
- CP-04: Verification scan detects relisting
- CP-05: Followup escalates after 3 attempts
- CP-07: PII encryption round-trip (plaintext → encrypted at rest)
- CP-08: Audit log append-only immutability
- CP-10: JWT never stored in localStorage
- CP-11: Complete onboarding wizard (5 steps)