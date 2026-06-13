# ---------------------------------------------------------------------------
# Link Extractor Unit Tests
# ---------------------------------------------------------------------------
# Tests for the opt-out link extraction and classification module.
# Verifies URL extraction from HTML/text, opt-out classification,
# broker domain extraction, and URL normalization.
# ---------------------------------------------------------------------------

import pytest
from mailwatcher.link_extractor import (
    extract_opt_out_links,
    classify_url_as_opt_out,
    extract_urls_from_html,
    extract_urls_from_text,
    extract_broker_domain,
    normalize_opt_out_url,
)


# ---------------------------------------------------------------------------
# classify_url_as_opt_out tests
# ---------------------------------------------------------------------------

class TestClassifyUrlAsOptOut:
    """Tests for opt-out URL classification."""

    def test_opt_out_in_path(self):
        url = "https://spokeo.com/opt-out/remove"
        assert classify_url_as_opt_out(url) is True

    def test_remove_in_path(self):
        url = "https://whitepages.com/privacy/remove-my-info"
        assert classify_url_as_opt_out(url) is True

    def test_privacy_in_path(self):
        url = "https://radaris.com/privacy/dns-request"
        assert classify_url_as_opt_out(url) is True

    def test_do_not_sell_in_path(self):
        url = "https://example.com/do-not-sell"
        assert classify_url_as_opt_out(url) is True

    def test_delete_in_path(self):
        url = "https://broker.com/account/delete"
        assert classify_url_as_opt_out(url) is True

    def test_regular_url_not_opt_out(self):
        url = "https://spokeo.com/search/results"
        assert classify_url_as_opt_out(url) is False

    def test_login_url_not_opt_out(self):
        url = "https://whitepages.com/login"
        assert classify_url_as_opt_out(url) is False

    def test_context_text_match(self):
        url = "https://broker.com/action"
        context = "Click here to opt-out and remove your information"
        assert classify_url_as_opt_out(url, context) is True

    def test_context_text_no_match(self):
        url = "https://broker.com/action"
        context = "Click here to view your profile"
        assert classify_url_as_opt_out(url, context) is False

    def test_empty_context(self):
        url = "https://broker.com/action"
        assert classify_url_as_opt_out(url, "") is False


# ---------------------------------------------------------------------------
# extract_urls_from_html tests
# ---------------------------------------------------------------------------

class TestExtractUrlsFromHtml:
    """Tests for URL extraction from HTML content."""

    def test_extract_href_urls(self):
        html = '<a href="https://example.com/opt-out">Opt Out</a>'
        urls = extract_urls_from_html(html)
        assert "https://example.com/opt-out" in urls

    def test_extract_action_urls(self):
        html = '<form action="https://broker.com/submit">Submit</form>'
        urls = extract_urls_from_html(html)
        assert "https://broker.com/submit" in urls

    def test_multiple_urls(self):
        html = (
            '<a href="https://a.com/link">A</a>'
            '<form action="https://b.com/submit">B</form>'
        )
        urls = extract_urls_from_html(html)
        assert "https://a.com/link" in urls
        assert "https://b.com/submit" in urls

    def test_no_urls(self):
        html = '<p>No links here</p>'
        urls = extract_urls_from_html(html)
        assert len(urls) == 0

    def test_relative_urls_ignored(self):
        html = '<a href="/relative/path">Link</a>'
        urls = extract_urls_from_html(html)
        assert len(urls) == 0


# ---------------------------------------------------------------------------
# extract_urls_from_text tests
# ---------------------------------------------------------------------------

class TestExtractUrlsFromText:
    """Tests for URL extraction from plain text."""

    def test_extract_url_from_text(self):
        text = "Visit https://example.com for more info"
        urls = extract_urls_from_text(text)
        assert "https://example.com" in urls

    def test_multiple_urls_in_text(self):
        text = "See https://a.com and http://b.com/path"
        urls = extract_urls_from_text(text)
        assert "https://a.com" in urls
        assert "http://b.com/path" in urls

    def test_trailing_punctuation_stripped(self):
        text = "Click here: https://example.com."
        urls = extract_urls_from_text(text)
        assert "https://example.com" in urls

    def test_no_urls_in_text(self):
        text = "No URLs in this text"
        urls = extract_urls_from_text(text)
        assert len(urls) == 0


# ---------------------------------------------------------------------------
# extract_opt_out_links tests
# ---------------------------------------------------------------------------

class TestExtractOptOutLinks:
    """Tests for the main opt-out link extraction function."""

    def test_extract_opt_out_from_html(self):
        html = '<a href="https://spokeo.com/opt-out">Remove your info</a>'
        results = extract_opt_out_links(html)
        assert len(results) > 0
        assert results[0]["url"] == "https://spokeo.com/opt-out"
        assert results[0]["confidence"] >= 0.5

    def test_no_opt_out_links(self):
        html = '<a href="https://spokeo.com/search">Search</a>'
        results = extract_opt_out_links(html)
        assert len(results) == 0

    def test_multiple_opt_out_links(self):
        html = (
            '<a href="https://a.com/opt-out">A</a>'
            '<a href="https://b.com/remove">B</a>'
        )
        results = extract_opt_out_links(html)
        assert len(results) >= 2

    def test_results_sorted_by_confidence(self):
        html = (
            '<a href="https://a.com/opt-out">A</a>'
            '<a href="https://b.com/privacy/remove">B</a>'
        )
        results = extract_opt_out_links(html)
        # Results should be sorted by confidence descending
        for i in range(len(results) - 1):
            assert results[i]["confidence"] >= results[i + 1]["confidence"]

    def test_result_structure(self):
        html = '<a href="https://spokeo.com/opt-out">Link</a>'
        results = extract_opt_out_links(html)
        assert len(results) > 0
        result = results[0]
        assert "url" in result
        assert "confidence" in result
        assert "context" in result

    def test_text_content_fallback(self):
        html = "<p>No links</p>"
        text = "Visit https://broker.com/opt-out to remove your data"
        results = extract_opt_out_links(html, text)
        assert len(results) > 0


# ---------------------------------------------------------------------------
# extract_broker_domain tests
# ---------------------------------------------------------------------------

class TestExtractBrokerDomain:
    """Tests for broker domain extraction from URLs."""

    def test_extract_domain(self):
        assert extract_broker_domain("https://spokeo.com/opt-out") == "spokeo.com"

    def test_extract_domain_with_path(self):
        assert extract_broker_domain("https://whitepages.com/privacy/remove?id=123") == "whitepages.com"

    def test_domain_is_lowercased(self):
        assert extract_broker_domain("https://Spokeo.com/page") == "spokeo.com"

    def test_invalid_url_returns_none(self):
        assert extract_broker_domain("not-a-url") is None


# ---------------------------------------------------------------------------
# normalize_opt_out_url tests
# ---------------------------------------------------------------------------

class TestNormalizeOptOutUrl:
    """Tests for URL normalization."""

    def test_remove_tracking_params(self):
        url = "https://spokeo.com/opt-out?utm_source=email&id=123"
        result = normalize_opt_out_url(url)
        assert "utm_source" not in result

    def test_preserve_essential_params(self):
        url = "https://spokeo.com/opt-out?token=abc123"
        result = normalize_opt_out_url(url)
        assert "token=abc123" in result

    def test_remove_fbclid(self):
        url = "https://broker.com/remove?fbclid=123&id=test"
        result = normalize_opt_out_url(url)
        assert "fbclid" not in result

    def test_invalid_url_returns_as_is(self):
        url = "not-a-valid-url"
        result = normalize_opt_out_url(url)
        assert result == "not-a-valid-url"