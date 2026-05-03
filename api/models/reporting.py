"""
Reporting Schema Models
Pre-computed analytics for dashboard reads.
"""
from sqlalchemy import Column, Text, Boolean, DateTime, Integer, ForeignKey, Index, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
try:
    from api.database import Base
except ImportError:
    from database import Base


class ExposureScore(Base):
    __tablename__ = "exposure_scores"
    __table_args__ = (
        Index("idx_exposure_scores_profile_date", "profile_id", "score_date"),
        {"schema": "reporting"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    score_date = Column(Date, nullable=False)
    score = Column(Numeric(5, 1), nullable=False)
    active_exposures = Column(Integer, nullable=False)
    total_confirmed_removed = Column(Integer, nullable=False)
    total_re_listings = Column(Integer, nullable=False)
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("scanning.scan_runs.id"), nullable=True)
    computed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DailyBrokerSnapshot(Base):
    __tablename__ = "daily_broker_snapshots"
    __table_args__ = {"schema": "reporting"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    exposure_score_id = Column(UUID(as_uuid=True), ForeignKey("reporting.exposure_scores.id"), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=False)
    score_date = Column(Date, nullable=False)
    status = Column(Text, nullable=False)
    active_request_id = Column(UUID(as_uuid=True), ForeignKey("requests.removal_requests.id"), nullable=True)


class RelistingEvent(Base):
    __tablename__ = "relisting_events"
    __table_args__ = {"schema": "reporting"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=False)
    original_request_id = Column(UUID(as_uuid=True), ForeignKey("requests.removal_requests.id"), nullable=False)
    relisting_request_id = Column(UUID(as_uuid=True), ForeignKey("requests.removal_requests.id"), nullable=False)
    days_until_relisting = Column(Integer, nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class FieldExposureSummary(Base):
    __tablename__ = "field_exposure_summary"
    __table_args__ = {"schema": "reporting"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=False)
    field_type = Column(Text, nullable=False)
    is_currently_exposed = Column(Boolean, nullable=False, default=True)
    first_detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    removed_at = Column(DateTime(timezone=True), nullable=True)