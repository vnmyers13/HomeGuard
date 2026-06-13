"""Tests for error classification in gw_playwright.executor."""

import pytest


class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_error_categories_exist(self):
        from gw_playwright.executor import ErrorCategory

        assert hasattr(ErrorCategory, 'RETRYABLE')
        assert hasattr(ErrorCategory, 'NON_RETRYABLE')
        assert hasattr(ErrorCategory, 'CAPTCHA')


class TestClassifyError:
    """Test classify_error function."""

    def test_classifies_timeout(self):
        from gw_playwright.executor import classify_error, ErrorCategory

        result = classify_error("TimeoutError: Navigation timed out")
        assert result == ErrorCategory.RETRYABLE

    def test_classifies_captcha(self):
        from gw_playwright.executor import classify_error, ErrorCategory

        result = classify_error("CAPTCHA challenge detected")
        assert result == ErrorCategory.CAPTCHA

    def test_classifies_blocked(self):
        from gw_playwright.executor import classify_error, ErrorCategory

        result = classify_error("Access denied - account blocked")
        assert result == ErrorCategory.NON_RETRYABLE

    def test_default_classification(self):
        from gw_playwright.executor import classify_error, ErrorCategory

        result = classify_error("Some unknown error")
        assert result == ErrorCategory.RETRYABLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])