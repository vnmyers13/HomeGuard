"""
Scanning Schema Models
Scan runs, results, exposures, and screenshots.
"""
from sqlalchemy import Column, Text, Boolean, DateTime, Integer, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
try:
    from api.database import Base
except ImportError:
    from database import Base


class ScanRun(Base):
    __tablename__ = "scan_runs"
    __table_args__ = {"schema": "scanning"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    run_type = Column(Text, nullable=False)  # manual|scheduled|verification|catch_up
    status = Column(Text, nullable=False, default="pending")  # pending|running|completed|failed|cancelled
    total_brokers = Column(Integer, nullable=False, default=0)
    completed_brokers = Column(Integer, nullable=False, default=0)
    exposures_found = Column(Integer, nullable=False, default=0)
    exposures_removed = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)


class ScanResult(Base):
    __tablename__ = "scan_results"
    __table_args__ = {"schema": "scanning"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("scanning.scan_runs.id"), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=False)
    status = Column(Text, nullable=False)  # found|not_found|error
    data_found = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    screenshot_path = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Exposure(Base):
    __tablename__ = "exposures"
    __table_args__ = (
        Index("idx_exposures_active", "profile_id", "broker_id",
              postgresql_where=text("is_active = true")),
        {"schema": "scanning"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=False)
    data_fields_found = Column(JSONB, nullable=True)
    first_detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_confirmed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    is_removed = Column(Boolean, nullable=False, default=False)
    removed_at = Column(DateTime(timezone=True), nullable=True)
    removal_request_id = Column(UUID(as_uuid=True), ForeignKey("requests.removal_requests.id"), nullable=True)
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("scanning.scan_runs.id"), nullable=True)


class Screenshot(Base):
    __tablename__ = "screenshots"
    __table_args__ = {"schema": "scanning"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    scan_result_id = Column(UUID(as_uuid=True), ForeignKey("scanning.scan_results.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    screenshot_type = Column(Text, nullable=False)  # evidence|error|confirmation
    file_size_bytes = Column(Integer, nullable=True)
    taken_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    purge_at = Column(DateTime(timezone=True), nullable=True)
    purged_at = Column(DateTime(timezone=True), nullable=True)