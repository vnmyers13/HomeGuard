# ---------------------------------------------------------------------------
# Request Matcher — Correlate incoming emails with removal requests
# ---------------------------------------------------------------------------
# Matches incoming broker response emails to pending RemovalRequest records.
# Uses multiple matching strategies: email thread IDs, URL extraction, domain
# matching, and temporal proximity.
# ---------------------------------------------------------------------------

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email header extractors
# ---------------------------------------------------------------------------

def extract_message_id(headers: dict) -> Optional[str]:
    """Extract Message-ID from email headers."""
    msg_id = headers.get("Message-ID", "") or headers.get("message-id", "")
    if msg_id:
        # Strip angle brackets
        return msg_id.strip("<>")
    return None


def extract_in_reply_to(headers: dict) -> Optional[str]:
    """Extract In-Reply-To header."""
    in_reply = headers.get("In-Reply-To", "") or headers.get("in-reply-to", "")
    if in_reply:
        return in_reply.strip("<>")
    return None


def extract_references(headers):
    """Extract References header (space-separated Message-IDs)."""
    refs = headers.get("References", "") or headers.get("references", "")
    if not refs:
        return []
    return [ref.strip("<>").strip() for ref in refs.replace(">", " ").split() if ref]


def extract_broker_from_domain(domain):
    """Normalize broker domain for matching."""
    if not domain:
        return None
    # Strip www. and common subdomains
    normalized = re.sub(r'^(www\.|mail\.)', '', domain.lower())
    return normalized


# ---------------------------------------------------------------------------
# Matching strategies (offline — no DB dependency)
# ---------------------------------------------------------------------------

def match_by_message_id(requests, message_id):
    """Match a removal request by stored Message-ID in metadata (offline)."""
    for req in requests:
        meta = req.get("metadata", {}) if isinstance(req, dict) else (req.metadata or {})
        if message_id in str(meta):
            return req
    return None


def match_by_broker_and_user(requests, user_id, broker_domain, since=None):
    """Match removal requests by broker domain and user (offline)."""
    if since is None:
        since = datetime.now(timezone.utc) - timedelta(days=7)

    matches = []
    for req in requests:
        req_user_id = req.get("user_id") if isinstance(req, dict) else req.user_id
        req_domain = req.get("broker_domain", "").lower() if isinstance(req, dict) else (req.broker_domain or "").lower()
        req_status = req.get("status", "") if isinstance(req, dict) else (req.status or "")
        req_created = req.get("created_at") if isinstance(req, dict) else req.created_at

        if req_user_id != user_id:
            continue
        if broker_domain.lower() not in req_domain:
            continue
        if req_status not in ("submitted", "pending"):
            continue
        if req_created and req_created < since:
            continue

        matches.append(req)

    return matches


def match_by_url_in_response(requests, user_id, response_url):
    """Match a removal request by URL found in the broker response (offline)."""
    for req in requests:
        req_user_id = req.get("user_id") if isinstance(req, dict) else req.user_id
        if req_user_id != user_id:
            continue
        meta = req.get("metadata", {}) if isinstance(req, dict) else (req.metadata or {})
        if response_url in str(meta):
            return req
    return None


def match_by_temporal_proximity(requests, user_id, broker_domain, email_timestamp, window_hours=48):
    """Match removal requests submitted within a time window of the email (offline)."""
    since = email_timestamp - timedelta(hours=window_hours)
    until = email_timestamp + timedelta(hours=1)

    matches = []
    for req in requests:
        req_user_id = req.get("user_id") if isinstance(req, dict) else req.user_id
        req_domain = req.get("broker_domain", "").lower() if isinstance(req, dict) else (req.broker_domain or "").lower()
        req_status = req.get("status", "") if isinstance(req, dict) else (req.status or "")
        req_created = req.get("created_at") if isinstance(req, dict) else req.created_at

        if req_user_id != user_id:
            continue
        if broker_domain.lower() not in req_domain:
            continue
        if req_status not in ("submitted", "pending"):
            continue
        if not req_created or req_created < since or req_created > until:
            continue

        matches.append(req)

    return matches


# ---------------------------------------------------------------------------
# Main matching function
# ---------------------------------------------------------------------------

