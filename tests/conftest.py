"""Pytest configuration for OpenDataRemoval tests.

Ensures project root and API root are on sys.path so that imports like
'from api.models.xxx', 'from mailwatcher.xxx', and 'from gw_playwright.xxx'
resolve correctly both locally and inside Docker containers.
"""
import sys
import os

# Project root (for mailwatcher/, gw_playwright/ module imports)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Add the API root for 'from api.xxx' imports
_api_path = os.path.join(_project_root, "api")
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)

# Also support running from inside the Docker container where code is at /app
_container_app = "/app"
if _container_app not in sys.path:
    sys.path.insert(0, _container_app)