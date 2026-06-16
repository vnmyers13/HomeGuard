"""
Archive Schema Models
Mirrors of key tables - populated during profile deletion transaction before hard delete.
All archive tables include archived_at TIMESTAMPTZ NOT NULL DEFAULT now().
"""
from sqlalchemy import Column, Text, Boolean, DateTime, Integer, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
try:
    from database import Base
except ImportError:
    from database import Base


class ArchiveProfile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    household_id = Column(UUID(as_uuid=True), nullable=True)
    display_name = Column(Text, nullable=False)
    full_legal_name = Column(Text, nullable=False)
    date_of_birth = Column(Date)
    gender = Column(Text)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_paused = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArchiveProfileField(Base):
    __tablename__ = "profile_fields"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    profile_id = Column(UUID(as_uuid=True), nullable=False)
    field_type = Column(Text, nullable=False)
    field_value = Column(Text, nullable=False)
    field_subtype = Column(Text, nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    source = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArchiveAlias(Base):
    __tablename__ = "aliases"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    profile_id = Column(UUID(as_uuid=True), nullable=False)
    alias_name = Column(Text, nullable=False)
    alias_type = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArchiveIdentityDocument(Base):
    __tablename__ = "identity_documents"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    profile_id = Column(UUID(as_uuid=True), nullable=False)
    document_type = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArchiveExposure(Base):
    __tablename__ = "exposures"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    profile_id = Column(UUID(as_uuid=True), nullable=False)
    broker_id = Column(UUID(as_uuid=True), nullable=False)
    data_fields_found = Column(JSONB, nullable=True)
    first_detected_at = Column(DateTime(timezone=True), nullable=False)
    last_confirmed_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_removed = Column(Boolean, nullable=False, default=False)
    removed_at = Column(DateTime(timezone=True), nullable=True)
    removal_request_id = Column(UUID(as_uuid=True), nullable=True)
    scan_run_id = Column(UUID(as_uuid=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArchiveScanResult(Base):
    __tablename__ = "scan_results"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    scan_run_id = Column(UUID(as_uuid=True), nullable=False)
    profile_id = Column(UUID(as_uuid=True), nullable=False)
    broker_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Text, nullable=False)
    data_found = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    screenshot_path = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArchiveRemovalRequest(Base):
    __tablename__ = "removal_requests"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    profile_id = Column(UUID(as_uuid=True), nullable=False)
    broker_id = Column(UUID(as_uuid=True), nullable=False)
    exposure_id = Column(UUID(as_uuid=True), nullable=False)
    removal_method = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    confirmation_message = Column(Text, nullable=True)
    next_action_at = Column(DateTime(timezone=True), nullable=True)
    followup_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArchiveRequestStatusLog(Base):
    __tablename__ = "request_status_log"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    request_id = Column(UUID(as_uuid=True), nullable=False)
    previous_status = Column(Text, nullable=True)
    new_status = Column(Text, nullable=False)
    change_reason = Column(Text, nullable=True)
    meta_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArchiveFollowup(Base):
    __tablename__ = "followups"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    request_id = Column(UUID(as_uuid=True), nullable=False)
    followup_number = Column(Integer, nullable=False)
    method_used = Column(Text, nullable=False)
    response_received = Column(Boolean, nullable=False, default=False)
    response_details = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArchiveMessageClassification(Base):
    __tablename__ = "message_classifications"
    __table_args__ = {"schema": "archive"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    message_id = Column(UUID(as_uuid=True), nullable=False)
    classification = Column(Text, nullable=False)
    confidence = Column(Integer, nullable=False, default=0)
    matched_pattern = Column(Text, nullable=True)
    extracted_data = Column(JSONB, nullable=True)
    linked_request_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())