def correlate_email_to_request(
    pending_requests,
    user_id,
    email_from,
    email_headers,
    email_body,
    email_timestamp = None,
):
    """Correlate an incoming email to a pending removal request.

    Args:
        pending_requests: List of removal request dicts/objects for the user
        user_id: The user who received the email
        email_from: Sender email address
        email_headers: Full email headers dict
        email_body: Email body content (HTML or text)
        email_timestamp: When the email was received

    Returns:
        Dict with 'match', 'confidence', 'strategy', and 'request_id' keys.
    """
    if email_timestamp is None:
        email_timestamp = datetime.now(timezone.utc)

    # Extract broker domain from sender
    email_domain = extract_email_domain(email_from)
    broker_domain = extract_broker_from_domain(email_domain)

    if not broker_domain:
        return {
            "match": False,
            "confidence": 0.0,
            "strategy": None,
            "request_id": None,
            "reason": "could_not_extract_broker_domain",
        }

    # Strategy 1: Message-ID matching (highest confidence)
    message_id = extract_message_id(email_headers)
    if message_id:
        req = match_by_message_id(pending_requests, message_id)
        if req:
            req_id = req.get("id") if isinstance(req, dict) else req.id
            return {
                "match": True,
                "confidence": 0.95,
                "strategy": "message_id",
                "request_id": req_id,
            }

    # Strategy 2: URL in response body matching
    urls_in_body = re.findall(r'https?://[^\s<>"\')\]}]+', email_body)
    for url in urls_in_body:
        req = match_by_url_in_response(pending_requests, user_id, url)
        if req:
            req_id = req.get("id") if isinstance(req, dict) else req.id
            return {
                "match": True,
                "confidence": 0.9,
                "strategy": "url_in_response",
                "request_id": req_id,
            }

    # Strategy 3: Broker + user matching
    requests = match_by_broker_and_user(pending_requests, user_id, broker_domain)
    if requests:
        # If only one match, high confidence
        if len(requests) == 1:
            req_id = requests[0].get("id") if isinstance(requests[0], dict) else requests[0].id
            return {
                "match": True,
                "confidence": 0.75,
                "strategy": "broker_and_user",
                "request_id": req_id,
            }
        # Multiple matches - try temporal proximity to narrow down
        temporal = match_by_temporal_proximity(
            pending_requests, user_id, broker_domain, email_timestamp
        )
        if len(temporal) == 1:
            req_id = temporal[0].get("id") if isinstance(temporal[0], dict) else temporal[0].id
            return {
                "match": True,
                "confidence": 0.85,
                "strategy": "temporal_proximity",
                "request_id": req_id,
            }
        elif len(temporal) > 1:
            req_id = temporal[0].get("id") if isinstance(temporal[0], dict) else temporal[0].id
            return {
                "match": True,
                "confidence": 0.65,
                "strategy": "temporal_proximity",
                "request_id": req_id,
            }
        # Fall back to most recent broker+user match
        req_id = requests[0].get("id") if isinstance(requests[0], dict) else requests[0].id
        return {
            "match": True,
            "confidence": 0.5,
            "strategy": "broker_and_user",
            "request_id": req_id,
        }

    # No match found
    return {
        "match": False,
        "confidence": 0.0,
        "strategy": None,
        "request_id": None,
        "reason": "no_pending_request_for_broker",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_email_domain(email_address):
    """Extract domain from email address."""
    if not email_address or "@" not in email_address:
        return None
    return email_address.split("@", 1)[1].lower()


def update_request_with_response(request, correlation_result, email_data):
    """Update a RemovalRequest with correlation data.

    Args:
        request: The RemovalRequest model instance or dict
        correlation_result: Result from correlate_email_to_request
        email_data: Dict with email metadata (message_id, timestamp, etc.)

    Returns:
        Updated request data dict.
    """
    if isinstance(request, dict):
        metadata = request.get("metadata", {})
    else:
        metadata = getattr(request, 'metadata_', None) or {}

    # Store correlation info
    metadata["correlated_at"] = datetime.now(timezone.utc).isoformat()
    metadata["correlation_strategy"] = correlation_result.get("strategy")
    metadata["correlation_confidence"] = correlation_result.get("confidence")

    if email_data:
        metadata["response_message_id"] = email_data.get("message_id")
        metadata["response_timestamp"] = email_data.get("timestamp")

    if isinstance(request, dict):
        request["metadata"] = metadata
    else:
        request.metadata_ = metadata

    req_id = request.get("id") if isinstance(request, dict) else getattr(request, 'id', None)

    return {
        "request_id": req_id,
        "correlated": True,
        "strategy": correlation_result.get("strategy"),
        "confidence": correlation_result.get("confidence"),
    }