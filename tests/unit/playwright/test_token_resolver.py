"""Tests for the gw_playwright.token_resolver module."""

import pytest


class TestResolveTokens:
    """Test resolve_tokens function."""

    def test_import_works(self):
        from gw_playwright.token_resolver import resolve_tokens, SafeDict
        assert resolve_tokens is not None
        assert SafeDict is not None

    def test_simple_placeholder(self):
        from gw_playwright.token_resolver import resolve_tokens

        result = resolve_tokens("Hello {{name}}!", {"name": "World"})
        assert result == "Hello World!"

    def test_multiple_placeholders(self):
        from gw_playwright.token_resolver import resolve_tokens

        result = resolve_tokens(
            "{{first}} {{last}}",
            {"first": "John", "last": "Doe"}
        )
        assert result == "John Doe"

    def test_missing_key_returns_empty(self):
        from gw_playwright.token_resolver import resolve_tokens

        result = resolve_tokens("Hello {{name}}!", {})
        assert result == "Hello !"

    def test_dot_notation(self):
        from gw_playwright.token_resolver import resolve_tokens

        result = resolve_tokens(
            "{{profile.first_name}} {{profile.last_name}}",
            {"profile": {"first_name": "Jane", "last_name": "Smith"}}
        )
        assert result == "Jane Smith"

    def test_mixed_simple_and_nested(self):
        from gw_playwright.token_resolver import resolve_tokens

        result = resolve_tokens(
            "{{name}} - {{user.email}}",
            {"name": "Test", "user": {"email": "test@example.com"}}
        )
        assert result == "Test - test@example.com"

    def test_no_placeholders(self):
        from gw_playwright.token_resolver import resolve_tokens

        result = resolve_tokens("Hello World!", {})
        assert result == "Hello World!"


class TestResolveAll:
    """Test resolve_all function."""

    def test_resolve_list(self):
        from gw_playwright.token_resolver import resolve_all

        values = ["Hello {{name}}", "Goodbye {{name}}"]
        context = {"name": "Alice"}
        result = resolve_all(values, context)
        assert result == ["Hello Alice", "Goodbye Alice"]


class TestFindPlaceholders:
    """Test find_placeholders function."""

    def test_extract_simple(self):
        from gw_playwright.token_resolver import find_placeholders

        result = find_placeholders("Hello {{name}}!")
        assert result == ["name"]

    def test_extract_multiple(self):
        from gw_playwright.token_resolver import find_placeholders

        result = find_placeholders("{{first}} {{last}}")
        assert result == ["first", "last"]

    def test_extract_dot_notation(self):
        from gw_playwright.token_resolver import find_placeholders

        result = find_placeholders("{{profile.first_name}}")
        assert result == ["profile.first_name"]

    def test_no_placeholders(self):
        from gw_playwright.token_resolver import find_placeholders

        result = find_placeholders("Hello World!")
        assert result == []


class TestValidateContext:
    """Test validate_context function."""

    def test_no_missing_keys(self):
        from gw_playwright.token_resolver import validate_context

        result = validate_context("Hello {{name}}!", {"name": "World"})
        assert result == []

    def test_missing_keys(self):
        from gw_playwright.token_resolver import validate_context

        result = validate_context("{{first}} {{last}}", {"first": "John"})
        assert result == ["last"]

    def test_none_value_is_missing(self):
        from gw_playwright.token_resolver import validate_context

        result = validate_context("{{name}}", {"name": None})
        assert result == ["name"]

    def test_dot_notation_validation(self):
        from gw_playwright.token_resolver import validate_context

        result = validate_context(
            "{{profile.first_name}} {{profile.last_name}}",
            {"profile": {"first_name": "Jane"}}
        )
        assert result == ["profile.last_name"]


class TestSafeDict:
    """Test SafeDict class."""

    def test_missing_key_returns_empty_string(self):
        from gw_playwright.token_resolver import SafeDict

        d = SafeDict()
        assert d["nonexistent"] == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])