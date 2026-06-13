"""Tests for notification Celery tasks."""

from unittest.mock import MagicMock, patch
import pytest


class TestSendNotificationTask:
    """Test send_notification_task."""

    @patch("api.workers.tasks.notifications.get_db_session")
    def test_task_sends_notification(self, mock_get_session):
        from api.workers.tasks.notifications import send_notification_task

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with patch("api.workers.tasks.notifications.Notification") as mock_notification:
            mock_notif = MagicMock()
            mock_notif.id = "notif-001"
            mock_notif.type = "scan_complete"
            mock_notif.recipient_id = "user-123"
            mock_notification.by_id.return_value = mock_notif

            send_notification_task.delay("notif-001")

        mock_session.commit.assert_called()


class TestProcessPendingNotificationsTask:
    """Test process_pending_notifications_task."""

    @patch("api.workers.tasks.notifications.get_db_session")
    def test_task_processes_pending_notifications(self, mock_get_session):
        from api.workers.tasks.notifications import process_pending_notifications_task

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with patch("api.workers.tasks.notifications.Notification") as mock_notification:
            mock_notif = MagicMock()
            mock_notif.id = "notif-001"
            mock_notification.query.return_value.filter.return_value.all.return_value = [mock_notif]

            process_pending_notifications_task.delay()

        mock_session.commit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])