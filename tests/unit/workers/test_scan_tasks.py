"""Unit tests for scanning Celery tasks."""

import pytest
from unittest.mock import patch, MagicMock


class TestDispatchScanTask:
    """Tests for dispatch_scan_task."""

    @patch("workers.tasks.scanning.scan_broker.delay")
    def test_dispatch_scan_task_success(self, mock_scan_broker_delay):
        from workers.tasks.scanning import dispatch_scan_task

        result = dispatch_scan_task("profile-123", "broker-456")

        assert result["status"] == "dispatched"
        assert result["profile_id"] == "profile-123"
        mock_scan_broker_delay.assert_called_once_with("profile-123", "broker-456")

    @patch("workers.tasks.scanning.scan_broker.delay")
    def test_dispatch_scan_task_calls_correctly(self, mock_scan_broker_delay):
        from workers.tasks.scanning import dispatch_scan_task

        dispatch_scan_task("p1", "b1")
        dispatch_scan_task("p2", "b2")

        assert mock_scan_broker_delay.call_count == 2
        mock_scan_broker_delay.assert_any_call("p1", "b1")
        mock_scan_broker_delay.assert_any_call("p2", "b2")


class TestDispatchVerificationScan:
    """Tests for dispatch_verification_scan."""

    @patch("workers.tasks.scanning.scan_broker.delay")
    def test_dispatch_verification_scan(self, mock_scan_broker_delay):
        from workers.tasks.scanning import dispatch_verification_scan

        result = dispatch_verification_scan("profile-123", "broker-456", "request-789")

        assert result["status"] == "dispatched"
        assert result["profile_id"] == "profile-123"
        assert result["broker_id"] == "broker-456"
        mock_scan_broker_delay.assert_called_once()


class TestScanBroker:
    """Tests for scan_broker task."""

    @patch("workers.tasks.scanning._create_scan_run")
    @patch("workers.tasks.scanning.playwright_service.dispatch_job")
    def test_scan_broker_success(self, mock_dispatch, mock_create):
        from workers.tasks.scanning import scan_broker

        mock_create.return_value = {"scan_run_id": "sr-123"}
        mock_dispatch.return_value = {"job_id": "job-456", "result_url": "http://example.com/result"}

        result = scan_broker("profile-123", "broker-456")

        assert result["status"] == "dispatched"
        mock_dispatch.assert_called_once()

    @patch("workers.tasks.scanning._create_scan_run")
    @patch("workers.tasks.scanning.playwright_service.dispatch_job")
    def test_scan_broker_dispatch_failure(self, mock_dispatch, mock_create):
        from workers.tasks.scanning import scan_broker

        mock_create.return_value = {"scan_run_id": "sr-123"}
        mock_dispatch.side_effect = Exception("Service unavailable")

        result = scan_broker("profile-123", "broker-456")

        assert result["status"] == "failed"
        assert "error" in result["result"]