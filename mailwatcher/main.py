"""
Mailwatcher - Email Monitoring Service for OpenDataRemoval
Polls IMAP mailbox, classifies incoming emails, stores results,
and dispatches webhook notifications for billing/scanning events.
"""
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Mailwatcher modules
from imap_client import IMAPClient
from classifier import EmailClassifier, Classification
from repository import MailRepository
from notifier import WebhookDispatcher


class MailPoller:
    """Main polling loop that connects IMAP -> Classification -> Storage -> Notification."""

    def __init__(self, config: dict):
        self.config = config
        self.running = False

        # IMAP settings
        self.imap_host = config.get("IMAP_HOST", "imap.gmail.com")
        self.imap_port = config.get("IMAP_PORT", 993)
        self.imap_user = config.get("IMAP_USER", "")
        self.imap_password = config.get("IMAP_PASSWORD", "")

        # Polling settings
        self.poll_interval = config.get("POLL_INTERVAL_SEC", 30)
        self.max_messages_per_poll = config.get("MAX_MESSAGES_PER_POLL", 50)

        # API webhook settings
        self.api_base_url = config.get("API_BASE_URL", "http://localhost:8000")
        self.api_key = config.get("API_KEY", None)

        # Database DSN for repository
        self.db_dsn = config.get("DATABASE_URL", "postgresql://opendataremoval:opendataremoval@postgres:5432/opendataremoval")

        # Components
        self.imap_client: Optional[IMAPClient] = None
        self.classifier = EmailClassifier()
        self.repository: Optional[MailRepository] = None
        self.dispatcher: Optional[WebhookDispatcher] = None

    @staticmethod
    def _build_config_dict() -> dict:
        """Build configuration from environment variables."""
        return {
            "IMAP_HOST": os.getenv("MAILWATCHER_IMAP_HOST", "imap.gmail.com"),
            "IMAP_PORT": int(os.getenv("MAILWATCHER_IMAP_PORT", "993")),
            "IMAP_USER": os.getenv("MAILWATCHER_IMAP_USER", ""),
            "IMAP_PASSWORD": os.getenv("MAILWATCHER_IMAP_PASSWORD", ""),
            "POLL_INTERVAL_SEC": int(os.getenv("MAILWATCHER_POLL_INTERVAL_SEC", "30")),
            "MAX_MESSAGES_PER_POLL": int(os.getenv("MAILWATCHER_MAX_MESSAGES_PER_POLL", "50")),
            "API_BASE_URL": os.getenv("MAILWATCHER_API_URL", "http://localhost:8000"),
            "API_KEY": os.getenv("MAILWATCHER_API_KEY", None),
            "DATABASE_URL": os.getenv(
                "DATABASE_URL",
                "postgresql://opendataremoval:opendataremoval@postgres:5432/opendataremoval",
            ),
        }

    def connect(self):
        """Initialize all components."""
        logger.info("Connecting to IMAP: %s@%s:%d", self.imap_user, self.imap_host, self.imap_port)
        self.imap_client = IMAPClient(
            host=self.imap_host,
            port=self.imap_port,
            username=self.imap_user,
            password=self.imap_password,
        )
        self.imap_client.connect()

        logger.info("Connecting to database: %s", self.db_dsn)
        self.repository = MailRepository(dsn=self.db_dsn)

        logger.info("Webhook dispatcher target: %s", self.api_base_url)
        self.dispatcher = WebhookDispatcher(
            base_url=self.api_base_url,
            api_key=self.api_key,
        )

        logger.info("All components connected.")

    def disconnect(self):
        """Clean up all connections."""
        if self.dispatcher:
            self.dispatcher.close()
        logger.info("All components disconnected.")

    def process_message(self, msg_data: dict):
        """
        Process a single email message through the pipeline.

        Pipeline: classify -> store -> notify
        """
        msg_id = msg_data.get("message_id", "unknown")
        from_addr = msg_data.get("from", "")
        subject = msg_data.get("subject", "")

        # Step 1: Classify
        classification: Classification = self.classifier.classify(msg_data)
        logger.info(
            "Classified msg=%s from=%s class=%s confidence=%d",
            msg_id,
            from_addr,
            classification.category,
            classification.confidence,
        )

        # Step 2: Store in database
        try:
            self.repository.upsert_message(
                message_id=msg_data.get("message_id"),
                from_address=msg_data.get("from", ""),
                to_address=msg_data.get("to", ""),
                subject=msg_data.get("subject", ""),
                body_text=msg_data.get("body_text", ""),
                body_html=msg_data.get("body_html", ""),
                received_at=datetime.fromisoformat(msg_data["date"]) if msg_data.get("date") else None,
                classification=classification.category,
                confidence=classification.confidence,
                extracted_data=classification.extracted_data,
            )
        except Exception as e:
            logger.error("Failed to store message %s: %s", msg_id, e)

        # Step 3: Dispatch webhook notification for important classifications
        if classification.category in ("bill", "scan_result", "alert"):
            try:
                self.dispatcher.send_classification_notification(
                    message_id=msg_data.get("message_id", ""),
                    from_address=from_addr,
                    subject=subject,
                    classification=classification.category,
                    confidence=classification.confidence,
                    extracted_data=classification.extracted_data,
                )
            except Exception as e:
                logger.error("Failed to dispatch notification for %s: %s", msg_id, e)

    def poll_once(self) -> int:
        """Run a single polling cycle. Returns number of messages processed."""
        if not self.imap_client:
            logger.warning("IMAP client not connected, skipping poll.")
            return 0

        try:
            messages = self.imap_client.fetch_new(
                limit=self.max_messages_per_poll,
            )
        except Exception as e:
            logger.error("IMAP fetch failed: %s", e)
            # Attempt reconnection
            try:
                logger.info("Attempting IMAP reconnect...")
                self.imap_client.connect()
            except Exception:
                logger.error("IMAP reconnect failed.")
            return 0

        if not messages:
            logger.debug("No new messages this cycle.")
            return 0

        logger.info("Fetched %d new message(s).", len(messages))

        processed = 0
        for msg_data in messages:
            try:
                self.process_message(msg_data)
                processed += 1
            except Exception as e:
                logger.error("Error processing message %s: %s", msg_data.get("message_id"), e)

        logger.info("poll_completed - processed=%d", processed)
        return processed

    def run(self):
        """Main polling loop."""
        self.running = True
        logger.info("Mailwatcher starting up...")
        self.connect()
        logger.info("Mailwatcher ready - polling every %d seconds.", self.poll_interval)

        while self.running:
            self.poll_once()
            time.sleep(self.poll_interval)

    def stop(self):
        """Signal the poller to stop."""
        self.running = False


def main():
    """Entry point for the mailwatcher service."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = MailPoller._build_config_dict()
    poller = MailPoller(config)

    def _signal_handler(signum, frame):
        logger.info("Received signal %d, stopping...", signum)
        poller.stop()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        poller.run()
    finally:
        poller.disconnect()
        logger.info("Mailwatcher stopped.")


if __name__ == "__main__":
    main()