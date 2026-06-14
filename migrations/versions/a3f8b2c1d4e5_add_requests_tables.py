"""add requests tables

Revision ID: a3f8b2c1d4e5
Revises: c191a8c36f6a
Create Date: 2026-06-13 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f8b2c1d4e5'
down_revision: Union[str, None] = 'c191a8c36f6a'
branch_labels: Union[tuple, str, None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS requests')

    # requests.removal_requests (FKs added separately when source tables exist)
    op.execute("""
        CREATE TABLE requests.removal_requests (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            profile_id UUID NOT NULL,
            broker_id UUID NOT NULL,
            exposure_id UUID NOT NULL,
            removal_method TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            confirmation_message TEXT,
            next_action_at TIMESTAMPTZ,
            followup_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id)
        )
    """)
    op.execute("CREATE UNIQUE INDEX ix_removal_requests_id ON requests.removal_requests(id)")
    op.execute("CREATE INDEX ix_removal_requests_profile_id ON requests.removal_requests(profile_id)")
    op.execute("CREATE INDEX ix_removal_requests_broker_id ON requests.removal_requests(broker_id)")
    op.execute("CREATE INDEX ix_removal_requests_status ON requests.removal_requests(status)")
    op.execute("CREATE INDEX ix_removal_requests_next_action ON requests.removal_requests(next_action_at) WHERE status NOT IN ('confirmed_removed', 'failed')")

    # requests.request_status_log
    op.execute("""
        CREATE TABLE requests.request_status_log (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            request_id UUID NOT NULL,
            previous_status TEXT,
            new_status TEXT NOT NULL,
            change_reason TEXT,
            meta_data JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id)
        )
    """)
    op.execute("CREATE UNIQUE INDEX ix_request_status_log_id ON requests.request_status_log(id)")
    op.execute("CREATE INDEX ix_request_status_log_request_id ON requests.request_status_log(request_id)")
    op.execute("CREATE INDEX ix_request_status_log_created_at ON requests.request_status_log(created_at)")

    # requests.followups
    op.execute("""
        CREATE TABLE requests.followups (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            request_id UUID NOT NULL,
            followup_number INTEGER NOT NULL,
            method_used TEXT NOT NULL,
            response_received BOOLEAN NOT NULL DEFAULT false,
            response_details TEXT,
            scheduled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            executed_at TIMESTAMPTZ,
            PRIMARY KEY (id)
        )
    """)
    op.execute("CREATE UNIQUE INDEX ix_followups_id ON requests.followups(id)")
    op.execute("CREATE INDEX ix_followups_request_id ON requests.followups(request_id)")
    op.execute("CREATE INDEX ix_followups_scheduled_at ON requests.followups(scheduled_at)")

    # requests.verification_scans
    op.execute("""
        CREATE TABLE requests.verification_scans (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            removal_request_id UUID NOT NULL,
            profile_id UUID NOT NULL,
            broker_id UUID NOT NULL,
            result TEXT,
            evidence_path TEXT,
            scheduled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            PRIMARY KEY (id)
        )
    """)
    op.execute("CREATE UNIQUE INDEX ix_verification_scans_id ON requests.verification_scans(id)")
    op.execute("CREATE INDEX ix_verification_scans_removal_request_id ON requests.verification_scans(removal_request_id)")
    op.execute("CREATE INDEX ix_verification_scans_scheduled_at ON requests.verification_scans(scheduled_at)")


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS requests.verification_scans')
    op.execute('DROP TABLE IF EXISTS requests.followups')
    op.execute('DROP TABLE IF EXISTS requests.request_status_log')
    op.execute('DROP TABLE IF EXISTS requests.removal_requests')
