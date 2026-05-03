"""
Audit Schema Models
Append-only audit log and system event tracking.
"""
from sqlalchemy import Column, Text, DateTime, Integer, ForeignKey, Index, event
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
try:
    from api.database import Base
except ImportError:
    from database import Base


class AuditLog(Base):
    """
    Append-only audit log for compliance. Cannot be updated or deleted.
    """
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_audit_log_created", "created_at"),
        {"schema": "audit"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    event_type = Column(Text, nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    target_entity_type = Column(Text, nullable=True)
    target_entity_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(INET, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def delete(self, _):
        raise NotImplementedError("Audit log entries cannot be deleted")

    def update(self, **kwargs):
        raise NotImplementedError("Audit log entries cannot be updated")


class SystemEvent(Base):
    """Celery task execution log - separate from compliance audit_log."""
    __tablename__ = "system_events"
    __table_args__ = {"schema": "audit"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    task_name = Column(Text, nullable=False)
    task_id = Column(Text, nullable=False, unique=True)
    status = Column(Text, nullable=False)  # started|success|failure|retry
    retry_count = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    kwargs = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)