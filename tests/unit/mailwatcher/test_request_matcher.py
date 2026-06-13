"""Tests for mailwatcher.request_matcher module.

All matching functions are designed to work offline (no DB dependency) and
accept plain dicts as request objects.
"""

from datetime import datetime, timedelta, timezone

import pytest

from mailwatcher.request_matcher import (
    correlate_email_to_request,
    extract_broker_from_domain,
    extract_email_domain,
    extract_in_reply_to,
    extract_message_id,
    extract_references,
    match_by_broker_and_user,
    match_by_message_id,
    match_by_temporal_proximity,
    match_by_url_in_response,
    update_request_with_response,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_request():
    """A single pending removal request as a dict."""
    return {
        "id": 1,
        "user_id": 42,
        "broker_domain": "spokeo.com",
        "status": "submitted",
        "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
        "metadata": {
            "message_id": "test-message-123",
            "target_url": "https://spokeo.com/profile/12345",
        },
    }


@pytest.fixture
def multiple_requests(sample_request):
    """Multiple pending requests for the same user."""
    req2 = {
        "id": 2,
        "user_id": 42,
        "broker_domain": "whitepages.com",
        "status": "pending",
        "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
        "metadata": {},
    }
    req3 = {
        "id": 3,
        "user_id": 42,
        "broker_domain": "spokeo.com",
        "status": "submitted",
        "created_at": datetime.now(timezone.utc) - timedelta(days=30),  # old
        "metadata": {},
    }
    return [sample_request, req2, req3]


# ---------------------------------------------------------------------------
# extract_email_domain tests
# ---------------------------------------------------------------------------

class TestExtractEmailDomain:

    def test_valid_email(self):
        assert extract_email_domain("noreply@spokeo.com") == "spokeo.com"

    def test_none_input(self):
        assert extract_email_domain(None) is None

    def test_no_at_symbol(self):
        assert extract_email_domain("invalid") is None

    def test_uppercase_normalized(self):
        assert extract_email_domain("test@BROKER.COM") == "broker.com"


# ---------------------------------------------------------------------------
# extract_broker_from_domain tests
# ---------------------------------------------------------------------------

class TestExtractBrokerFromDomain:

    def test_plain_domain(self):
        assert extract_broker_from_domain("spokeo.com") == "spokeo.com"

    def test_strips_www(self):
        assert extract_broker_from_domain("www.spokeo.com") == "spokeo.com"

    def test_strips_mail_subdomain(self):
        assert extract_broker_from_domain("mail.spokeo.com") == "spokeo.com"

    def test_none_input(self):
        assert extract_broker_from_domain(None) is None


# ---------------------------------------------------------------------------
# Header extraction tests
# ---------------------------------------------------------------------------

class TestExtractHeaders:

    def test_extract_message_id(self):
        headers = {"Message-ID": "<msg-123@example.com>"}
        assert extract_message_id(headers) == "msg-123@example.com"

    def test_extract_message_id_no_brackets(self):
        headers = {"message-id": "msg-456"}
        assert extract_message_id(headers) == "msg-456"

    def test_extract_in_reply_to(self):
        headers = {"In-Reply-To": "<reply-789>"}
        assert extract_in_reply_to(headers) == "reply-789"

    def test_extract_references(self):
        headers = {"References": "<ref1> <ref2>"}
        refs = extract_references(headers)
        assert "ref1" in refs
        assert "ref2" in refs

    def test_extract_references_empty(self):
        assert extract_references({}) == []


# ---------------------------------------------------------------------------
# match_by_message_id tests
# ---------------------------------------------------------------------------

class TestMatchByMessageId:

    def test_match_found(self, sample_request):
        result = match_by_message_id([sample_request], "test-message-123")
        assert result["id"] == 1

    def test_no_match(self, sample_request):
        result = match_by_message_id([sample_request], "nonexistent")
        assert result is None


# ---------------------------------------------------------------------------
# match_by_broker_and_user tests
# ---------------------------------------------------------------------------

class TestMatchByBrokerAndUser:

    def test_single_match(self, sample_request):
        matches = match_by_broker_and_user([sample_request], 42, "spokeo.com")
        assert len(matches) == 1
        assert matches[0]["id"] == 1

    def test_wrong_user(self, sample_request):
        matches = match_by_broker_and_user([sample_request], 99, "spokeo.com")
        assert len(matches) == 0

    def test_wrong_domain(self, sample_request):
        matches = match_by_broker_and_user([sample_request], 42, "whitepages.com")
        assert len(matches) == 0

    def test_completed_request_excluded(self, sample_request):
        sample_request["status"] = "completed"
        matches = match_by_broker_and_user([sample_request], 42, "spokeo.com")
        assert len(matches) == 0

    def test_old_request_excluded(self, sample_request):
        sample_request["created_at"] = datetime.now(timezone.utc) - timedelta(days=10)
        matches = match_by_broker_and_user([sample_request], 42, "spokeo.com")
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# match_by_url_in_response tests
# ---------------------------------------------------------------------------

class TestMatchByUrlInResponse:

    def test_match_found(self, sample_request):
        result = match_by_url_in_response(
            [sample_request], 42, "https://spokeo.com/profile/12345"
        )
        assert result["id"] == 1

    def test_no_match(self, sample_request):
        result = match_by_url_in_response(
            [sample_request], 42, "https://other.com/page"
        )
        assert result is None


# ---------------------------------------------------------------------------
# match_by_temporal_proximity tests
# ---------------------------------------------------------------------------

class TestMatchByTemporalProximity:

    def test_match_within_window(self, sample_request):
        now = datetime.now(timezone.utc)
        matches = match_by_temporal_proximity(
            [sample_request], 42, "spokeo.com", now
        )
        assert len(matches) == 1

    def test_no_match_outside_window(self, sample_request):
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        matches = match_by_temporal_proximity(
            [sample_request], 42, "spokeo.com", old_time
        )
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# correlate_email_to_request tests
# ---------------------------------------------------------------------------

class TestCorrelateEmailToRequest:

    def test_no_match_unknown_domain(self, sample_request):
        result = correlate_email_to_request(
            pending_requests=[sample_request],
            user_id=42,
            email_from="unknown@randomsite.com",
            email_headers={},
            email_body="",
        )
        assert result["match"] is False

    def test_match_by_broker_and_user(self, sample_request):
        now = datetime.now(timezone.utc)
        result = correlate_email_to_request(
            pending_requests=[sample_request],
            user_id=42,
            email_from="noreply@spokeo.com",
            email_headers={},
            email_body="",
            email_timestamp=now,
        )
        assert result["match"] is True
        assert result["strategy"] == "broker_and_user"

    def test_no_match_wrong_user(self, sample_request):
        result = correlate_email_to_request(
            pending_requests=[sample_request],
            user_id=99,
            email_from="noreply@spokeo.com",
            email_headers={},
            email_body="",
        )
        assert result["match"] is False

    def test_message_id_strategy(self, sample_request):
        result = correlate_email_to_request(
            pending_requests=[sample_request],
            user_id=42,
            email_from="test@spokeo.com",
            email_headers={"Message-ID": "<test-message-123>"},
            email_body="",
        )
        assert result["match"] is True
        assert result["strategy"] == "message_id"
        assert result["confidence"] >= 0.9


# ---------------------------------------------------------------------------
# update_request_with_response tests
# ---------------------------------------------------------------------------

class TestUpdateRequestWithResponse:

    def test_update_dict_request(self, sample_request):
        correlation = {
            "strategy": "broker_and_user",
            "confidence": 0.75,
        }
        email_data = {
            "message_id": "resp-123",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        result = update_request_with_response(sample_request, correlation, email_data)
        assert result["request_id"] == 1
        assert result["correlated"] is True
        assert result["strategy"] == "broker_and_user"

    def test_metadata_updated(self, sample_request):
        correlation = {"strategy": "message_id", "confidence": 0.95}
        email_data = {"message_id": "resp-456"}
        update_request_with_response(sample_request, correlation, email_data)
        metadata = sample_request["metadata"]
        assert "correlated_at" in metadata
        assert metadata["correlation_strategy"] == "message_id"