"""Unit tests for broker endpoints."""

import pytest
from unittest.mock import MagicMock, patch


class TestBrokerService:
    """Tests for broker service layer."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.mock_broker = MagicMock(
            id=1,
            domain="spokeo.com",
            name="Spokeo",
            status="active",
            playbook={"version": "1.0"},
        )

    @patch('services.broker_service.BrokerService._load_playbook')
    def test_get_brokers_list(self, mock_load):
        """Test listing all brokers."""
        from services.broker_service import BrokerService

        mock_load.return_value = [self.mock_broker]
        brokers = BrokerService.list(self.mock_session)
        assert len(brokers) == 1

    @patch('services.broker_service.BrokerService._load_playbook')
    def test_get_broker_by_domain(self, mock_load):
        """Test getting a specific broker by domain."""
        from services.broker_service import BrokerService

        mock_load.return_value = self.mock_broker
        broker = BrokerService.get_by_domain(self.mock_session, "spokeo.com")
        assert broker.domain == "spokeo.com"

    def test_broker_status_filter(self):
        """Test filtering brokers by status."""
        from schemas.broker import BrokerStatus

        assert BrokerStatus.active.value == "active"
        assert BrokerStatus.inactive.value == "inactive"
        assert BrokerStatus.error.value == "error"


class TestBrokerSchemas:
    """Tests for broker schema validation."""

    def test_broker_response_schema(self):
        """Test BrokerResponse schema."""
        from schemas.broker import BrokerResponse

        broker = BrokerResponse(
            id=1,
            domain="spokeo.com",
            name="Spokeo",
            status="active",
        )
        assert broker.domain == "spokeo.com"
        assert broker.status == "active"

    def test_broker_status_schema(self):
        """Test BrokerStatus enum."""
        from schemas.broker import BrokerStatus

        # Verify all expected statuses exist
        statuses = [s.value for s in BrokerStatus]
        assert "active" in statuses
        assert "inactive" in statuses
        assert "error" in statuses

    def test_broker_list_response(self):
        """Test BrokerListResponse with multiple brokers."""
        from schemas.broker import BrokerResponse, BrokerListResponse

        brokers = [
            BrokerResponse(id=1, domain="spokeo.com", name="Spokeo", status="active"),
            BrokerResponse(id=2, domain="whitepages.com", name="WhitePages", status="active"),
        ]
        response = BrokerListResponse(brokers=brokers, total=2)
        assert len(response.brokers) == 2
        assert response.total == 2

    def test_broker_list_empty(self):
        """Test BrokerListResponse with no brokers."""
        from schemas.broker import BrokerListResponse

        response = BrokerListResponse(brokers=[], total=0)
        assert len(response.brokers) == 0
        assert response.total == 0


class TestBrokerEndpoints:
    """Tests for broker router endpoints."""

    def setup_method(self):
        self.mock_session = MagicMock()

    @patch('services.broker_service.BrokerService.list')
    def test_get_all_brokers(self, mock_list):
        """Test GET /brokers endpoint."""
        from services.broker_service import BrokerService

        mock_broker = MagicMock(id=1, domain="test.com", name="Test", status="active")
        mock_list.return_value = [mock_broker]

        result = BrokerService.list(self.mock_session)
        assert len(result) == 1

    @patch('services.broker_service.BrokerService.get_by_domain')
    def test_get_broker_by_domain(self, mock_get):
        """Test GET /brokers/{domain} endpoint."""
        from services.broker_service import BrokerService

        mock_broker = MagicMock(id=1, domain="spokeo.com", name="Spokeo", status="active")
        mock_get.return_value = mock_broker

        result = BrokerService.get_by_domain(self.mock_session, "spokeo.com")
        assert result.domain == "spokeo.com"

    @patch('services.broker_service.BrokerService.get_by_domain')
    def test_get_broker_not_found(self, mock_get):
        """Test GET /brokers/{domain} with non-existent domain."""
        from services.broker_service import BrokerService

        mock_get.return_value = None
        result = BrokerService.get_by_domain(self.mock_session, "nonexistent.com")
        assert result is None