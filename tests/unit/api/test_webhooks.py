"""Unit tests for webhook processing."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
import asyncio


class TestWebhookService:
    """Tests for WebhookService."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_process_scan_result_not_found(self, mock_db):
        """Test process_scan_result when ScanResult doesn't exist."""
        from services.webhook_service import WebhookService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        service = WebhookService(mock_db)
        result = await service.process_scan_result({"scan_id": "nonexistent"})

        assert result == {"error": "scan_not_found"}

    @pytest.mark.asyncio
    async def test_process_removal_result_not_found(self, mock_db):
        """Test process_removal_result when RemovalRequest doesn't exist."""
        from services.webhook_service import WebhookService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        service = WebhookService(mock_db)

        result = await service.process_removal_result({"request_id": "nonexistent"})
        assert result == {"error": "removal_request_not_found"}

    @pytest.mark.asyncio
    async def test_process_captcha_update_not_found(self, mock_db):
        """Test process_captcha_update when ScanResult doesn't exist."""
        from services.webhook_service import WebhookService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        service = WebhookService(mock_db)

        result = await service.process_captcha_update({"scan_id": "nonexistent"})
        assert result == {"error": "scan_not_found"}


class TestWebhookSchemas:
    """Tests for webhook schema validation."""

    def test_scan_webhook_payload(self):
        """Test WebhookScanResult schema."""
        from schemas.webhook import WebhookScanResult

        payload = WebhookScanResult(
            scan_id="test-scan-id",
            broker_domain="example.com",
            found_listing=True,
            data_found={"name": "John Doe", "address": "123 Main St"},
        )
        assert payload.scan_id == "test-scan-id"
        assert payload.found_listing is True

    def test_scan_webhook_payload_optional_fields(self):
        """Test WebhookScanResult with optional fields."""
        from schemas.webhook import WebhookScanResult

        payload = WebhookScanResult(
            scan_id="test-scan-id",
            broker_domain="example.com",
            found_listing=False,
        )
        assert payload.scan_id == "test-scan-id"
        assert payload.found_listing is False
        assert payload.data_found is None

    def test_removal_webhook_payload(self):
        """Test WebhookRemovalResult schema."""
        from schemas.webhook import WebhookRemovalResult

        payload = WebhookRemovalResult(
            request_id="test-request-id",
            broker_domain="example.com",
            success=True,
            status="confirmed",
            message="Data removed successfully",
        )
        assert payload.request_id == "test-request-id"
        assert payload.success is True

    def test_captcha_webhook_payload(self):
        """Test WebhookCAPAUpdate schema."""
        from schemas.webhook import WebhookCAPAUpdate

        payload = WebhookCAPAUpdate(
            scan_id="test-scan-id",
            broker_domain="example.com",
            captcha_required=True,
        )
        assert payload.scan_id == "test-scan-id"
        assert payload.captcha_required is True

    def test_webhook_ack_response(self):
        """Test WebhookAckResponse schema."""
        from schemas.webhook import WebhookAckResponse

        response = WebhookAckResponse()
        assert response.received is True

    def test_webhook_ack_response_custom(self):
        """Test WebhookAckResponse with custom values."""
        from schemas.webhook import WebhookAckResponse

        response = WebhookAckResponse(received=False)
        assert response.received is False


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

        assert asyncio.iscoroutinefunction(WebhookService.process_scan_result)
        assert asyncio.iscoroutinefunction(WebhookService.process_captcha_update)
        assert asyncio.iscoroutinefunction(WebhookService.process_removal_result)
