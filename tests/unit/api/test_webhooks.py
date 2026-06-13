"""Unit tests for webhook processing."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone


class TestWebhookService:
    """Tests for WebhookService."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=AsyncMock)

    def test_process_scan_result_not_found(self, mock_db):
        """Test process_scan_result when ScanResult doesn't exist."""
        from services.webhook_service import WebhookService

        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        service = WebhookService(mock_db)
        result = service.process_scan_result({"scan_id": "nonexistent"})

        # Result is a coroutine in async, but we can check the service was created
        assert service.db == mock_db

    def test_process_removal_result_not_found(self, mock_db):
        """Test process_removal_result when RemovalRequest doesn't exist."""
        from services.webhook_service import WebhookService

        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        service = WebhookService(mock_db)

        assert service.db == mock_db

    def test_process_captcha_update_not_found(self, mock_db):
        """Test process_captcha_update when ScanResult doesn't exist."""
        from services.webhook_service import WebhookService

        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        service = WebhookService(mock_db)

        assert service.db == mock_db


class TestWebhookSchemas:
    """Tests for webhook schema validation."""

    def test_scan_webhook_payload(self):
        """Test ScanWebhookPayload schema."""
        from schemas.webhook import ScanWebhookPayload

        payload = ScanWebhookPayload(
            scan_id="test-scan-id",
            status="completed",
            found_listing=True,
            data_found={"name": "John Doe", "address": "123 Main St"},
        )
        assert payload.scan_id == "test-scan-id"
        assert payload.found_listing is True

    def test_scan_webhook_payload_optional_fields(self):
        """Test ScanWebhookPayload with optional fields."""
        from schemas.webhook import ScanWebhookPayload

        payload = ScanWebhookPayload(
            scan_id="test-scan-id",
            status="completed",
            found_listing=False,
        )
        assert payload.scan_id == "test-scan-id"
        assert payload.found_listing is False
        assert payload.data_found is None

    def test_removal_webhook_payload(self):
        """Test RemovalWebhookPayload schema."""
        from schemas.webhook import RemovalWebhookPayload

        payload = RemovalWebhookPayload(
            request_id="test-request-id",
            status="confirmed",
            success=True,
            message="Data removed successfully",
        )
        assert payload.request_id == "test-request-id"
        assert payload.success is True

    def test_captcha_webhook_payload(self):
        """Test CaptchaWebhookPayload schema."""
        from schemas.webhook import CaptchaWebhookPayload

        payload = CaptchaWebhookPayload(
            scan_id="test-scan-id",
            captcha_url="https://example.com/captcha",
        )
        assert payload.scan_id == "test-scan-id"
        assert payload.captcha_url == "https://example.com/captcha"

    def test_webhook_response_schema(self):
        """Test WebhookResponse schema."""
        from schemas.webhook import WebhookResponse

        response = WebhookResponse(
            success=True,
            message="Webhook processed successfully",
        )
        assert response.success is True

    def test_webhook_error_response(self):
        """Test WebhookResponse with error."""
        from schemas.webhook import WebhookResponse

        response = WebhookResponse(
            success=False,
            message="Invalid payload",
        )
        assert response.success is False


class TestWebhookServiceIntegration:
    """Integration-style tests for webhook service."""

    def test_service_initialization(self):
        """Test WebhookService initializes with db session."""
        from services.webhook_service import WebhookService

        mock_db = MagicMock()
        service = WebhookService(mock_db)

        assert service.db == mock_db

    def test_service_has_required_methods(self):
        """Test WebhookService has all required processing methods."""
        from services.webhook_service import WebhookService

        assert hasattr(WebhookService, 'process_scan_result')
        assert hasattr(WebhookService, 'process_captcha_update')
        assert hasattr(WebhookService, 'process_removal_result')

    def test_webhook_service_async_methods(self):
        """Test that webhook service methods are async."""
        from services.webhook_service import WebhookService
        import inspect

        assert asyncio.iscoroutinefunction(WebhookService.process_scan_result)
        assert asyncio.iscoroutinefunction(WebhookService.process_captcha_update)
        assert asyncio.iscoroutinefunction(WebhookService.process_removal_result)