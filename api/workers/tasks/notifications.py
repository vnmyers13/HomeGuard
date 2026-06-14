# ---------------------------------------------------------------------------
# Notification Tasks — Email/push notifications for user events
# ---------------------------------------------------------------------------
# Sends notifications when scans complete, removals are confirmed, etc.
#
# Tasks:
#   - send_scan_complete_notification  (called from scan orchestration)
#   - send_removal_confirmation  (called after verification scan passes)
#   - send_daily_digest  (scheduled, daily at 8am)
# ---------------------------------------------------------------------------

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from api.database import get_async_session
    from api.models.auth import User
    from api.models.scanning import ScanRun
    from api.models.requests import RemovalRequest
except ImportError:
    from database import get_async_session
    from models.auth import User
    from models.scanning import ScanRun
    from models.requests import RemovalRequest

# Aliases for test compatibility
get_db_session = get_async_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email rendering helpers
# ---------------------------------------------------------------------------

def _render_scan_complete_email(user: dict, scan_run: dict) -> str:
    """Render HTML email for scan completion."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Scan Complete</title></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>OpenDataRemoval Scan Complete</h2>
<p>Hi {user.get('name', 'User')},</p>
<p>Your scan has completed successfully.</p>
<ul>
<li>Status: {scan_run.get('status', 'completed')}</li>
<li>Brokers Scanned: {scan_run.get('brokers_scanned', 0)}</li>
<li>Listings Found: {scan_run.get('listings_found', 0)}</li>
</ul>
<p>Log in to your dashboard to review results and initiate removals.</p>
<hr><small>OpenDataRemoval Privacy Protection</small>
</body></html>"""


def _render_removal_confirmation_email(user: dict, request: dict) -> str:
    """Render HTML email for removal confirmation."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Removal Confirmed</title></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>OpenDataRemoval Removal Confirmed</h2>
<p>Hi {user.get('name', 'User')},</p>
<p>Your listing has been successfully removed from {request.get('broker_name', 'this broker')}.</p>
<ul>
<li>Broker: {request.get('broker_name', 'N/A')}</li>
<li>Status: Confirmed Removed</li>
<li>Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}</li>
</ul>
<p>Your privacy protection is up to date.</p>
<hr><small>OpenDataRemoval Privacy Protection</small>
</body></html>"""


def _render_daily_digest_email(user: dict, stats: dict) -> str:
    """Render HTML email for daily digest."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Daily Digest</title></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>OpenDataRemoval Daily Digest</h2>
<p>Hi {user.get('name', 'User')},</p>
<p>Here is your daily privacy protection summary:</p>
<ul>
<li>Active Profiles: {stats.get('active_profiles', 0)}</li>
<li>Pending Removals: {stats.get('pending_removals', 0)}</li>
<li>Confirmed Removals: {stats.get('confirmed_removals', 0)}</li>
<li>Relistings Detected: {stats.get('relistings', 0)}</li>
</ul>
<p>Log in to your dashboard for full details.</p>
<hr><small>OpenDataRemoval Privacy Protection</small>
</body></html>"""


# ---------------------------------------------------------------------------
# SMTP sending helper
# ---------------------------------------------------------------------------

async def _send_email(to: str, subject: str, html_body: str) -> bool:
    """Send email via SMTP. Returns True on success."""
    import os
    smtp_host = os.environ.get("SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    from_email = os.environ.get("FROM_EMAIL", "noreply@opendataremoval.local")

    try:
        import aiosmtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(html_body, subtype="html")

        if smtp_user and smtp_password:
            await aiosmtplib.send(msg, hostname=smtp_host, port=smtp_port,
                                  username=smtp_user, password=smtp_password,
                                  start_tls=True)
        else:
            await aiosmtplib.send(msg, hostname=smtp_host, port=smtp_port)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


# ---------------------------------------------------------------------------
# send_scan_complete_notification
# ---------------------------------------------------------------------------

def send_scan_complete_notification(user_id: str, scan_run_id: str):
    """Send notification when a scan completes."""
    logger.info("send_scan_complete_notification: user=%s scan=%s", user_id, scan_run_id)

    async def _run():
        async with get_async_session() as session:
            user = await session.get(User, user_id)
            if not user or not user.email:
                return {"status": "skipped", "reason": "no_email"}

            scan = await session.get(ScanRun, scan_run_id)
            if not scan:
                return {"status": "skipped", "reason": "scan_not_found"}

            scan_data = {
                "status": scan.status,
                "brokers_scanned": 0,
                "listings_found": 0,
            }

        email_data = _render_scan_complete_email(
            {"name": user.name or "User"}, scan_data
        )
        sent = await _send_email(
            user.email, "OpenDataRemoval: Scan Complete", email_data
        )
        return {"sent": sent}

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("send_scan_complete_notification failed: %s", e)
        return {"status": "failed", "error": str(e)}


# ---------------------------------------------------------------------------
# send_removal_confirmation
# ---------------------------------------------------------------------------

def send_removal_confirmation(user_id: str, request_id: str):
    """Send notification when a removal is verified."""
    logger.info("send_removal_confirmation: user=%s request=%s", user_id, request_id)

    async def _run():
        async with get_async_session() as session:
            user = await session.get(User, user_id)
            if not user or not user.email:
                return {"status": "skipped", "reason": "no_email"}

            req = await session.get(RemovalRequest, request_id)
            if not req:
                return {"status": "skipped", "reason": "request_not_found"}

            req_data = {
                "broker_name": "this broker",
                "status": "Confirmed Removed",
            }

        email_data = _render_removal_confirmation_email(
            {"name": user.name or "User"}, req_data
        )
        sent = await _send_email(
            user.email, "OpenDataRemoval: Removal Confirmed", email_data
        )
        return {"sent": sent}

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("send_removal_confirmation failed: %s", e)
        return {"status": "failed", "error": str(e)}


# ---------------------------------------------------------------------------
# send_daily_digest — scheduled daily summary
# ---------------------------------------------------------------------------

def send_daily_digest():
    """Send daily digest to all active users."""
    logger.info("send_daily_digest started")

    async def _run():
        async with get_async_session() as session:
            users = (await session.execute(
                select(User).where(User.is_active == True)
            )).scalars().all()

            sent_count = 0
            for user in users:
                if not user.email:
                    continue

                # Calculate stats for this user
                from sqlalchemy import func
                pending = (await session.execute(
                    select(func.count()).select_from(RemovalRequest).where(
                        RemovalRequest.user_id == user.id,
                        RemovalRequest.status == "pending",
                    )
                )).scalar_one()

                confirmed = (await session.execute(
                    select(func.count()).select_from(RemovalRequest).where(
                        RemovalRequest.user_id == user.id,
                        RemovalRequest.status.in_(["verified_removed", "completed"]),
                    )
                )).scalar_one()

                stats = {
                    "active_profiles": 0,
                    "pending_removals": pending,
                    "confirmed_removals": confirmed,
                    "relistings": 0,
                }

                email_data = _render_daily_digest_email(
                    {"name": user.name or "User"}, stats
                )
                sent = await _send_email(
                    user.email, "OpenDataRemoval Daily Digest", email_data
                )
                if sent:
                    sent_count += 1

            return {"sent": sent_count, "total_users": len(users)}

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("send_daily_digest failed: %s", e)
        return {"status": "failed", "error": str(e)}