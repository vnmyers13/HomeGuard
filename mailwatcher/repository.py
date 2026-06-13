"""
Mail Database Repository
Repository layer for inbound messages and message classifications.
Provides CRUD operations over the mail schema tables.
"""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

try:
    from api.models.mail import InboundMessage, MessageClassification
except ImportError:
    from models.mail import InboundMessage, MessageClassification

logger = logging.getLogger(__name__)


class MailRepository:
    """Repository for inbound messages and classifications."""

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # InboundMessage operations
    # ------------------------------------------------------------------

    def get_unprocessed_messages(
        self, limit: int = 50, to_address: Optional[str] = None
    ) -> List[InboundMessage]:
        """Retrieve unprocessed inbound messages, optionally filtered by recipient."""
        query = select(InboundMessage).where(
            InboundMessage.processed == False
        )
        if to_address:
            query = query.where(InboundMessage.to_address == to_address)
        query = query.order_by(InboundMessage.received_at.asc()).limit(limit)

        results = self.session.execute(query).scalars().all()
        # Detach from session to avoid lazy-loading issues after commit
        for msg in results:
            self.session.expunge(msg)
        return results

    def get_message_by_id(self, message_id: UUID) -> Optional[InboundMessage]:
        """Retrieve a single inbound message by primary key."""
        msg = self.session.get(InboundMessage, message_id)
        if msg:
            self.session.expunge(msg)
        return msg

    def get_message_by_header_id(self, message_id_header: str) -> Optional[InboundMessage]:
        """Retrieve a message by its Message-ID header value."""
        result = self.session.execute(
            select(InboundMessage).where(
                InboundMessage.message_id_header == message_id_header
            )
        ).scalar_one_or_none()
        if result:
            self.session.expunge(result)
        return result

    def create_message(
        self,
        message_id_header: str,
        from_address: str,
        to_address: str,
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        headers: Optional[dict] = None,
    ) -> InboundMessage:
        """Insert a new inbound message. Returns the created object."""
        msg = InboundMessage(
            message_id_header=message_id_header,
            from_address=from_address,
            to_address=to_address,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            headers=headers,
        )
        self.session.add(msg)
        return msg

    def mark_processed(self, message_id: UUID) -> None:
        """Mark a message as processed."""
        self.session.execute(
            update(InboundMessage)
            .where(InboundMessage.id == message_id)
            .values(processed=True)
        )

    def delete_message(self, message_id: UUID) -> bool:
        """Delete a message and its classifications. Returns True if deleted."""
        msg = self.session.get(InboundMessage, message_id)
        if not msg:
            return False
        # Classifications are cascade-deleted via relationship, but do it explicitly for safety
        self.session.execute(
            delete(MessageClassification).where(
                MessageClassification.message_id == message_id
            )
        )
        self.session.delete(msg)
        return True

    # ------------------------------------------------------------------
    # MessageClassification operations
    # ------------------------------------------------------------------

    def create_classification(
        self,
        message_id: UUID,
        classification: str,
        confidence: int = 0,
        matched_pattern: Optional[str] = None,
        extracted_data: Optional[dict] = None,
        linked_request_id: Optional[UUID] = None,
    ) -> MessageClassification:
        """Insert a new classification record."""
        cls = MessageClassification(
            message_id=message_id,
            classification=classification,
            confidence=confidence,
            matched_pattern=matched_pattern,
            extracted_data=extracted_data,
            linked_request_id=linked_request_id,
        )
        self.session.add(cls)
        return cls

    def get_classifications_for_message(
        self, message_id: UUID
    ) -> List[MessageClassification]:
        """Retrieve all classifications for a given message."""
        results = self.session.execute(
            select(MessageClassification).where(
                MessageClassification.message_id == message_id
            )
        ).scalars().all()
        for c in results:
            self.session.expunge(c)
        return results

    def link_classification_to_request(
        self, classification_id: UUID, linked_request_id: UUID
    ) -> None:
        """Update a classification to link it to a removal request."""
        self.session.execute(
            update(MessageClassification)
            .where(MessageClassification.id == classification_id)
            .values(linked_request_id=linked_request_id)
        )

    def get_unlinked_classifications(
        self, classification: Optional[str] = None
    ) -> List[MessageClassification]:
        """Retrieve classifications that have not been linked to a request."""
        query = select(MessageClassification).where(
            MessageClassification.linked_request_id == None
        )
        if classification:
            query = query.where(MessageClassification.classification == classification)
        query = query.order_by(MessageClassification.created_at.asc())

        results = self.session.execute(query).scalars().all()
        for c in results:
            self.session.expunge(c)
        return results

    # ------------------------------------------------------------------
    # Bulk / utility operations
    # ------------------------------------------------------------------

    def count_unprocessed(self, to_address: Optional[str] = None) -> int:
        """Count unprocessed messages."""
        from sqlalchemy import func as sql_func

        query = select(sql_func.count()).select_from(InboundMessage).where(
            InboundMessage.processed == False
        )
        if to_address:
            query = query.where(InboundMessage.to_address == to_address)
        return self.session.execute(query).scalar() or 0

    def cleanup_old_messages(self, older_than_days: int = 90) -> int:
        """Delete processed messages older than the specified number of days."""
        cutoff = datetime.utcnow()
        from datetime import timedelta
        cutoff -= timedelta(days=older_than_days)

        result = self.session.execute(
            delete(InboundMessage).where(
                InboundMessage.processed == True,
                InboundMessage.received_at < cutoff,
            )
        )
        return result.rowcount