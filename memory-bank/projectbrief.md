# HomeGuard - Privacy Protection Platform

## Project Brief

HomeGuard is an automated privacy protection platform that scans data broker websites for user PII, submits removal requests (web forms, emails, legal letters), and verifies/completes opt-out workflows.

## Core Goals
1. **Scan**: Automatically discover where a user's PII appears across 50+ data broker sites
2. **Remove**: Submit removal requests through multiple channels (web forms, email, postal mail legal letters)
3. **Verify**: Monitor and confirm that removals stick - detect relistings
4. **Dashboard**: Provide a real-time React dashboard showing exposure scores, scan progress, and removal status

## Key Components
- **API**: FastAPI backend with PostgreSQL (PII encryption), Celery workers
- **Playwright Executor**: Headless browser service for automated broker site interaction
- **Mailwatcher**: IMAP email classifier for processing broker responses
- **Frontend**: React + Vite + Tailwind dashboard
- **n8n Integration**: Broker discovery pipeline via n8n workflows

## Architecture
9 Docker services: API, Frontend (nginx), Playwright, Mailwatcher, PostgreSQL, Redis, Celery Worker, Celery Beat, n8n

## Sprint Plan
7 sprints of 5 days each, 39 total tasks:
- Sprint 1: Foundation & Database Schema
- Sprint 2: Core API - Auth, Profiles, Brokers & n8n
- Sprint 3: Playwright Executor Service
- Sprint 4: Celery Workers & Mailwatcher
- Sprint 5: Remaining API Routers & React Frontend Foundation
- Sprint 6: Frontend Pages, E2E Setup & Complete Test Suite
- Sprint 7: Security Hardening, Operations & Final Sign-off