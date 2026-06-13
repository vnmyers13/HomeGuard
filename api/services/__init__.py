"""API service layer."""

from __future__ import annotations

__all__ = [
    "AuthService",
    "ProfileService",
    "BrokerService",
    "WebhookService",
    "PlaywrightService",
]

def __getattr__(name: str):
    """Lazy-import service classes only when accessed."""
    import importlib  # local import to avoid eager database pulls

    _modules: dict[str, str] = {
        "AuthService": ".auth_service",
        "ProfileService": ".profile_service",
        "BrokerService": ".broker_service",
        "WebhookService": ".webhook_service",
        "PlaywrightService": ".playwright_service",
    }
    if name not in _modules:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = importlib.import_module(_modules[name], package=__name__)
    return getattr(mod, name)