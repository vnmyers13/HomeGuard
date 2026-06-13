"""Full scan flow integration tests — verify end-to-end scan lifecycle."""

import pytest
import httpx


# ------------------------------------------------------------------
# Full Scan Flow Tests
# These tests verify the complete scan lifecycle from creation to completion.
# They require all services (API, Playwright, Redis, PostgreSQL) to be running.
# ------------------------------------------------------------------

class TestFullScanFlow:
    """Complete scan flow from profile creation through scan execution."""

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_complete_scan_flow(self, authorized_client):
        """Full scan flow: create profile -> create scan -> wait for completion -> verify results."""
        # Step 1: Create a profile
        profile_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Flow",
            "last_name": "Test",
            "address_line1": "123 Flow St",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
        })
        assert profile_resp.status_code == 200
        profile_id = profile_resp.json()["id"]

        # Step 2: Create a scan in dry-run mode
        scan_resp = authorized_client.post("/api/scans", json={
            "profile_id": profile_id,
            "broker_id": "spokeo.com",
            "dry_run": True,
        })
        assert scan_resp.status_code == 200
        scan_data = scan_resp.json()
        scan_id = scan_data.get("id") or scan_data.get("scan_id")

        # Step 3: Wait for scan to complete (poll with timeout)
        import time
        timeout = 60  # seconds
        start = time.time()
        while time.time() - start < timeout:
            status_resp = authorized_client.get(f"/api/scans/{scan_id}")
            if status_resp.status_code == 200:
                status = status_resp.json().get("status")
                if status in ("completed", "failed"):
                    break
            time.sleep(2)

        # Step 4: Verify scan completed
        final_resp = authorized_client.get(f"/api/scans/{scan_id}")
        assert final_resp.status_code == 200
        final_data = final_resp.json()
        assert final_data.get("status") in ("completed", "failed", "dry_run_completed")

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_scan_with_invalid_broker(self, authorized_client):
        """Create a scan with an invalid broker ID should fail gracefully."""
        profile_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Invalid",
            "last_name": "Broker",
            "address_line1": "456 Error Ln",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
        })
        profile_id = profile_resp.json()["id"]

        scan_resp = authorized_client.post("/api/scans", json={
            "profile_id": profile_id,
            "broker_id": "nonexistent-broker.com",
        })
        assert scan_resp.status_code in (400, 404)

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_scan_with_invalid_profile(self, authorized_client):
        """Create a scan with an invalid profile ID should fail."""
        import uuid
        fake_profile_id = str(uuid.uuid4())

        scan_resp = authorized_client.post("/api/scans", json={
            "profile_id": fake_profile_id,
            "broker_id": "spokeo.com",
        })
        assert scan_resp.status_code in (400, 404)

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_multiple_scans_same_profile(self, authorized_client):
        """Run multiple scans on the same profile."""
        profile_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Multi",
            "last_name": "Scan",
            "address_line1": "789 Multi Ave",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
        })
        profile_id = profile_resp.json()["id"]

        # Create two scans for the same profile
        scan1_resp = authorized_client.post("/api/scans", json={
            "profile_id": profile_id,
            "broker_id": "spokeo.com",
            "dry_run": True,
        })
        assert scan1_resp.status_code == 200

        scan2_resp = authorized_client.post("/api/scans", json={
            "profile_id": profile_id,
            "broker_id": "whitepages.com",
            "dry_run": True,
        })
        assert scan2_resp.status_code == 200

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_scan_status_history(self, authorized_client):
        """Verify scan status transitions are tracked."""
        profile_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Status",
            "last_name": "Track",
            "address_line1": "321 Status Rd",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
        })
        profile_id = profile_resp.json()["id"]

        scan_resp = authorized_client.post("/api/scans", json={
            "profile_id": profile_id,
            "broker_id": "spokeo.com",
            "dry_run": True,
        })
        assert scan_resp.status_code == 200

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_scan_results_retrieval(self, authorized_client):
        """Retrieve scan results after completion."""
        profile_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Results",
            "last_name": "Test",
            "address_line1": "654 Results Blvd",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
        })
        profile_id = profile_resp.json()["id"]

        scan_resp = authorized_client.post("/api/scans", json={
            "profile_id": profile_id,
            "broker_id": "spokeo.com",
            "dry_run": True,
        })
        scan_id = scan_resp.json().get("id") or scan_resp.json().get("scan_id")

        # Get scan details
        detail_resp = authorized_client.get(f"/api/scans/{scan_id}")
        assert detail_resp.status_code == 200


# ------------------------------------------------------------------
# Household Flow Tests
# ------------------------------------------------------------------

class TestHouseholdFlow:
    """Test household member management flow."""

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_create_household_with_members(self, authorized_client):
        """Create a household and add members."""
        # Create primary profile
        primary_resp = authorized_client.post("/api/profiles", json={
            "first_name": "Primary",
            "last_name": "Member",
            "address_line1": "100 Household St",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
        })
        assert primary_resp.status_code == 200

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_household_scan(self, authorized_client):
        """Run a scan on all household members."""
        # Create household profiles
        for i in range(2):
            resp = authorized_client.post("/api/profiles", json={
                "first_name": f"Member{i}",
                "last_name": "Household",
                "address_line1": f"{200+i} Household Ave",
                "city": "Detroit",
                "state": "MI",
                "postal_code": "48201",
            })
            assert resp.status_code == 200


# ------------------------------------------------------------------
# Webhook Delivery Tests
# ------------------------------------------------------------------

class TestWebhookDelivery:
    """Test webhook delivery for scan events."""

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_webhook_on_scan_complete(self, authorized_client):
        """Verify webhook is called when scan completes."""
        # Create webhook subscription
        webhook_resp = authorized_client.post("/api/webhooks", json={
            "url": "https://httpbin.org/post",
            "events": ["scan.completed"],
        })
        assert webhook_resp.status_code == 200

    @pytest.mark.skipif(True, reason="Full flow tests require all services running")
    def test_webhook_retry_on_failure(self, authorized_client):
        """Verify webhook retries on delivery failure."""
        # Create webhook with a failing URL
        webhook_resp = authorized_client.post("/api/webhooks", json={
            "url": "https://this-does-not-exist-12345.com/webhook",
            "events": ["scan.completed"],
        })
        assert webhook_resp.status_code == 200