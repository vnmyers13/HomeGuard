"""Token resolver with SafeDict for placeholder substitution."""

import re
from typing import Any

# Pattern to match {{key}} placeholders
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+(?:\.\w+)*)\}\}")


class SafeDict(dict):
    """dict subclass that renders {{key}} and {{key.nested}} as empty string when missing."""

    def __missing__(self, key: str) -> str:
        return ""


def resolve_tokens(template: str, context: dict[str, Any]) -> str:
    """Replace all {{key}} placeholders in *template* using *context*.

    Missing keys are replaced with empty string (safe for optional tokens).
    Supports dot-notation: {{profile.first_name}}.

    Args:
        template: The action value string containing placeholders.
        context: Key-value pairs to substitute (e.g., profile fields, session data).

    Returns:
        The resolved string with all placeholders replaced.
    """
    safe = SafeDict()
    # Flatten dot-notation keys
    for key, value in context.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                safe[f"{key}.{sub_key}"] = str(sub_value) if sub_value is not None else ""
        else:
            safe[key] = str(value) if value is not None else ""

    def _replacer(match: re.Match) -> str:
        key = match.group(1)
        return safe.get(key, "")

    return _PLACEHOLDER_RE.sub(_replacer, template)


def resolve_all(action_values: list[str], context: dict[str, Any]) -> list[str]:
    """Resolve tokens in a list of action value strings."""
    return [resolve_tokens(v, context) for v in action_values]


def find_placeholders(template: str) -> list[str]:
    """Extract all placeholder keys from a template string."""
    return _PLACEHOLDER_RE.findall(template)


def validate_context(template: str, context: dict[str, Any]) -> list[str]:
    """Return list of missing placeholder keys that have no value in context."""
    placeholders = find_placeholders(template)
    safe = SafeDict()
    for key, value in context.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                safe[f"{key}.{sub_key}"] = sub_value
        else:
            safe[key] = value

    return [p for p in placeholders if p not in safe or safe[p] is None]