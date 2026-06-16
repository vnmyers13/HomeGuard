"""
Auth Schema Models
User accounts, sessions, and notification queue.
"""
from sqlalchemy import Column, Text, Boolean, DateTime, Integer, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
try:
    from database import Base
except ImportError:
    from database import Base


class Household(Base):
    """
    Household group linking multiple profiles.
    """
    __tablename__ = "households"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(Text, nullable=False, default="OpenDataRemoval")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    username = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    role = Column(Text, nullable=False, default="member")  # admin|member
    linked_profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user")


class Session(Base):
    """
    Active JWT sessions. id is also the JWT jti claim for revocation.
    """
    __tablename__ = "sessions"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    user = relationship("User", back_populates="sessions")


class Notification(Base):
    """
    Dashboard notifications. Persisted for durability + pushed via Redis pub/sub WebSocket.
    """
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user_unread", "user_id", "created_at",
              postgresql_where=text("is_read = false")),
        {"schema": "auth"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    notification_type = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=True)
    entity_type = Column(Text, nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("identity.profiles.id"), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="notifications")


class PasswordResetToken(Base):
    """
    One-time password reset tokens generated via forgot-password flow.
    """
    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    token = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())