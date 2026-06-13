"""Shared fixtures for integration tests.

Provides a synchronous SQLAlchemy session backed by an in-memory SQLite
database so integration tests can run without requiring an external Postgres.

PostgreSQL-specific types (JSONB) are translated to SQLite-compatible types
by replacing JSONB column types with SQLAlchemy's generic JSON type before
creating tables.
"""

import json
import pytest
from sqlalchemy import create_engine, JSON
from sqlalchemy.orm import sessionmaker


# Use a sync SQLite engine for integration tests
_SYNC_URL = "sqlite:///:memory:"


@pytest.fixture(scope="class")
def engine(request):
    """Create a class-scoped sync engine backed by SQLite."""
    _engine = create_engine(_SYNC_URL, echo=False)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="class")
def session(engine, request):
    """Create a class-scoped session that rolls back after each test.

    All models from `api.database.Base` are created at the start of each
    test class and rolled back afterwards, giving every test a clean slate
    while sharing the same underlying connection.
    """
    from sqlalchemy.dialects.postgresql import JSONB
    from api.database import Base

    # Import all models so they are registered with Base.metadata
    import api.models  # noqa: F401

    # Replace JSONB columns with JSON for SQLite compatibility
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()

    # Strip schemas from all tables for SQLite compatibility
    for name, table in Base.metadata.tables.items():
        table.schema = None

    # Drop existing tables first, then create fresh (handles class-scoped reuse)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    connection = engine.connect()
    # Begin the transaction - all tests share this transaction
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    sess = Session()

    yield sess

    sess.close()
    transaction.rollback()
    Base.metadata.drop_all(engine)
    connection.close()


# Alias used by tests that import `db` instead of `session`
@pytest.fixture(scope="class")
def db(session):
    """Alias for the session fixture to match test convention."""
    return session