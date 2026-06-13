"""Shared fixtures and configuration for end-to-end tests."""

import os
import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure API module is importable
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.database import Base, SessionLocal
from api.models.auth import User


# ------------------------------------------------------------------
# Test Database Fixtures
# ------------------------------------------------------------------

@pytest.fixture(scope="session")
def docker_compose_project_name():
    """Unique project name for Docker Compose to avoid DB conflicts."""
    return "opendataremoval-e2e"


@pytest.fixture(scope="session")
def test_db_url():
    """PostgreSQL DSN for the test database (from env or default)."""
    return os.getenv(
        "E2E_DATABASE_URL",
        "postgresql+psycopg2://opendataremoval:opendataremoval@localhost:5432/opendataremoval_test"
    )


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create a SQLAlchemy engine for the test database."""
    engine = create_engine(test_db_url, pool_size=5, max_overflow=10)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def _setup_test_db(test_engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db_session(test_engine, _setup_test_db):
    """Yield a clean database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()


# ------------------------------------------------------------------
# API Client Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def api_base_url():
    """Base URL for the FastAPI service under test."""
    return os.getenv("E2E_API_URL", "http://localhost:8000")


@pytest.fixture
def api_client(api_base_url):
    """Yield an httpx client pointed at the API."""
    client = httpx.Client(base_url=api_base_url, timeout=httpx.Timeout(30.0))
    yield client
    client.close()


# ------------------------------------------------------------------
# Auth Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def auth_token(api_client):
    """Register a new user and return a JWT access token."""
    email = f"e2e_test_{id(api_client)}@example.com"
    response = api_client.post("/api/auth/register", json={
        "email": email,
        "password": "E2eTestPassword123!",
    })
    assert response.status_code == 200, f"Registration failed: {response.text}"
    token = response.json()["access_token"]
    yield token


@pytest.fixture
def authorized_client(api_client, auth_token):
    """Yield an httpx client with Authorization header set."""
    api_client.headers["Authorization"] = f"Bearer {auth_token}"
    yield api_client
    api_client.headers.pop("Authorization", None)


# ------------------------------------------------------------------
# Playwright Service Fixture
# ------------------------------------------------------------------

@pytest.fixture
def playwright_base_url():
    """Base URL for the Playwright executor service."""
    return os.getenv("E2E_PLAYWRIGHT_URL", "http://localhost:8002")


@pytest.fixture
def playwright_client(playwright_base_url):
    """Yield an httpx client pointed at the Playwright service."""
    client = httpx.Client(base_url=playwright_base_url, timeout=httpx.Timeout(30.0))
    yield client
    client.close()


# ------------------------------------------------------------------
# Fixture to skip tests when external services are unavailable
# ------------------------------------------------------------------

@pytest.fixture
def require_playwright(pytestconfig):
    """Marker/fixture to skip if Playwright service is not reachable."""
    import httpx as h
    try:
        resp = h.get(os.getenv("E2E_PLAYWRIGHT_URL", "http://localhost:8002") + "/health", timeout=3.0)
        has_playwright = resp.status_code == 200
    except Exception:
        has_playwright = False
    pytest.skip("Playwright service not available") if not has_playwright else None
    return True