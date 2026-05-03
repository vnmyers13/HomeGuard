"""
Requests Schema Models
Removal requests, status logs, followups, and verification scans.
"""
from sqlalchemy import Column, Text, Boolean, DateTime, Integer, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
try:
    from api.database import Base
except ImportError:
    from database import Base


class RemovalRequest(Base):
    __tablename__ = "removal_requests"
    __table_args__ = (
        Index("idx_removal_requests_next_action", "next_action_at",
              postgresql_where=text("status NOT IN ('confirmed_removed', 'failed')")),
        {"schema": "requests"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=False)
    exposure_id = Column(UUID(as_uuid=True), ForeignKey("scanning.exposures.id"), nullable=False)
    removal_method = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    confirmation_message = Column(Text, nullable=True)
    next_action_at = Column(DateTime(timezone=True), nullable=True)
    followup_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class RequestStatusLog(Base):
    __tablename__ = "request_status_log"
    __table_args__ = {"schema": "requests"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.removal_requests.id"), nullable=False)
    previous_status = Column(Text, nullable=True)
    new_status = Column(Text, nullable=False)
    change_reason = Column(Text, nullable=True)
    meta_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Followup(Base):
    __tablename__ = "followups"
    __table_args__ = {"schema": "requests"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.removal_requests.id"), nullable=False)
    followup_number = Column(Integer, nullable=False)
    method_used = Column(Text, nullable=False)
    response_received = Column(Boolean, nullable=False, default=False)
    response_details = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)


class VerificationScan(Base):
    __tablename__ = "verification_scans"
    __table_args__ = {"schema": "requests"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    removal_request_id = Column(UUID(as_uuid=True), ForeignKey("requests.removal_requests.id"), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=False)
    result = Column(Text, nullable=True)
    evidence_path = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)