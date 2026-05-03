-- ============================================================
-- HomeGuard Database Initialization
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create all 9 schemas
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS registry;
CREATE SCHEMA IF NOT EXISTS scanning;
CREATE SCHEMA IF NOT EXISTS requests;
CREATE SCHEMA IF NOT EXISTS mail;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS reporting;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS archive;

-- Grant schema access to homeguard user
GRANT ALL ON SCHEMA identity TO homeguard;
GRANT ALL ON SCHEMA registry TO homeguard;
GRANT ALL ON SCHEMA scanning TO homeguard;
GRANT ALL ON SCHEMA requests TO homeguard;
GRANT ALL ON SCHEMA mail TO homeguard;
GRANT ALL ON SCHEMA audit TO homeguard;
GRANT ALL ON SCHEMA reporting TO homeguard;
GRANT ALL ON SCHEMA auth TO homeguard;
GRANT ALL ON SCHEMA archive TO homeguard;

-- Set default privileges for tables
GRANT ALL ON ALL TABLES IN SCHEMA identity TO homeguard;
GRANT ALL ON ALL TABLES IN SCHEMA registry TO homeguard;
GRANT ALL ON ALL TABLES IN SCHEMA scanning TO homeguard;
GRANT ALL ON ALL TABLES IN SCHEMA requests TO homeguard;
GRANT ALL ON ALL TABLES IN SCHEMA mail TO homeguard;
GRANT ALL ON ALL TABLES IN SCHEMA audit TO homeguard;
GRANT ALL ON ALL TABLES IN SCHEMA reporting TO homeguard;
GRANT ALL ON ALL TABLES IN SCHEMA auth TO homeguard;
GRANT ALL ON ALL TABLES IN SCHEMA archive TO homeguard;

GRANT ALL ON ALL SEQUENCES IN SCHEMA identity TO homeguard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA registry TO homeguard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA scanning TO homeguard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA requests TO homeguard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA mail TO homeguard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA audit TO homeguard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA reporting TO homeguard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA auth TO homeguard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA archive TO homeguard;

-- Set search path for homeguard role
ALTER ROLE homeguard SET search_path TO identity, registry, scanning, requests, mail, audit, reporting, auth, archive, public;

-- Create Celery Beat schedule table (required for DatabaseScheduler)
CREATE TABLE IF NOT EXISTS celery_beat_periodic_tasks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    interval_id INTEGER,
    crontab_id INTEGER,
    interval_seconds BIGINT,
    interval_days INTEGER,
    interval_weeks INTEGER,
    crontab_minute VARCHAR(240),
    crontab_hour VARCHAR(240),
    crontab_day_of_week VARCHAR(240),
    crontab_day_of_month VARCHAR(240),
    crontab_month_of_year VARCHAR(240),
    crontab_timezone VARCHAR(64) DEFAULT 'UTC',
    args TEXT DEFAULT '[]',
    kwargs TEXT DEFAULT '{}',
    queue VARCHAR(255),
    exchange VARCHAR(255),
    routing_key VARCHAR(255),
    expires TIMESTAMP WITH TIME ZONE,
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    total_run_count INTEGER DEFAULT 0,
    date_changed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

CREATE TABLE IF NOT EXISTS celery_beat_interval (
    id SERIAL PRIMARY KEY,
    every INTEGER NOT NULL,
    period VARCHAR(24) NOT NULL,
    UNIQUE (every, period)
);

CREATE TABLE IF NOT EXISTS celery_beat_crontab (
    id SERIAL PRIMARY KEY,
    minute VARCHAR(240) NOT NULL,
    hour VARCHAR(240) NOT NULL,
    day_of_week VARCHAR(240) NOT NULL,
    day_of_month VARCHAR(240) NOT NULL,
    month_of_year VARCHAR(240) NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC'
);

ALTER TABLE celery_beat_periodic_tasks ADD CONSTRAINT fk_interval FOREIGN KEY (interval_id) REFERENCES celery_beat_interval(id);
ALTER TABLE celery_beat_periodic_tasks ADD CONSTRAINT fk_crontab FOREIGN KEY (crontab_id) REFERENCES celery_beat_crontab(id);

-- Insert default intervals
INSERT INTO celery_beat_interval (every, period) VALUES
    (10, 'seconds'),
    (60, 'minutes'),
    (3600, 'hours'),
    (86400, 'days')
ON CONFLICT (every, period) DO NOTHING;

SELECT 'Database initialized successfully with 9 schemas and Celery Beat tables.' AS status;