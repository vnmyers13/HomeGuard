# Product Context

## Why HomeGuard Exists
Data brokers collect, aggregate, and sell personal information (names, addresses, phone numbers, emails) about everyday people. Finding and removing this data manually is time-consuming, technically challenging, and unsustainable - brokers re-list data frequently.

## Problems It Solves
1. **Automated Discovery**: Scans 50+ data broker sites automatically instead of manual searching
2. **Automated Removal**: Submits opt-out requests through multiple channels (web forms, email, legal letters)
3. **Response Processing**: Classifies broker responses via IMAP email monitoring
4. **Verification**: Runs follow-up scans to confirm removals stuck
5. **Real-time Tracking**: Dashboard with exposure scores, progress bars, and notifications

## How It Works
1. User creates profiles (name, DOB, addresses, phones, emails) via onboarding wizard
2. System scans brokers using Playwright headless browsers against configured playbooks
3. Found exposures trigger automated removal requests based on playbook configuration
4. Mailwatcher monitors email for broker responses, classifies them into categories
5. Verification scans confirm removals or detect relistings
6. User monitors everything from the React dashboard

## User Experience Goals
- **Zero-config setup**: `init.sh` handles everything - Docker, secrets, migrations, seeding
- **Real-time feedback**: SSE scan progress bars, WebSocket notifications on dashboard
- **Trustworthy operations**: PII encrypted at rest, immutable audit logs, HMAC webhook auth
- **Transparent status**: Every request has a visible timeline from creation through confirmed removal