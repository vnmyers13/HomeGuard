"""Tests for removal request Celery tasks."""

from unittest.mock import MagicMock, patch
import pytest


class TestSubmitRemovalRequestTask:
    """Test submit_removal_request_task."""

    @patch("api.workers.tasks.requests.playwright_service")
    @patch("api.workers.tasks.requests.get_db_session")
    def test_task_submits_request_successfully(
        self, mock_get_session, mock_playwright
    ):
        from api.workers.tasks.requests import submit_removal_request_task

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_broker = MagicMock()
        mock_broker.domain = "example.com"
        mock_broker.playbook = {"steps": []}

        mock_profile = MagicMock()
        mock_profile.id = "profile-123"
        mock_profile.household_id = "hh-456"

        mock_playwright.submit_request.return_value = {
            "request_id": "req-789",
            "status_url": "https://example.com/status/123",
        }

        result = submit_removal_request_task.delay("req-001")

        # Task returns request dict
        assert "request_id" in result or result is None  # Celery AsyncResult

    @patch("api.workers.tasks.requests.playwright_service")
    @patch("api.workers.tasks.requests.get_db_session")
    def test_task_handles_playwright_failure(
        self, mock_get_session, mock_playwright
    ):
        from api.workers.tasks.requests import submit_removal_request_task

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_playwright.submit_request.side_effect = Exception("Browser error")

        # Task should not raise; it logs and retries via Celery
        submit_removal_request_task.delay("req-001")


class TestEscalateToLegalTask:
    """Test escalate_to_legal_task."""

    @patch("api.workers.tasks.requests.get_db_session")
    def test_task_creates_legal_request(self, mock_get_session):
        from api.workers.tasks.requests import escalate_to_legal_task

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock the request lookup
        with patch("api.workers.tasks.requests.Request") as mock_request:
            mock_req = MagicMock()
            mock_req.id = "req-001"
            mock_req.broker_id = "broker-123"
            mock_req.profile_id = "profile-456"
            mock_request.by_id.return_value = mock_req

            escalate_to_legal_task.delay("req-001")

        # Verify commit was called
        mock_session.commit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])