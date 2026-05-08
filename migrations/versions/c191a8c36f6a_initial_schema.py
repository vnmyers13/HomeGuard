"""initial_schema

Revision ID: c191a8c36f6a
Revises:
Create Date: 2026-05-03 01:30:43.560815

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c191a8c36f6a'
down_revision: Union[str, None] = None
branch_labels: Union[tuple, str, None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    # Create 9 schemas
    for schema_name in ['identity', 'registry', 'scanning', 'requests',
                        'mail', 'audit', 'reporting', 'auth', 'archive']:
        op.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')

    # -----------------------------------------------------------
    # auth.auth_profiles
    # -----------------------------------------------------------
    op.create_table('auth_profiles', schema='auth',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('role', sa.String(50), server_default='user', nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_profiles')),
    )
    op.create_unique_constraint(op.f('uq_auth_profiles_username'), 'auth_profiles', ['username'], schema='auth')
    op.create_unique_constraint(op.f('uq_auth_profiles_email'), 'auth_profiles', ['email'], schema='auth')
    op.create_index(op.f('ix_auth_profiles_id'), 'auth_profiles', ['id'], unique=True, schema='auth')
    op.create_index(op.f('ix_auth_profiles_username'), 'auth_profiles', ['username'], unique=True, schema='auth')

    # -----------------------------------------------------------
    # identity.personal_identity
    # -----------------------------------------------------------
    op.create_table('personal_identity', schema='identity',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('first_name', sa.String(100)),
        sa.Column('middle_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('date_of_birth', sa.Date()),
        sa.Column('ssn_last4', sa.String(4)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_personal_identity')),
        sa.ForeignKeyConstraint(['profile_id'], ['auth.auth_profiles.id'], name=op.f('fk_personal_identity_profile_id_auth_profiles')),
    )
    op.create_unique_constraint(op.f('uq_personal_identity_profile_id'), 'personal_identity', ['profile_id'], schema='identity')
    op.create_index(op.f('ix_personal_identity_id'), 'personal_identity', ['id'], unique=True, schema='identity')

    # -----------------------------------------------------------
    # registry.broker_playbooks
    # -----------------------------------------------------------
    op.create_table('broker_playbooks', schema='registry',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('broker_domain', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255)),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('config', sa.JSON()),
        sa.Column('selectors', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_broker_playbooks')),
    )
    op.create_unique_constraint(op.f('uq_registry_broker_playbooks_broker_domain'), 'broker_playbooks', ['broker_domain'], schema='registry')
    op.create_index(op.f('ix_registry_broker_playbooks_id'), 'broker_playbooks', ['id'], unique=True, schema='registry')
    op.create_index(op.f('ix_registry_broker_playbooks_domain'), 'broker_playbooks', ['broker_domain'], unique=True, schema='registry')

    # -----------------------------------------------------------
    # scanning.scan_tasks
    # -----------------------------------------------------------
    op.create_table('scan_tasks', schema='scanning',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('broker_domain', sa.String(255)),
        sa.Column('status', sa.String(50), server_default='pending', nullable=False),
        sa.Column('payload', sa.JSON()),
        sa.Column('result', sa.JSON()),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_scan_tasks')),
        sa.ForeignKeyConstraint(['profile_id'], ['auth.auth_profiles.id'], name=op.f('fk_scan_tasks_profile_id_auth_profiles')),
    )
    op.create_index(op.f('ix_scanning_scan_tasks_id'), 'scan_tasks', ['id'], unique=True, schema='scanning')
    op.create_index(op.f('ix_scanning_scan_tasks_status'), 'scan_tasks', ['status'], schema='scanning')
    op.create_index(op.f('ix_scanning_scan_tasks_profile_id'), 'scan_tasks', ['profile_id'], schema='scanning')

    # -----------------------------------------------------------
    # requests.api_request_logs
    # -----------------------------------------------------------
    op.create_table('api_request_logs', schema='requests',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('method', sa.String(10)),
        sa.Column('url', sa.Text()),
        sa.Column('status_code', sa.Integer()),
        sa.Column('request_body', sa.Text()),
        sa.Column('response_body', sa.Text()),
        sa.Column('duration_ms', sa.Integer()),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_api_request_logs')),
        sa.ForeignKeyConstraint(['profile_id'], ['auth.auth_profiles.id'], name=op.f('fk_api_request_logs_profile_id_auth_profiles')),
    )
    op.create_index(op.f('ix_requests_api_request_logs_id'), 'api_request_logs', ['id'], unique=True, schema='requests')

    # -----------------------------------------------------------
    # mail.incoming_mail
    # -----------------------------------------------------------
    op.create_table('incoming_mail', schema='mail',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('subject', sa.String(500)),
        sa.Column('from_addr', sa.String(255)),
        sa.Column('to_addr', sa.String(255)),
        sa.Column('body', sa.Text()),
        sa.Column('raw_message', sa.Text()),
        sa.Column('processed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_incoming_mail')),
        sa.ForeignKeyConstraint(['profile_id'], ['auth.auth_profiles.id'], name=op.f('fk_incoming_mail_profile_id_auth_profiles')),
    )
    op.create_index(op.f('ix_mail_incoming_mail_id'), 'incoming_mail', ['id'], unique=True, schema='mail')
    op.create_index(op.f('ix_mail_incoming_mail_processed'), 'incoming_mail', ['processed'], schema='mail')

    # -----------------------------------------------------------
    # audit.audit_logs
    # -----------------------------------------------------------
    op.create_table('audit_logs', schema='audit',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('profile_id', sa.Uuid()),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', sa.Uuid()),
        sa.Column('details', sa.JSON()),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs')),
        sa.ForeignKeyConstraint(['profile_id'], ['auth.auth_profiles.id'], name=op.f('fk_audit_logs_profile_id_auth_profiles')),
    )
    op.create_index(op.f('ix_audit_audit_logs_id'), 'audit_logs', ['id'], unique=True, schema='audit')
    op.create_index(op.f('ix_audit_audit_logs_timestamp'), 'audit_logs', ['timestamp'], schema='audit')

    # -----------------------------------------------------------
    # reporting.generated_reports
    # -----------------------------------------------------------
    op.create_table('generated_reports', schema='reporting',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('content', sa.JSON()),
        sa.Column('status', sa.String(50), server_default='draft', nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_generated_reports')),
        sa.ForeignKeyConstraint(['profile_id'], ['auth.auth_profiles.id'], name=op.f('fk_generated_reports_profile_id_auth_profiles')),
    )
    op.create_index(op.f('ix_reporting_generated_reports_id'), 'generated_reports', ['id'], unique=True, schema='reporting')

    # -----------------------------------------------------------
    # archive.archived_documents
    # -----------------------------------------------------------
    op.create_table('archived_documents', schema='archive',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('content', sa.JSON()),
        sa.Column('archived_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_archived_documents')),
        sa.ForeignKeyConstraint(['profile_id'], ['auth.auth_profiles.id'], name=op.f('fk_archived_documents_profile_id_auth_profiles')),
    )
    op.create_index(op.f('ix_archive_archived_documents_id'), 'archived_documents', ['id'], unique=True, schema='archive')

    # -----------------------------------------------------------
    # Celery Beat schedule tables (public schema)
    # -----------------------------------------------------------
    op.create_table('celery_beat_interval',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('every', sa.Integer(), nullable=False),
        sa.Column('period', sa.String(24), nullable=False),
        sa.UniqueConstraint('every', 'period'),
    )

    op.create_table('celery_beat_crontab',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('minute', sa.String(240), nullable=False),
        sa.Column('hour', sa.String(240), nullable=False),
        sa.Column('day_of_week', sa.String(240), nullable=False),
        sa.Column('day_of_month', sa.String(240), nullable=False),
        sa.Column('month_of_year', sa.String(240), nullable=False),
        sa.Column('timezone', sa.String(64), server_default='UTC', nullable=False),
    )

    op.create_table('celery_beat_periodic_tasks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('interval_id', sa.Integer()),
        sa.Column('crontab_id', sa.Integer()),
        sa.Column('interval_seconds', sa.BigInteger()),
        sa.Column('interval_days', sa.Integer()),
        sa.Column('interval_weeks', sa.Integer()),
        sa.Column('crontab_minute', sa.String(240)),
        sa.Column('crontab_hour', sa.String(240)),
        sa.Column('crontab_day_of_week', sa.String(240)),
        sa.Column('crontab_day_of_month', sa.String(240)),
        sa.Column('crontab_month_of_year', sa.String(240)),
        sa.Column('crontab_timezone', sa.String(64), server_default='UTC'),
        sa.Column('args', sa.Text(), server_default='[]'),
        sa.Column('kwargs', sa.Text(), server_default='{}'),
        sa.Column('queue', sa.String(255)),
        sa.Column('exchange', sa.String(255)),
        sa.Column('routing_key', sa.String(255)),
        sa.Column('expires', sa.DateTime(timezone=True)),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True)),
        sa.Column('total_run_count', sa.Integer(), server_default='0'),
        sa.Column('date_changed', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('description', sa.Text()),
        sa.ForeignKeyConstraint(['interval_id'], ['celery_beat_interval.id']),
        sa.ForeignKeyConstraint(['crontab_id'], ['celery_beat_crontab.id']),
    )

    # Insert default Celery Beat intervals
    op.execute("""
        INSERT INTO celery_beat_interval (every, period) VALUES
            (10, 'seconds'),
            (60, 'minutes'),
            (3600, 'hours'),
            (86400, 'days')
        ON CONFLICT (every, period) DO NOTHING
    """)


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table('celery_beat_periodic_tasks')
    op.drop_table('celery_beat_crontab')
    op.drop_table('celery_beat_interval')

    op.drop_table('archived_documents', schema='archive')
    op.drop_table('generated_reports', schema='reporting')
    op.drop_table('audit_logs', schema='audit')
    op.drop_table('incoming_mail', schema='mail')
    op.drop_table('api_request_logs', schema='requests')
    op.drop_table('scan_tasks', schema='scanning')
    op.drop_table('broker_playbooks', schema='registry')
    op.drop_table('personal_identity', schema='identity')
    op.drop_table('auth_profiles', schema='auth')

    # Drop schemas
    for schema_name in ['archive', 'reporting', 'audit', 'mail', 'requests',
                        'scanning', 'registry', 'identity', 'auth']:
        op.execute(f'DROP SCHEMA IF EXISTS {schema_name} CASCADE')

    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS pgcrypto')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')