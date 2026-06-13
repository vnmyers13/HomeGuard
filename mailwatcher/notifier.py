"""
Webhook Notification Dispatch
Sends classification results to configured webhook endpoints.
"""
import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """Sends webhook notifications for classified emails."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        # Build session with retry logic
        self.session = requests.Session()
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
        self.session.headers["Content-Type"] = "application/json"

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def send_notification(
        self,
        event_type: str,
        payload: dict,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Send a webhook notification.

        Args:
            event_type: The type of event (e.g., 'mailwatcher.classification')
            payload: The notification payload data
            webhook_url: Optional specific webhook URL (overrides base_url)

        Returns:
            True if notification was sent successfully.
        """
        url = webhook_url or f"{self.base_url}/api/v1/webhooks/inbound"

        notification = {
            "event": event_type,
            "payload": payload,
        }

        try:
            response = self.session.post(
                url,
                json=notification,
                timeout=self.timeout,
            )

            if response.status_code in (200, 201, 202):
                logger.info(
                    "Webhook notification sent: event=%s status=%s",
                    event_type,
                    response.status_code,
                )
                return True
            else:
                logger.warning(
                    "Webhook notification failed: event=%s status=%s body=%s",
                    event_type,
                    response.status_code,
                    response.text[:500],
                )
                return False

        except requests.exceptions.Timeout:
            logger.error(
                "Webhook notification timed out: event=%s url=%s",
                event_type,
                url,
            )
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(
                "Webhook notification connection error: event=%s url=%s error=%s",
                event_type,
                url,
                e,
            )
            return False
        except Exception as e:
            logger.error(
                "Webhook notification unexpected error: event=%s error=%s",
                event_type,
                e,
            )
            return False

    def send_classification_notification(
        self,
        message_id: str,
        from_address: str,
        subject: str,
        classification: str,
        confidence: int,
        extracted_data: Optional[dict] = None,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """Send a notification for a classified email."""
        payload = {
            "message_id": message_id,
            "from_address": from_address,
            "subject": subject,
            "classification": classification,
            "confidence": confidence,
        }
        if extracted_data:
            payload["extracted_data"] = extracted_data

        return self.send_notification(
            event_type="mailwatcher.classification",
            payload=payload,
            webhook_url=webhook_url,
        )

    def send_error_notification(
        self,
        message_id: str,
        error: str,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """Send a notification for a processing error."""
        payload = {
            "message_id": message_id,
            "error": error,
        }

        return self.send_notification(
            event_type="mailwatcher.error",
            payload=payload,
            webhook_url=webhook_url,
        )

    def close(self):
        """Close the underlying session."""
        self.session.close()