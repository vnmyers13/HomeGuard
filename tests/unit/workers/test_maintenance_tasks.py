"""Unit tests for maintenance Celery tasks."""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestCleanupOldSessions:
    """Tests for cleanup_old_sessions."""

    @patch("workers.tasks.maintenance.get_async_session")
    def test_cleanup_old_sessions_success(self, mock_session):
        from workers.tasks.maintenance import cleanup_old_sessions

        mock_async_ctx = MagicMock()
        mock_session.return_value.__aenter__.return_value = mock_async_ctx
        mock_session.return_value.__aexit__.return_value = None

        result = cleanup_old_sessions(max_age_days=30)

        assert result is None  # Task logs but returns nothing on success


class TestCleanupOldScans:
    """Tests for cleanup_old_scans."""

    @patch("workers.tasks.maintenance.get_async_session")
    def test_cleanup_old_scans_success(self, mock_session):
        from workers.tasks.maintenance import cleanup_old_scans

        mock_async_ctx = MagicMock()
        mock_session.return_value.__aenter__.return_value = mock_async_ctx
        mock_session.return_value.__aexit__.return_value = None

        result = cleanup_old_scans(max_age_days=90)

        assert result is None


class TestPurgeExpiredScreenshots:
    """Tests for purge_expired_screenshots."""

    @patch("workers.tasks.maintenance.glob.glob")
    @patch("workers.tasks.maintenance.os.path.getmtime")
    @patch("workers.tasks.maintenance.os.remove")
    def test_purge_expired_screenshots_removes_old_files(
        self, mock_remove, mock_getmtime, mock_glob
    ):
        from workers.tasks.maintenance import purge_expired_screenshots

        cutoff = datetime.utcnow() - timedelta(days=30)
        old_time = (datetime.utcnow() - timedelta(days=60)).timestamp()

        mock_glob.return_value = ["/tmp/screenshots/old1.png", "/tmp/screenshots/old2.png"]
        mock_getmtime.return_value = old_time

        result = purge_expired_screenshots(max_age_days=30)

        assert result == 2
        assert mock_remove.call_count == 2

    @patch("workers.tasks.maintenance.glob.glob")
    def test_purge_expired_screenshots_no_files(self, mock_glob):
        from workers.tasks.maintenance import purge_expired_screenshots

        mock_glob.return_value = []

        result = purge_expired_screenshots(max_age_days=30)

        assert result == 0


class TestComputeDiskUsage:
    """Tests for compute_disk_usage."""

    @patch("workers.tasks.maintenance.shutil.disk_usage")
    def test_compute_disk_usage_success(self, mock_disk_usage):
        from workers.tasks.maintenance import compute_disk_usage

        mock_disk_usage.return_value.used = 1024

        result = compute_disk_usage()

        assert "screenshots" in result
        assert "playbooks" in result

    @patch("workers.tasks.maintenance.shutil.disk_usage")
    def test_compute_disk_usage_handles_error(self, mock_disk_usage):
        from workers.tasks.maintenance import compute_disk_usage

        mock_disk_usage.side_effect = OSError("Permission denied")

        result = compute_disk_usage()

        assert result["screenshots"] == 0
        assert result["playbooks"] == 0


class TestHealthCheck:
    """Tests for health_check."""

    @patch("workers.tasks.maintenance.get_async_session")
    def test_health_check_all_pass(self, mock_session):
        from workers.tasks.maintenance import health_check

        mock_async_ctx = MagicMock()
        mock_session.return_value.__aenter__.return_value = mock_async_ctx
        mock_session.return_value.__aexit__.return_value = None

        result = health_check()

        assert "database" in result
        assert "redis" in result
        assert result["redis"] is True

    @patch("workers.tasks.maintenance.get_async_session")
    def test_health_check_db_failure(self, mock_session):
        from workers.tasks.maintenance import health_check

        mock_async_ctx = MagicMock()
        mock_session.return_value.__aenter__.return_value = mock_async_ctx
        mock_session.return_value.__aexit__.return_value = None
        mock_async_ctx.execute.side_effect = Exception("Connection refused")

        result = health_check()

        assert result["database"] is False
        assert result["redis"] is True  # Redis still passes