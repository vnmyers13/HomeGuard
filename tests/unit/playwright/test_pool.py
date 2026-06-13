"""Tests for gw_playwright.pool."""

import pytest


class TestBrowserPool:
    """Test BrowserPool class."""

    def test_import_pool(self):
        from gw_playwright.pool import BrowserPool
        assert BrowserPool is not None

    def test_import_launch_context(self):
        from gw_playwright.pool import launch_context
        assert callable(launch_context)


class TestLaunchContext:
    """Test launch_context function."""

    def test_launch_context_is_callable(self):
        from gw_playwright.pool import launch_context
        assert callable(launch_context)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])