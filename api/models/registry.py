"""
Registry Schema Models
Data broker catalog and versioned automation playbooks.
"""
from sqlalchemy import Column, Text, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
try:
    from api.database import Base
except ImportError:
    from database import Base


class Broker(Base):
    __tablename__ = "brokers"
    __table_args__ = (
        Index("idx_brokers_active", "canonical_domain", "is_active"),
        {"schema": "registry"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    canonical_domain = Column(Text, nullable=False, unique=True)
    display_name = Column(Text, nullable=False)
    category = Column(Text, nullable=True)
    removal_method = Column(Text, nullable=True)
    opt_out_url = Column(Text, nullable=True)
    contact_email = Column(Text, nullable=True)
    ccpa_applicable = Column(Boolean, nullable=False, default=False)
    gdpr_applicable = Column(Boolean, nullable=False, default=False)
    captcha_required = Column(Boolean, nullable=False, default=False)
    requires_manual = Column(Boolean, nullable=False, default=False)
    estimated_response_days = Column(Integer, nullable=True, default=30)
    is_active = Column(Boolean, nullable=False, default=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    discovered_via = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    playbooks = relationship("BrokerPlaybook", back_populates="broker", cascade="all, delete-orphan")
    field_requirements = relationship("BrokerFieldRequirement", back_populates="broker", cascade="all, delete-orphan")
    email_templates = relationship("EmailTemplate", back_populates="broker", cascade="all, delete-orphan")


class BrokerFieldRequirement(Base):
    __tablename__ = "broker_field_requirements"
    __table_args__ = {"schema": "registry"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=False)
    field_type = Column(Text, nullable=False)
    is_required = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)

    broker = relationship("Broker", back_populates="field_requirements")


class BrokerPlaybook(Base):
    __tablename__ = "broker_playbooks"
    __table_args__ = (
        Index("idx_broker_playbooks_active", "broker_id", "is_active"),
        {"schema": "registry"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=False)
    version = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    playbook_json = Column(JSONB, nullable=False)
    change_notes = Column(Text, nullable=True)
    created_by = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    activated_at = Column(DateTime(timezone=True), nullable=True)

    broker = relationship("Broker", back_populates="playbooks")


class EmailTemplate(Base):
    __tablename__ = "email_templates"
    __table_args__ = {"schema": "registry"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    broker_id = Column(UUID(as_uuid=True), ForeignKey("registry.brokers.id"), nullable=True)
    template_type = Column(Text, nullable=False)
    template_path = Column(Text, nullable=False)
    subject_line = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    broker = relationship("Broker", back_populates="email_templates")