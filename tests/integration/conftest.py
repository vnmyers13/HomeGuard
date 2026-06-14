"""Shared fixtures for integration tests.

Provides a synchronous SQLAlchemy session backed by an in-memory SQLite
database so integration tests can run without requiring an external Postgres.

PostgreSQL-specific types (JSONB, UUID with gen_random_uuid) are translated
to SQLite-compatible types by replacing column types and defaults before
creating tables.
"""

import json
import os
import sys
import uuid as uuid_module
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, JSON, Text, text, event
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure api module is importable in both Docker and local environments
# Docker: code is at /app, api module at /app/api/
# Local: repo root parent of tests/, api module at <repo>/api/
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in [_project_root, "/app"]:
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

# Use a sync SQLite engine for integration tests
_SYNC_URL = "sqlite:///:memory:"


def _generate_uuid(mapper, connection, instance):
    """Generate UUID for models with UUID primary keys before insert."""
    pk_cols = mapper.primary_key
    if pk_cols:
        pk_name = pk_cols[0].name
        pk_value = getattr(instance, pk_name, None)
        if pk_value is None:
            setattr(instance, pk_name, str(uuid_module.uuid4()))


def _generate_timestamp(mapper, connection, instance):
    """Generate timestamps for models with created_at/updated_at before insert."""
    now = datetime.now(timezone.utc)
    if hasattr(instance, 'created_at') and getattr(instance, 'created_at', None) is None:
        setattr(instance, 'created_at', now)
    if hasattr(instance, 'updated_at') and getattr(instance, 'updated_at', None) is None:
        setattr(instance, 'updated_at', now)


@pytest.fixture(scope="class")
def session(request):
    """Create a class-scoped session backed by a fresh SQLite engine.

    Each test class gets its own engine and database for complete isolation.
    """
    from sqlalchemy.dialects.postgresql import JSONB
    try:
        from api.database import Base
    except ImportError:
        from database import Base

    # Import all models so they are registered with Base.metadata
    try:
        import api.models  # noqa: F401
    except ImportError:
        import models  # noqa: F401

    # Replace JSONB columns with JSON for SQLite compatibility
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()
            if isinstance(column.type, PG_UUID):
                column.type = Text()

    # Replace PostgreSQL-specific inet type (ip_address) with Text for SQLite
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.name == "ip_address":
                column.type = Text()

    # Strip schemas from all tables for SQLite compatibility
    for table in Base.metadata.tables.values():
        table.schema = None

    # Create a fresh engine for this test class
    engine = create_engine(
        _SYNC_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create tables - archive models have same tablename as main models
    # After stripping schemas, they conflict. We catch and skip duplicates.
    for table in Base.metadata.sorted_tables:
        try:
            table.create(engine)
        except Exception:
            pass  # Skip tables that already exist (archive conflicts)

    # Use a connection with transaction for test data
    connection = engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    sess = Session()

    # Register event listeners to generate UUIDs and timestamps before insert
    try:
        from api.models.auth import User, Household, Session as AuthSession, Notification
        from api.models.identity import Profile, Alias, IdentityDocument, ProfileField
        from api.models.scanning import ScanRun, Exposure, ScanResult, Screenshot
        from api.models.requests import RemovalRequest, Followup, RequestStatusLog, VerificationScan
        from api.models.audit import SystemEvent, AuditLog
        from api.models.registry import Broker, BrokerFieldRequirement, BrokerPlaybook, EmailTemplate
        from api.models.mail import InboundMessage, MessageClassification
        from api.models.reporting import ExposureScore, FieldExposureSummary, RelistingEvent, DailyBrokerSnapshot
    except ImportError:
        from models.auth import User, Household, Session as AuthSession, Notification
        from models.identity import Profile, Alias, IdentityDocument, ProfileField
        from models.scanning import ScanRun, Exposure, ScanResult, Screenshot
        from models.requests import RemovalRequest, Followup, RequestStatusLog, VerificationScan
        from models.audit import SystemEvent, AuditLog
        from models.registry import Broker, BrokerFieldRequirement, BrokerPlaybook, EmailTemplate
        from models.mail import InboundMessage, MessageClassification
        from models.reporting import ExposureScore, FieldExposureSummary, RelistingEvent, DailyBrokerSnapshot

    all_models = [
        User, Household, AuthSession, Notification,
        Profile, Alias, IdentityDocument, ProfileField,
        ScanRun, Exposure, ScanResult, Screenshot,
        RemovalRequest, Followup, RequestStatusLog, VerificationScan,
        SystemEvent, AuditLog,
        Broker, BrokerFieldRequirement, BrokerPlaybook, EmailTemplate,
        InboundMessage, MessageClassification,
        ExposureScore, FieldExposureSummary, RelistingEvent, DailyBrokerSnapshot,
    ]

    for model in all_models:
        try:
            event.listen(model, "before_insert", _generate_uuid)
            event.listen(model, "before_insert", _generate_timestamp)
        except Exception:
            pass

    yield sess

    sess.close()
    try:
        transaction.rollback()
    except Exception:
        pass  # Transaction may already be deassociated
    connection.close()
    engine.dispose()

    # Cleanup hook to drop tables after the class
    def teardown():
        with engine.connect() as conn:
            for tbl in Base.metadata.sorted_tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {tbl.name}"))
                except Exception:
                    pass
            conn.commit()

    request.addfinalizer(teardown)


# Alias used by tests that import `db` instead of `session`
@pytest.fixture(scope="class")
def db(session):
    """Alias for the session fixture to match test convention."""
    return session
