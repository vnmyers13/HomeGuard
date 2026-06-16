"""
Identity Schema Models
Household member profiles and encrypted PII fields.
"""
import os
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    ForeignKey, Index, event, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
try:
    from database import Base
except ImportError:
    from database import Base


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "identity"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    household_id = Column(UUID(as_uuid=True), ForeignKey("auth.households.id"), nullable=True)
    display_name = Column(Text, nullable=False)
    full_legal_name = Column(Text, nullable=False)
    date_of_birth = Column(Date)
    gender = Column(Text)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_paused = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    fields = relationship("ProfileField", back_populates="profile", cascade="all, delete-orphan")
    aliases = relationship("Alias", back_populates="profile", cascade="all, delete-orphan")
    documents = relationship("IdentityDocument", back_populates="profile", cascade="all, delete-orphan")


class ProfileField(Base):
    __tablename__ = "profile_fields"
    __table_args__ = (
        Index("idx_profile_fields_current", "profile_id", "is_current",
              postgresql_where=text("is_current = true")),
        {"schema": "identity"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    field_type = Column(Text, nullable=False)  # address|phone|email|employer|relative_name
    field_value = Column(Text, nullable=False)
    field_subtype = Column(Text, nullable=True)  # mobile|landline|home|work|personal|previous
    is_current = Column(Boolean, nullable=False, default=True)
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    source = Column(Text, nullable=True)  # manual|import|verified
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="fields")


class Alias(Base):
    __tablename__ = "aliases"
    __table_args__ = {"schema": "identity"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    alias_name = Column(Text, nullable=False)
    alias_type = Column(Text, nullable=True)  # maiden_name|nickname|former_name|professional
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="aliases")


class IdentityDocument(Base):
    __tablename__ = "identity_documents"
    __table_args__ = {"schema": "identity"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=False)
    document_type = Column(Text, nullable=False)  # drivers_license|passport|state_id|utility_bill
    file_path = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    profile = relationship("Profile", back_populates="documents")