"""Pytest configuration for HomeGuard tests.

Ensures /app (the API root inside the container) is on sys.path
so that imports like 'from services.xxx' and 'from schemas.xxx' resolve.
"""
import sys
import os

# Add the API root (/app inside container, or project root's api/ dir locally)
_app_path = os.path.join(os.path.dirname(__file__), "..", "api")
if _app_path not in sys.path:
    sys.path.insert(0, _app_path)

# Also support running from inside the Docker container where tests are at /app/tests
_container_app = "/app"
if _container_app not in sys.path:
    sys.path.insert(0, _container_app)