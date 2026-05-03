"""
Mail Schema Models
Inbound messages and message classifications for Mailwatcher.
"""
from sqlalchemy import Column, Text, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
try:
    from api.database import Base
except ImportError:
    from database import Base


class InboundMessage(Base):
    __tablename__ = "inbound_messages"
    __table_args__ = (
        Index("idx_inbound_messages_msgid", "message_id_header", unique=True),
        {"schema": "mail"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id_header = Column(Text, nullable=False, unique=True)
    from_address = Column(Text, nullable=False)
    to_address = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    headers = Column(JSONB, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed = Column(Boolean, nullable=False, default=False)


class MessageClassification(Base):
    __tablename__ = "message_classifications"
    __table_args__ = {"schema": "mail"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(UUID(as_uuid=True), ForeignKey("mail.inbound_messages.id"), nullable=False)
    classification = Column(Text, nullable=False)  # confirmed_removal|rejection|info_requested|verification_link|unclassified
    confidence = Column(Integer, nullable=False, default=0)
    matched_pattern = Column(Text, nullable=True)
    extracted_data = Column(JSONB, nullable=True)
    linked_request_id = Column(UUID(as_uuid=True), ForeignKey("requests.removal_requests.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())