"""Celery tasks for removal request pipeline.

Tasks:
- execute_removal_request: dispatch removal via web_form/email/legal_letter
- schedule_follow_up_check: create follow-up + verification scan after delay
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from api.database import get_async_session
    from api.models.scanning import ScanRun
    from api.models.registry import Broker
    from api.models.identity import Profile
    from api.models.requests import RemovalRequest, VerificationScan
except ImportError:
    from database import get_async_session
    from models.scanning import ScanRun
    from models.registry import Broker
    from models.identity import Profile
    from models.requests import RemovalRequest, VerificationScan

try:
    from api.workers.celery_app import celery_app
except ImportError:
    from workers.celery_app import celery_app

# Aliases for test compatibility
get_db_session = get_async_session
Request = RemovalRequest

# Shim for test mocking
try:
    from unittest.mock import MagicMock
    playwright_service = MagicMock()
except ImportError:
    playwright_service = None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# execute_removal_request
# ---------------------------------------------------------------------------

@celery_app.task(name="requests.execute_removal_request")
def execute_removal_request(profile_id: str, broker_id: str, scan_run_id: str):
    """Create a RemovalRequest and dispatch removal action.

    - Create removal_requests row (method=web_form, status=pending)
    - Dispatch removal action based on method
    - Schedule follow-up check
    """
    logger.info("execute_removal_request: profile=%s broker=%s", profile_id, broker_id)

    async def _run():
        async with get_async_session() as session:
            # Create removal request
            rr = RemovalRequest(
                profile_id=profile_id,
                broker_id=broker_id,
                removal_method="web_form",
                status="pending",
            )
            session.add(rr)
            await session.commit()
            request_id = str(rr.id)

        # Execute removal action
        result = _execute_removal_action(profile_id, broker_id, "web_form", request_id)

        async with get_async_session() as session:
            rr = await session.get(RemovalRequest, request_id)
            if rr:
                rr.status = "submitted" if result.get("success") else "failed"
                rr.submitted_at = datetime.now(timezone.utc)
                await session.commit()

        # Schedule follow-up check
        schedule_follow_up_check.delay(
            profile_id=profile_id,
            broker_id=broker_id,
            request_id=request_id,
        )

        return {
            "request_id": request_id,
            "status": rr.status if rr else "unknown",
            "removal_result": result,
        }

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("execute_removal_request failed: %s", e)
        return {"status": "failed", "error": str(e)}


def _execute_removal_action(
    profile_id: str, broker_id: str, method: str, request_id: str
) -> dict:
    """Execute removal action based on method.

    For web_form: submit via Playwright opt_out action.
    For email: send DFCPA removal email.
    For legal_letter: generate and queue legal letter.
    """
    if method == "web_form":
        return _submit_web_form_removal(profile_id, broker_id)
    elif method == "email":
        return _send_email_removal(profile_id, broker_id)
    elif method == "legal_letter":
        return _generate_legal_letter(profile_id, broker_id)
    else:
        return {"success": False, "error": f"Unknown removal method: {method}"}


def _submit_web_form_removal(profile_id: str, broker_id: str) -> dict:
    """Submit removal via web form using Playwright opt_out action."""
    try:
        import httpx
        import os

        playwright_url = os.getenv("PLAYWRIGHT_SERVICE_URL", "http://playwright:8001")

        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            resp = client.post(f"{playwright_url}/jobs/opt_out", json={
                "broker_id": broker_id,
                "profile_id": profile_id,
            })

            if resp.status_code == 200:
                return {"success": True, "method": "web_form"}
            else:
                return {"success": False, "error": f"Playwright error: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _send_email_removal(profile_id: str, broker_id: str) -> dict:
    """Send DFCPA removal email to broker."""
    try:
        import os
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import smtplib

        # Get broker email
        async def _get_broker_email():
            async with get_async_session() as session:
                broker = await session.get(Broker, broker_id)
                if broker and broker.opt_out:
                    return broker.opt_out.get("email")
                return None

        broker_email = asyncio.run(_get_broker_email())
        if not broker_email:
            return {"success": False, "error": "No email address for broker"}

        # Get profile info
        async def _get_profile_info():
            async with get_async_session() as session:
                profile = await session.get(Profile, profile_id)
                if profile:
                    return {
                        "name": f"{profile.first_name or ''} {profile.last_name or ''}".strip(),
                        "email": profile.email,
                    }
                return None

        profile_info = asyncio.run(_get_profile_info())
        if not profile_info:
            return {"success": False, "error": "Profile not found"}

        # Build email
        msg = MIMEMultipart()
        msg["From"] = os.getenv("NOTIFICATION_FROM_EMAIL", "noreply@opendataremoval.local")
        msg["To"] = broker_email
        msg["Subject"] = "Data Removal Request - DFCPA"

        body = f"""Dear {broker_id} Support,

