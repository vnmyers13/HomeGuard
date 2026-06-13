"""Tests for registry update and broker health check tasks."""

from unittest.mock import MagicMock, patch
import pytest


class TestProcessRegistryUpdateTask:
    """Test process_registry_update_task."""

    @patch("api.workers.tasks.registry.get_db_session")
    def test_task_processes_registry_update(self, mock_get_session):
        from api.workers.tasks.registry import process_registry_update_task

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock broker query
        with patch("api.workers.tasks.registry.Broker") as mock_broker:
            mock_broker_instance = MagicMock()
            mock_broker_instance.domain = "example.com"
            mock_broker.query.return_value.all.return_value = [mock_broker_instance]

            process_registry_update_task.delay()

        mock_session.commit.assert_called()


class TestCheckBrokerHealthTask:
    """Test check_broker_health_task."""

    @patch("api.workers.tasks.registry.get_db_session")
    def test_task_checks_all_brokers(self, mock_get_session):
        from api.workers.tasks.registry import check_broker_health_task

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with patch("api.workers.tasks.registry.Broker") as mock_broker:
            mock_broker_instance = MagicMock()
            mock_broker_instance.domain = "example.com"
            mock_broker_instance.health_status = "healthy"
            mock_broker.query.return_value.all.return_value = [mock_broker_instance]

            check_broker_health_task.delay()

        mock_session.commit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])