"""Tests for gw_playwright.executor."""

import pytest


class TestExecutor:
    """Test Executor class and error classification."""

    def test_import_executor(self):
        from gw_playwright.executor import Executor
        assert Executor is not None

    def test_import_error_category(self):
        from gw_playwright.executor import ErrorCategory
        assert hasattr(ErrorCategory, 'RETRYABLE')
        assert hasattr(ErrorCategory, 'NON_RETRYABLE')
        assert hasattr(ErrorCategory, 'CAPTCHA')

    def test_import_classify_error(self):
        from gw_playwright.executor import classify_error
        assert callable(classify_error)


class TestClassifyError:
    """Test classify_error function."""

    def test_classifies_timeout_as_retryable(self):
        from gw_playwright.executor import classify_error, ErrorCategory

        result = classify_error("TimeoutError: Navigation timed out")
        assert result == ErrorCategory.RETRYABLE

    def test_classifies_captcha(self):
        from gw_playwright.executor import classify_error, ErrorCategory

        result = classify_error("CAPTCHA challenge detected")
        assert result == ErrorCategory.CAPTCHA

    def test_classifies_blocked_as_non_retryable(self):
        from gw_playwright.executor import classify_error, ErrorCategory

        result = classify_error("Access denied - account blocked")
        assert result == ErrorCategory.NON_RETRYABLE

    def test_default_is_retryable(self):
        from gw_playwright.executor import classify_error, ErrorCategory

        result = classify_error("Unknown error occurred")
        assert result == ErrorCategory.RETRYABLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])