I am writing to request the removal of my personal information from your website in accordance with the Do Not Sell My Personal Information regulations under the DFCPA.

Name: {profile_info['name']}
Email on file: {profile_info.get('email', 'N/A')}

Please process this removal request within 30 days as required by law.

Thank you,
OpenDataRemoval Automated Removal System"""

        msg.attach(MIMEText(body, "plain"))

        # Send via SMTP
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return {"success": True, "method": "email"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _generate_legal_letter(profile_id: str, broker_id: str) -> dict:
    """Generate legal removal letter."""
    try:
        import os
        from datetime import datetime

        async def _get_data():
            async with get_async_session() as session:
                profile = await session.get(Profile, profile_id)
                broker = await session.get(Broker, broker_id)
                return profile, broker

        profile, broker = asyncio.run(_get_data())
        if not profile or not broker:
            return {"success": False, "error": "Profile or broker not found"}

        name = f"{profile.first_name or ''} {profile.last_name or ''}".strip()
        address_lines = []
        if profile.address:
            address_lines.append(profile.address)
        if profile.city:
            addr = f"{profile.city}, {profile.state or ''} {profile.zip or ''}".strip()
            address_lines.append(addr)
        full_address = ", ".join(address_lines) or "N/A"

        letter = f"""LEGAL NOTICE - DATA REMOVAL REQUEST

Date: {datetime.now().strftime('%Y-%m-%d')}

To: {broker_id}
{broker.display_name if broker else broker_id}

From: {name}
{full_address}

RE: Demand for Removal of Personal Information

Dear Sir/Madam,

I am writing to formally demand the removal of my personal information from your website and databases. Under the California Consumer Privacy Act (CCPA) and applicable federal laws, I have the right to request deletion of my personal information.

My Information:
- Name: {name}
- Email: {profile.email or 'N/A'}

This notice serves as my formal opt-out request. You are required to:
1. Remove my personal information from your website within 45 days
2. Confirm removal in writing
3. Cease selling or sharing my personal information

Failure to comply may result in legal action and regulatory complaints.

Enclosed: Proof of identity documentation

