"""Unit tests for authentication endpoints."""

import pytest
from unittest.mock import MagicMock, patch


class TestAuthService:
    """Tests for auth service layer."""

    def setup_method(self):
        self.mock_session = MagicMock()

    @patch('services.auth_service.otp')
    def test_generate_otp_code(self, mock_otp):
        """Test OTP code generation."""
        from services.auth_service import AuthService

        mock_otp.random_text.return_value = "ABCDEF"
        code = AuthService.generate_code()
        assert len(code) == 6
        assert code.isdigit()

    @patch('services.auth_service.otp')
    def test_create_magic_link(self, mock_otp):
        """Test magic link token creation."""
        from services.auth_service import AuthService

        mock_otp.random_text.return_value = "testtoken123"
        token = AuthService.create_magic_link("user@example.com")
        assert "user@example.com" in token

    def test_verify_magic_link_valid(self):
        """Test valid magic link verification."""
        from services.auth_service import AuthService

        token = "user@example.com:token123"
        result = AuthService.verify_magic_link(token, "token123")
        assert result == "user@example.com"

    def test_verify_magic_link_invalid(self):
        """Test invalid magic link verification."""
        from services.auth_service import AuthService

        token = "user@example.com:token123"
        result = AuthService.verify_magic_link(token, "wrong_token")
        assert result is None

    def test_verify_magic_link_malformed(self):
        """Test malformed magic link verification."""
        from services.auth_service import AuthService

        result = AuthService.verify_magic_link("malformed", "token")
        assert result is None


class TestAuthEndpoints:
    """Tests for auth router endpoints."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.mock_request = MagicMock()

    @patch('services.auth_service.AuthService.create_magic_link')
    def test_request_code_success(self, mock_create):
        """Test successful code request."""
        from schemas.auth import CodeRequest

        mock_create.return_value = "test_token"
        payload = CodeRequest(email="user@example.com")

        # Verify schema validation works
        assert payload.email == "user@example.com"

    def test_code_request_invalid_email(self):
        """Test code request with invalid email."""
        from schemas.auth import CodeRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CodeRequest(email="not-an-email")

    def test_verify_code_schema(self):
        """Test verify code schema validation."""
        from schemas.auth import CodeVerify

        payload = CodeVerify(email="user@example.com", code="123456")
        assert payload.email == "user@example.com"
        assert payload.code == "123456"
        assert len(payload.code) == 6

    def test_verify_code_invalid_format(self):
        """Test verify code with invalid code format."""
        from schemas.auth import CodeVerify
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CodeVerify(email="user@example.com", code="123")  # too short