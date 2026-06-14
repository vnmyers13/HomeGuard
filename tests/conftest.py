"""Pytest configuration for OpenDataRemoval tests.

Ensures project root and API root are on sys.path so that imports like
'from api.models.xxx', 'from mailwatcher.xxx', and 'from gw_playwright.xxx'
resolve correctly both locally and inside Docker containers.
"""
import sys
import os
import pytest

# Project root (for api/, mailwatcher/, gw_playwright/ module imports)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Also support running from inside the Docker container where code is at /app
_container_app = "/app"
if _container_app not in sys.path:
    sys.path.insert(0, _container_app)


# Skip mailwatcher/playwright tests when running in API container
# (these modules live in separate Docker services)
_mailwatcher_available = False
_playwright_available = False

try:
    import mailwatcher.classifier  # noqa: F401
    _mailwatcher_available = True
except ImportError:
    pass

try:
    import gw_playwright.models  # noqa: F401
    _playwright_available = True
except ImportError:
    pass


def pytest_collection_modifyitems(config, items):
    """Skip mailwatcher/playwright tests when modules aren't available."""
    if not _mailwatcher_available:
        skip_mailwatcher = pytest.mark.skip(reason="mailwatcher module not available")
        for item in items:
            if "mailwatcher" in item.nodeid:
                item.add_marker(skip_mailwatcher)

    if not _playwright_available:
        skip_playwright = pytest.mark.skip(reason="gw_playwright module not available")
        for item in items:
            if "playwright" in item.nodeid:
                item.add_marker(skip_playwright)