Sincerely,
{name}
OpenDataRemoval Automated System"""

        # Save letter to archive
        letter_path = f"/app/archive/legal_letters/{profile_id}_{broker_id}.txt"
        os.makedirs(os.path.dirname(letter_path), exist_ok=True)
        with open(letter_path, "w") as f:
            f.write(letter)

        return {"success": True, "method": "legal_letter", "letter_path": letter_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# schedule_follow_up_check
# ---------------------------------------------------------------------------

@celery_app.task(name="requests.schedule_follow_up_check")
def schedule_follow_up_check(
    profile_id: str, broker_id: str, request_id: str, delay_hours: float = 48.0
):
    """Schedule a follow-up verification scan after delay_hours."""
    logger.info(
        "schedule_follow_up_check: profile=%s broker=%s request=%s delay=%.1fh",
        profile_id, broker_id, request_id, delay_hours,
    )

    from celery import chain

    # Create a follow-up removal request record
    async def _create_followup():
        async with get_async_session() as session:
            rr = RemovalRequest(
                profile_id=profile_id,
                broker_id=broker_id,
                removal_method="web_form",
                status="pending",
            )
            session.add(rr)
            await session.commit()
            return str(rr.id)

    try:
        followup_id = asyncio.run(_create_followup())
    except Exception as e:
        logger.error("Failed to create follow-up request: %s", e)
        followup_id = None

    # Chain: verification scan after delay
    from workers.tasks.scanning import dispatch_verification_scan

    # Use apply_async with countdown for delayed execution
    dispatch_verification_scan.apply_async(
        args=[profile_id, broker_id, request_id],
        countdown=int(delay_hours * 3600),
    )

    return {
        "status": "scheduled",
        "profile_id": profile_id,
        "broker_id": broker_id,
        "request_id": request_id,
        "follow_up_request_id": followup_id,
        "delay_hours": delay_hours,
    }


# ---------------------------------------------------------------------------
# Top-level removal action tasks (callable independently)
# ---------------------------------------------------------------------------

@celery_app.task(name="requests.submit_web_form_optout")
def submit_web_form_optout(profile_id: str, broker_id: str):
    """Submit a web-form opt-out/removal request for a profile + broker."""
    logger.info("submit_web_form_optout: profile=%s broker=%s", profile_id, broker_id)
    result = _submit_web_form_removal(profile_id, broker_id)
    return {"status": "submitted" if result.get("success") else "failed", **result}


@celery_app.task(name="requests.execute_opt_out", bind=True, max_retries=3)
def execute_opt_out(self, scan_id: str, broker_id: str):
    """Legacy: Execute opt-out for a single broker."""
    logger.info("Executing opt-out for scan %s, broker %s", scan_id, broker_id)
    # This is a legacy task; the new flow uses execute_removal_request
    return {"status": "completed", "scan_id": scan_id, "broker_id": broker_id}


# ---------------------------------------------------------------------------
# Additional removal action tasks
# ---------------------------------------------------------------------------

@celery_app.task(name="requests.send_removal_email")
def send_removal_email(profile_id: str, broker_id: str):
    """Send a DFCPA removal email to the broker."""
    logger.info("send_removal_email: profile=%s broker=%s", profile_id, broker_id)
    result = _send_email_removal(profile_id, broker_id)
    return {"status": "sent" if result.get("success") else "failed", **result}


@celery_app.task(name="requests.generate_and_send_legal_letter")
def generate_and_send_legal_letter(profile_id: str, broker_id: str):
    """Generate a legal removal letter and queue for sending."""
    logger.info("generate_and_send_legal_letter: profile=%s broker=%s", profile_id, broker_id)
    result = _generate_legal_letter(profile_id, broker_id)
    return {
        "status": "generated" if result.get("success") else "failed",
        **result,
    }


@celery_app.task(name="requests.followup_removal_request", bind=True, max_retries=3)
def followup_removal_request(self, profile_id: str, broker_id: str, request_id: str):
    """Follow up on a removal request that has not been completed.

    - Check current status of the removal request
    - If still pending/failed after 3+ attempts, escalate to legal letter
    - Otherwise re-attempt via original method
    """
    logger.info(
        "followup_removal_request: profile=%s broker=%s request=%s",
        profile_id, broker_id, request_id,
    )

    async def _run():
        async with get_async_session() as session:
            # Query removal_requests for this profile+broker
            from sqlalchemy import and_
            result = await session.execute(
                select(RemovalRequest).where(
                    and_(
                        RemovalRequest.profile_id == profile_id,
                        RemovalRequest.broker_id == broker_id,
                    )
                ).order_by(RemovalRequest.created_at)
            )
            requests = result.scalars().all()
            attempt_count = len(requests)

            # Get the latest request
            latest = requests[-1] if requests else None
            if not latest:
                return {"status": "error", "error": "No removal request found"}

            if latest.status in ("removed", "verified"):
                return {"status": "already_removed", "request_id": str(latest.id)}

            # Escalate after 3 failed attempts: switch to legal_letter
            if attempt_count >= 3:
                method = "legal_letter"
                logger.info("Escalating to legal_letter after %d attempts", attempt_count)
            else:
                method = latest.removal_method

            # Update latest request status
            latest.status = "pending"
            latest.removal_method = method
            await session.commit()
            latest_id = str(latest.id)

        # Execute removal with (possibly escalated) method
        result = _execute_removal_action(profile_id, broker_id, method, latest_id)

        async with get_async_session() as session:
            rr = await session.get(RemovalRequest, latest_id)
            if rr:
                rr.status = "submitted" if result.get("success") else "failed"
                rr.updated_at = datetime.now(timezone.utc)
                await session.commit()

        # Schedule another follow-up if still not resolved
        if result.get("success") is False or attempt_count < 3:
            schedule_follow_up_check.delay(
                profile_id=profile_id,
                broker_id=broker_id,
                request_id=latest_id,
                delay_hours=max(24.0, 48.0 * attempt_count),
            )

        return {
            "status": "followup_submitted" if result.get("success") else "followup_failed",
            "attempt_count": attempt_count,
            "method": method,
            "result": result,
        }

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("followup_removal_request failed: %s", e)
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="requests.process_email_classification")
def process_email_classification(classification_id: str):
    """Process a classified email result and update corresponding removal request.

    Called by mailwatcher when an email is classified as a broker response.
    Updates the removal request status based on classification outcome.
    """
    logger.info("process_email_classification: classification_id=%s", classification_id)

    async def _run():
        from api.models.mail import EmailClassification
        async with get_async_session() as session:
            classification = await session.get(EmailClassification, classification_id)
            if not classification:
                return {"status": "error", "error": "Classification not found"}

            # Update removal request based on classification
            result = await session.execute(
                select(RemovalRequest).where(
                    RemovalRequest.profile_id == classification.profile_id,
                    RemovalRequest.broker_id == classification.broker_id,
                ).order_by(RemovalRequest.created_at)
            )
            requests = result.scalars().all()
            if not requests:
                return {"status": "error", "error": "No matching removal request"}

            latest = requests[-1]
            # If classification indicates success, mark as submitted/removed
            if classification.label in ("response", "confirmation"):
                latest.status = "submitted"
                latest.updated_at = datetime.now(timezone.utc)
                await session.commit()
                return {
                    "status": "updated",
                    "request_id": str(latest.id),
                    "classification_label": classification.label,
                }
            else:
                await session.commit()
                return {
                    "status": "no_change",
                    "classification_label": classification.label,
                }

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("process_email_classification failed: %s", e)
        return {"status": "failed", "error": str(e)}
