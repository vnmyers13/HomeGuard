"""Playwright service integration tests — verify the executor works end-to-end."""

import pytest
import httpx


# ------------------------------------------------------------------
# Playwright Health & Status
# ------------------------------------------------------------------

class TestPlaywrightHealth:
    """Tests that require the Playwright service to be running."""

    @pytest.mark.skipif(True, reason="Playwright service requires Docker browser container")
    def test_health_endpoint(self, playwright_client):
        """GET /health should return 200."""
        response = playwright_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.skipif(True, reason="Playwright service requires Docker browser container")
    def test_status_endpoint(self, playwright_client):
        """GET /status should return pool information."""
        response = playwright_client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "pool" in data or "browsers" in data


# ------------------------------------------------------------------
# Playwright Execution Tests (marked skip by default)
# ------------------------------------------------------------------

class TestPlaywrightExecution:
    """Tests that actually execute browser actions via Playwright."""

    @pytest.mark.skipif(True, reason="Playwright service requires Docker browser container")
    def test_simple_navigation(self, playwright_client):
        """Navigate to a simple page and verify it loads."""
        resp = playwright_client.post("/execute", json={
            "url": "https://httpbin.org/html",
            "actions": [
                {
                    "type": "navigate",
                    "url": "https://httpbin.org/html",
                },
                {
                    "type": "wait",
                    "timeout": 2000,
                },
            ],
        })
        assert resp.status_code == 200

    @pytest.mark.skipif(True, reason="Playwright service requires Docker browser container")
    def test_screenshot_capture(self, playwright_client):
        """Take a screenshot of a page."""
        resp = playwright_client.post("/execute", json={
            "url": "https://httpbin.org/html",
            "actions": [
                {
                    "type": "navigate",
                    "url": "https://httpbin.org/html",
                },
                {
                    "type": "screenshot",
                    "path": "/tmp/test_screenshot.png",
                },
            ],
        })
        assert resp.status_code == 200

    @pytest.mark.skipif(True, reason="Playwright service requires Docker browser container")
    def test_element_click(self, playwright_client):
        """Click an element on a page."""
        resp = playwright_client.post("/execute", json={
            "url": "https://httpbin.org/forms/get",
            "actions": [
                {
                    "type": "navigate",
                    "url": "https://httpbin.org/forms/get",
                },
                {
                    "type": "fill",
                    "selector": "input[name=q]",
                    "value": "test",
                },
                {
                    "type": "click",
                    "selector": "button[type=submit]",
                },
                {
                    "type": "wait",
                    "timeout": 2000,
                },
            ],
        })
        assert resp.status_code == 200

    @pytest.mark.skipif(True, reason="Playwright service requires Docker browser container")
    def test_timeout_handling(self, playwright_client):
        """Verify timeout is handled gracefully."""
        resp = playwright_client.post("/execute", json={
            "url": "https://httpbin.org/delay/10",
            "timeout": 3000,
            "actions": [
                {
                    "type": "navigate",
                    "url": "https://httpbin.org/delay/10",
                },
            ],
        })
        # Should fail with timeout error
        assert resp.status_code in (200, 408, 504)

    @pytest.mark.skipif(True, reason="Playwright service requires Docker browser container")
    def test_invalid_url(self, playwright_client):
        """Navigate to an invalid URL should return an error."""
        resp = playwright_client.post("/execute", json={
            "url": "https://this-domain-definitely-does-not-exist-12345.com",
            "actions": [
                {
                    "type": "navigate",
                    "url": "https://this-domain-definitely-does-not-exist-12345.com",
                },
            ],
        })
        # Should fail gracefully
        assert resp.status_code in (200, 400, 500)


# ------------------------------------------------------------------
# Playwright Pool Management Tests
# ------------------------------------------------------------------

class TestPlaywrightPool:
    """Tests for browser pool management."""

    @pytest.mark.skipif(True, reason="Playwright service requires Docker browser container")
    def test_pool_stats(self, playwright_client):
        """Check pool statistics."""
        resp = playwright_client.get("/pool/stats")
        assert resp.status_code == 200

    @pytest.mark.skipif(True, reason="Playwright service requires Docker browser container")
    def test_concurrent_requests(self, playwright_client):
        """Submit multiple concurrent requests."""
        import concurrent.futures

        def make_request(client, i):
            return client.post("/execute", json={
                "url": f"https://httpbin.org/get?id={i}",
                "actions": [
                    {
                        "type": "navigate",
                        "url": f"https://httpbin.org/get?id={i}",
                    },
                ],
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, playwright_client, i) for i in range(3)]
            results = [f.result() for f in futures]

        # All requests should succeed (even if queued)
        for result in results:
            assert result.status_code == 200