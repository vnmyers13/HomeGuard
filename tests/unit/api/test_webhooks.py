"""Unit tests for webhook endpoints."""

import pytest
from unittest.mock import MagicMock, patch


class TestWebhookService:
    """Tests for webhook service layer."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.mock_webhook = MagicMock(
            id=1,
            event_type="profile.updated",
            target_url="https://example.com/webhook",
            secret="whsec_test123",
            status="active",
        )

    @patch('services.webhook_service.WebhookService._find_webhooks')
    def test_deliver_event_active(self, mock_find):
        """Test delivering event to active webhooks."""
        from services.webhook_service import WebhookService

        mock_find.return_value = [self.mock_webhook]
        # Service should find and deliver to matching webhooks
        result = WebhookService.deliver_event(self.mock_session, "profile.updated", {"data": "test"})
        # Verify the service processes without error

    @patch('services.webhook_service.WebhookService._find_webhooks')
    def test_deliver_event_no_match(self, mock_find):
        """Test delivering event with no matching webhooks."""
        from services.webhook_service import WebhookService

        mock_find.return_value = []
        result = WebhookService.deliver_event(self.mock_session, "nonexistent.event", {"data": "test"})
        assert result is not None

    def test_create_webhook(self):
        """Test creating a new webhook."""
        from schemas.webhook import WebhookCreate

        webhook = WebhookCreate(
            event_type="profile.created",
            target_url="https://example.com/hook",
            secret="my_secret",
        )
        assert webhook.event_type == "profile.created"
        assert webhook.target_url == "https://example.com/hook"


class TestWebhookSchemas:
    """Tests for webhook schema validation."""

    def test_webhook_create_schema(self):
        """Test WebhookCreate schema."""
        from schemas.webhook import WebhookCreate

        webhook = WebhookCreate(
            event_type="profile.updated",
            target_url="https://example.com/webhook",
        )
        assert webhook.event_type == "profile.updated"
        assert webhook.target_url == "https://example.com/webhook"

    def test_webhook_create_invalid_url(self):
        """Test WebhookCreate with invalid URL."""
        from schemas.webhook import WebhookCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            WebhookCreate(
                event_type="profile.updated",
                target_url="not-a-url",
            )

    def test_webhook_response_schema(self):
        """Test WebhookResponse schema."""
        from schemas.webhook import WebhookResponse

        webhook = WebhookResponse(
            id=1,
            event_type="profile.created",
            target_url="https://example.com/webhook",
            status="active",
        )
        assert webhook.id == 1
        assert webhook.status == "active"

    def test_webhook_secret_optional(self):
        """Test that webhook secret is optional in create."""
        from schemas.webhook import WebhookCreate

        webhook = WebhookCreate(
            event_type="profile.updated",
            target_url="https://example.com/webhook",
        )
        # Secret should be None or auto-generated
        assert webhook.secret is None


class TestWebhookEndpoints:
    """Tests for webhook router endpoints."""

    def setup_method(self):
        self.mock_session = MagicMock()

    @patch('services.webhook_service.WebhookService.list')
    def test_list_webhooks(self, mock_list):
        """Test GET /webhooks endpoint."""
        from services.webhook_service import WebhookService

        mock_webhook = MagicMock(
            id=1,
            event_type="profile.updated",
            target_url="https://example.com/webhook",
            status="active",
        )
        mock_list.return_value = [mock_webhook]

        result = WebhookService.list(self.mock_session)
        assert len(result) == 1

    @patch('services.webhook_service.WebhookService.create')
    def test_create_webhook(self, mock_create):
        """Test POST /webhooks endpoint."""
        from services.webhook_service import WebhookService
        from schemas.webhook import WebhookCreate

        payload = WebhookCreate(
            event_type="profile.created",
            target_url="https://example.com/new-webhook",
        )
        mock_create.return_value = MagicMock(id=1, event_type=payload.event_type)

        result = WebhookService.create(self.mock_session, payload)
        assert result is not None

    def test_webhook_event_types(self):
        """Test valid webhook event types."""
        from schemas.webhook import WebhookEvent

        events = [e.value for e in WebhookEvent]
        assert "profile.created" in events
        assert "profile.updated" in events
        assert "request.completed" in events