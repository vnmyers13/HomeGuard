"""Email templates for notification delivery."""

from templates.removal_confirmed import REMOVAL_CONFIRMED_TEMPLATE
from templates.scan_complete import SCAN_COMPLETE_TEMPLATE
from templates.removal_pending import REMOVAL_PENDING_TEMPLATE
from templates.error_alert import ERROR_ALERT_TEMPLATE

TEMPLATES = {
    "removal_confirmed": REMOVAL_CONFIRMED_TEMPLATE,
    "scan_complete": SCAN_COMPLETE_TEMPLATE,
    "removal_pending": REMOVAL_PENDING_TEMPLATE,
    "error_alert": ERROR_ALERT_TEMPLATE,
}


def get_template(name: str) -> dict:
    """Get an email template by name."""
    return TEMPLATES.get(name)