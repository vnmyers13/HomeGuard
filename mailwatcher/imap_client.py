"""
IMAP Client Module
Handles IMAP SSL/TLS connection, authentication, and email fetching.
"""
import logging
import email
import email.policy
import imaplib
import re
import time
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import parseaddr
from typing import Optional

logger = logging.getLogger(__name__)


class IMAPClient:
    """IMAP client with SSL/TLS support for monitoring email inbox."""

    def __init__(
        self,
        host: str,
        port: int = 993,
        username: str = "",
        password: str = "",
        ssl: bool = True,
        mailbox: str = "INBOX",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self.mailbox = mailbox
        self._connection = None

    @property
    def is_configured(self) -> bool:
        """Check if all required credentials are set."""
        return bool(self.host and self.username and self.password)

    def connect(self):
        """Establish IMAP connection with SSL/TLS."""
        if self._connection is not None:
            return

        if not self.is_configured:
            raise ConnectionError("IMAP client is not configured")

        if self.ssl:
            self._connection = imaplib.IMAP4_SSL(
                self.host, self.port, ssl_context=None
            )
        else:
            self._connection = imaplib.IMAP4(self.host, self.port)
            self._connection.starttls()

        self._connection.login(self.username, self.password)
        logger.info("Connected to IMAP server: %s:%d", self.host, self.port)

    def disconnect(self):
        """Close IMAP connection gracefully."""
        if self._connection:
            try:
                self._connection.logout()
            except Exception:
                pass
            self._connection = None
            logger.info("Disconnected from IMAP server")

    def select_mailbox(self, mailbox: Optional[str] = None):
        """Select the target mailbox."""
        if not self._connection:
            self.connect()
        mbox = mailbox or self.mailbox
        status, _ = self._connection.select(mbox)
        if status != "OK":
            raise ConnectionError(f"Failed to select mailbox: {mbox}")
        logger.debug("Selected mailbox: %s", mbox)

    def fetch_unseen(self, limit: int = 50) -> list[bytes]:
        """Fetch unseen (UNSEEN flag) messages from the mailbox."""
        if not self._connection:
            self.connect()
        self.select_mailbox()

        status, msg_data = self._connection.search(None, "UNSEEN")
        if status != "OK":
            return []

        msg_ids = msg_data[0].split()
        if not msg_ids:
            return []

        # Limit to the most recent messages
        recent = msg_ids[-limit:]
        messages = []

        for mid in recent:
            status, data = self._connection.fetch(mid, "(RFC822)")
            if status == "OK" and data:
                messages.append(data[0][1])

        return messages

    def fetch_since(self, since: datetime, limit: int = 50) -> list[bytes]:
        """Fetch messages received since a specific datetime."""
        if not self._connection:
            self.connect()
        self.select_mailbox()

        # IMAP date format: DD-Mmm-YYYY
        date_str = since.strftime("%d-%b-%Y").lower()
        # Capitalize month abbreviation properly
        months = {
            "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr",
            "may": "May", "jun": "Jun", "jul": "Jul", "aug": "Aug",
            "sep": "Sep", "oct": "Oct", "nov": "Nov", "dec": "Dec",
        }
        parts = date_str.split("-")
        parts[1] = months.get(parts[1], parts[1])
        date_str = "-".join(parts)

        status, msg_data = self._connection.search(None, f'(SINCE "{date_str}")')
        if status != "OK":
            return []

        msg_ids = msg_data[0].split()
        if not msg_ids:
            return []

        recent = msg_ids[-limit:]
        messages = []

        for mid in recent:
            status, data = self._connection.fetch(mid, "(RFC822)")
            if status == "OK" and data:
                messages.append(data[0][1])

        return messages

    def mark_as_seen(self, msg_ids: list[bytes]):
        """Mark specified message IDs as seen."""
        if not self._connection or not msg_ids:
            return
        id_str = " ".join(mid.decode() for mid in msg_ids)
        self._connection.store(id_str, "+FLAGS", "\\Seen")
        logger.debug("Marked %d messages as seen", len(msg_ids))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()


def decode_mime_header(header_value: str) -> str:
    """Decode MIME-encoded header values."""
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            charset = charset or "utf-8"
            try:
                part = part.decode(charset)
            except (UnicodeDecodeError, LookupError):
                part = part.decode("utf-8", errors="replace")
        result.append(part)
    return "".join(result)


def parse_raw_email(raw_bytes: bytes) -> dict:
    """Parse raw email bytes into a structured dictionary."""
    msg = email.message_from_bytes(raw_bytes, policy=email.policy.default)

    # Decode headers
    subject = decode_mime_header(msg.get("Subject", ""))
    from_addr, from_name = parseaddr(msg.get("From", ""))
    to_addr, to_name = parseaddr(msg.get("To", ""))
    message_id = msg.get("Message-ID", "").strip("<>")
    date_str = msg.get("Date", "")

    # Parse body - handle multipart messages
    body_text = ""
    body_html = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            if content_type == "text/plain" and not body_text:
                body_text = _decode_part(part)
            elif content_type == "text/html" and not body_html:
                body_html = _decode_part(part)
    else:
        if msg.get_content_type() == "text/html":
            body_html = _decode_part(msg)
        else:
            body_text = _decode_part(msg)

    # Collect important headers as JSON-serializable dict
    headers = {}
    for key in ["Message-ID", "From", "To", "Subject", "Date", "Reply-To", "In-Reply-To", "References"]:
        val = msg.get(key)
        if val:
            headers[key] = decode_mime_header(val)

    return {
        "message_id_header": message_id or f"unknown-{int(time.time())}-{id(raw_bytes)}",
        "from_address": from_addr or "",
        "to_address": to_addr or "",
        "subject": subject,
        "body_text": body_text.strip() if body_text else "",
        "body_html": body_html.strip() if body_html else "",
        "headers": headers,
    }


def _decode_part(part) -> str:
    """Decode an email part's content."""
    charset = part.get_content_charset() or "utf-8"
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    try:
        return payload.decode(charset)
    except (UnicodeDecodeError, LookupError):
        return payload.decode("utf-8", errors="replace")