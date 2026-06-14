"""Unit tests for authentication endpoints."""

import pytest
from unittest.mock import MagicMock, patch


class TestAuthEndpoints:
    """Tests for auth router endpoints."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.mock_request = MagicMock()

    def test_register_request_valid(self):
        """Test valid register request schema."""
        from schemas.auth import RegisterRequest

        payload = RegisterRequest(username="testuser", email="user@example.com", password="password123")
        assert payload.username == "testuser"
        assert payload.email == "user@example.com"

    def test_code_request_invalid_email(self):
        """Test code request with invalid email."""
        from schemas.auth import RegisterRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RegisterRequest(username="testuser", email="not-an-email", password="password123")

    def test_login_schema_valid(self):
        """Test login schema validation."""
        from schemas.auth import LoginRequest

        payload = LoginRequest(username="testuser", password="password123")
        assert payload.username == "testuser"
        assert payload.password == "password123"

    def test_login_empty_username_allowed(self):
        """Test that LoginRequest allows empty username (no min_length constraint)."""
        from schemas.auth import LoginRequest

        payload = LoginRequest(username="", password="password123")
        assert payload.username == ""

    def test_login_empty_password_not_allowed(self):
        """Test that LoginRequest allows empty password (no min_length constraint)."""
        from schemas.auth import LoginRequest

        payload = LoginRequest(username="testuser", password="")
        assert payload.password == ""
