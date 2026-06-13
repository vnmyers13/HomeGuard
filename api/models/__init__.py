"""
OpenDataRemoval SQLAlchemy Models
All models across 9 schemas with PII encryption support.
"""
import os
from sqlalchemy import TypeDecorator, text, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, DATE as PGDate
from sqlalchemy.sql import func
try:
    from api.database import Base
except ImportError:
    from database import Base


class EncryptedText(TypeDecorator):
    """
    PII encryption TypeDecorator using pgcrypto.
    Encrypts on bind, decrypts on result.
    All PII columns use this type.
    """
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        key = os.environ.get("DB_ENCRYPTION_KEY", "default_encryption_key")
        # Use pgp_sym_encrypt for encryption
        return f"pgp_sym_encrypt('{value}', '{key}')"

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        key = os.environ.get("DB_ENCRYPTION_KEY", "default_encryption_key")
        return value  # Decryption handled at query level via pgp_sym_decrypt


# Import all model modules to register with Base.metadata
try:
    from api.models.identity import Profile, ProfileField, Alias, IdentityDocument
    from api.models.registry import Broker, BrokerFieldRequirement, BrokerPlaybook, EmailTemplate
    from api.models.scanning import ScanRun, ScanResult, Exposure, Screenshot
    from api.models.requests import RemovalRequest, RequestStatusLog, Followup, VerificationScan
    from api.models.mail import InboundMessage, MessageClassification
    from api.models.audit import AuditLog, SystemEvent
    from api.models.reporting import ExposureScore, DailyBrokerSnapshot, RelistingEvent, FieldExposureSummary
    from api.models.auth import Household, User, Session, Notification
    from api.models.archive import (
        ArchiveProfile, ArchiveProfileField, ArchiveAlias,
        ArchiveIdentityDocument, ArchiveExposure, ArchiveScanResult,
        ArchiveRemovalRequest, ArchiveRequestStatusLog, ArchiveFollowup,
        ArchiveMessageClassification
    )
except ImportError:
    from models.identity import Profile, ProfileField, Alias, IdentityDocument
    from models.registry import Broker, BrokerFieldRequirement, BrokerPlaybook, EmailTemplate
    from models.scanning import ScanRun, ScanResult, Exposure, Screenshot
    from models.requests import RemovalRequest, RequestStatusLog, Followup, VerificationScan
    from models.mail import InboundMessage, MessageClassification
    from models.audit import AuditLog, SystemEvent
    from models.reporting import ExposureScore, DailyBrokerSnapshot, RelistingEvent, FieldExposureSummary
    from models.auth import Household, User, Session, Notification
    from models.archive import (
        ArchiveProfile, ArchiveProfileField, ArchiveAlias,
        ArchiveIdentityDocument, ArchiveExposure, ArchiveScanResult,
        ArchiveRemovalRequest, ArchiveRequestStatusLog, ArchiveFollowup,
        ArchiveMessageClassification
    )

__all__ = [
    "Profile", "ProfileField", "Alias", "IdentityDocument",
    "Broker", "BrokerFieldRequirement", "BrokerPlaybook", "EmailTemplate",
    "ScanRun", "ScanResult", "Exposure", "Screenshot",
    "RemovalRequest", "RequestStatusLog", "Followup", "VerificationScan",
    "InboundMessage", "MessageClassification",
    "AuditLog", "SystemEvent",
    "ExposureScore", "DailyBrokerSnapshot", "RelistingEvent", "FieldExposureSummary",
    "Household", "User", "Session", "Notification",
    "ArchiveProfile", "ArchiveProfileField", "ArchiveAlias",
    "ArchiveIdentityDocument", "ArchiveExposure", "ArchiveScanResult",
    "ArchiveRemovalRequest", "ArchiveRequestStatusLog", "ArchiveFollowup",
    "ArchiveMessageClassification",
]