"""API integration tests — verify the FastAPI endpoints work end-to-end."""

import pytest
import httpx


# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------

class TestHealthCheck:
    def test_root_endpoint(self, api_client):
        """GET / should return 200."""
        response = api_client.get("/")
        assert response.status_code == 200

    def test_health_endpoint(self, api_client):
        """GET /api/health should return 200 with status ok."""
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"


# ------------------------------------------------------------------
# Authentication Integration Tests
# ------------------------------------------------------------------

class TestAuthIntegration:
    def test_register_and_login_flow(self, api_client):
        """Full registration + login flow."""
        email = f"e2e_flow_{id(api_client)}@example.com"

        # Register
        reg_resp = api_client.post("/api/auth/register", json={
            "email": email,
            "password": "E2eTestPassword123!",
        })
        assert reg_resp.status_code == 200
        assert "access_token" in reg_resp.json()

        # Login with same credentials
        login_resp = api_client.post("/api/auth/login", json={
            "email": email,
            "password": "E2eTestPassword123!",
        })
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()

    def test_login_with_wrong_password(self, api_client):
        """Login with wrong password should fail."""
        # First register
        email = f"e2e_wrong_pw_{id(api_client)}@example.com"
        api_client.post("/api/auth/register", json={
            "email": email,
            "password": "E2eTestPassword123!",
        })

        # Try wrong password
        resp = api_client.post("/api/auth/login", json={
            "email": email,
            "password": "WrongPassword123!",
        })
        assert resp.status_code in (400, 401)

    def test_duplicate_registration(self, api_client):
        """Registering the same email twice should fail."""
        email = f"e2e_dup_{id(api_client)}@example.com"
        api_client.post("/api/auth/register", json={
            "email": email,
            "password": "E2eTestPassword123!",
        })
        resp = api_client.post("/api/auth/register", json={
            "email": email,
            "password": "AnotherPassword123!",
        })
        assert resp.status_code in (400, 409)

    def test_register_invalid_password(self, api_client):
        """Registration with weak password should fail."""
        email = f"e2e_weak_{id(api_client)}@example.com"
        resp = api_client.post("/api/auth/register", json={
            "email": email,
            "password": "weak",
        })
        assert resp.status_code == 400


# ------------------------------------------------------------------
# Profile Integration Tests
# ------------------------------------------------------------------

class TestProfileIntegration:
    def test_create_profile(self, authorized_client):
        """Create a new profile via API."""
        resp = authorized_client.post("/api/profiles", json={
            "first_name": "John",
            "last_name": "Doe",
            "address_line1": "123 Main St",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"

    def test_list_profiles(self, authorized_client):
        """List all profiles for the authenticated user."""
        # Create a profile first
        authorized_client.post("/api/profiles", json={
            "first_name": "Jane",
            "last_name": "Smith",
            "address_line1": "456 Oak Ave",
            "city": "Ann Arbor",
            "state": "MI",
            "postal_code": "48104",
        })

        resp = authorized_client.get("/api/profiles")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_profile_by_id(self, authorized_client):
        """Get a specific profile by ID."""
        create_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Alice",
            "last_name": "Johnson",
            "address_line1": "789 Pine Rd",
            "city": "Grand Rapids",
            "state": "MI",
            "postal_code": "49503",
        })
        profile_id = create_resp.json()["id"]

        resp = authorized_client.get(f"/api/profiles/{profile_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == profile_id

    def test_update_profile(self, authorized_client):
        """Update an existing profile."""
        create_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Bob",
            "last_name": "Wilson",
            "address_line1": "321 Elm St",
            "city": "Lansing",
            "state": "MI",
            "postal_code": "48933",
        })
        profile_id = create_resp.json()["id"]

        resp = authorized_client.patch(f"/api/profiles/{profile_id}", json={
            "first_name": "Robert",
        })
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Robert"

    def test_delete_profile(self, authorized_client):
        """Delete a profile."""
        create_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Eve",
            "last_name": "Davis",
            "address_line1": "654 Maple Dr",
            "city": "Flint",
            "state": "MI",
            "postal_code": "48502",
        })
        profile_id = create_resp.json()["id"]

        resp = authorized_client.delete(f"/api/profiles/{profile_id}")
        assert resp.status_code == 204

        # Verify it's gone
        get_resp = authorized_client.get(f"/api/profiles/{profile_id}")
        assert get_resp.status_code == 404

    def test_unauthorized_access(self, api_client):
        """Accessing profiles without auth should fail."""
        resp = api_client.get("/api/profiles")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# Scan Integration Tests
# ------------------------------------------------------------------

class TestScanIntegration:
    def test_create_scan_dry_run(self, authorized_client):
        """Create a scan in dry-run mode."""
        # Create profile first
        profile_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Scan",
            "last_name": "Test",
            "address_line1": "999 Test Ln",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
        })
        profile_id = profile_resp.json()["id"]

        # Create scan in dry-run mode
        resp = authorized_client.post("/api/scans", json={
            "profile_id": profile_id,
            "broker_id": "spokeo.com",
            "dry_run": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data or "scan_id" in data

    def test_list_scans(self, authorized_client):
        """List scans for the authenticated user."""
        resp = authorized_client.get("/api/scans")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


# ------------------------------------------------------------------
# Broker Integration Tests
# ------------------------------------------------------------------

class TestBrokerIntegration:
    def test_list_brokers(self, authorized_client):
        """List available brokers."""
        resp = authorized_client.get("/api/brokers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_broker_by_id(self, authorized_client):
        """Get a specific broker by ID."""
        resp = authorized_client.get("/api/brokers/spokeo.com")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "spokeo.com"

    def test_get_nonexistent_broker(self, authorized_client):
        """Get a broker that doesn't exist."""
        resp = authorized_client.get("/api/brokers/nonexistent.com")
        assert resp.status_code == 404


# ------------------------------------------------------------------
# Webhook Integration Tests
# ------------------------------------------------------------------

class TestWebhookIntegration:
    def test_create_webhook(self, authorized_client):
        """Create a webhook subscription."""
        resp = authorized_client.post("/api/webhooks", json={
            "url": "https://example.com/webhook",
            "events": ["scan.completed"],
        })
        assert resp.status_code == 200

    def test_list_webhooks(self, authorized_client):
        """List webhook subscriptions."""
        resp = authorized_client.get("/api/webhooks")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)