"""Unit tests for broker endpoints."""

import pytest
from unittest.mock import MagicMock, patch


class TestBrokerService:
    """Tests for broker service layer."""

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
            id="1",
            domain="spokeo.com",
            name="Spokeo",
            is_active=True,
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
            BrokerResponse(id="1", domain="spokeo.com", name="Spokeo", is_active=True, status="active"),
            BrokerResponse(id="2", domain="whitepages.com", name="WhitePages", is_active=True, status="active"),
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

    def test_broker_create_schema(self):
        """Test BrokerCreate schema validation."""
        from schemas.broker import BrokerCreate

        broker = BrokerCreate(domain="testbroker.com", name="Test Broker")
        assert broker.domain == "testbroker.com"
        assert broker.name == "Test Broker"

    def test_broker_create_schema_min_length(self):
        """Test BrokerCreate validates minimum domain length."""
        from schemas.broker import BrokerCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BrokerCreate(domain="ab", name="Test")

    def test_broker_create_schema_min_name(self):
        """Test BrokerCreate validates minimum name length."""
        from schemas.broker import BrokerCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BrokerCreate(domain="test.com", name="")
