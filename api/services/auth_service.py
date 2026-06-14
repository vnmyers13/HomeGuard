"""Authentication service: JWT, bcrypt password hashing, session management."""

import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from passlib.context import CryptContext

from database import get_session
from models.auth import User, Session as UserModelSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.environ.get("JWT_SECRET", "CHANGE_ME_jwt_secret_key_at_least_32_chars")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60
RESET_CODE_EXPIRY_MINUTES = 15


# --- Password helpers ---

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# --- JWT helpers ---

def create_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    expires = now + (expires_delta or timedelta(minutes=JWT_EXPIRY_MINUTES))
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expires,
        "iat": now,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, int((expires - now).total_seconds())


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# --- Current user dependency ---

def get_current_user(authorization: str = Header("Bearer ..."), session=None) -> User:
    """Extract current user from Authorization Bearer token. Used as FastAPI dependency."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        # Strip "Bearer " prefix if present
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except HTTPException:
        raise

    if session is None:
        from database import get_session as _gs
        session = next(_gs())

    user = session.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require the current user to have admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


# --- Session management ---

def create_session(user_id: uuid.UUID, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> UserModelSession:
    """Create a new session record (used for JWT revocation tracking)."""
    expires = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    s = UserModelSession(
        user_id=user_id,
        issued_at=datetime.now(timezone.utc),
        expires_at=expires,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return s


def revoke_session(session_id: uuid.UUID, session=None):
    """Mark a session as revoked (logout)."""
    if session is None:
        from database import get_session as _gs
        session = next(_gs())
    record = session.get(UserModelSession, session_id)
    if record:
        record.revoked_at = datetime.now(timezone.utc)


# --- Auth service (register/login/verify) ---

class AuthService:
    @staticmethod
    def register(username: str, password: str, session) -> tuple[User, dict]:
        """Register a new user. Returns (User, token_info). First user becomes admin."""
        # Check uniqueness
        existing = session.query(User).filter(
            User.username == username
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists")

        new_user = User(
            username=username,
            password_hash=hash_password(password),
            role="admin",  # first user is admin
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        token, expires_in = create_token(str(new_user.id), new_user.role)
        return new_user, {"access_token": token, "token_type": "bearer", "expires_in": expires_in}

    @staticmethod
    def login(username: str, password: str, session) -> tuple[User, dict]:
        """Login a user. Returns (User, token_info)."""
        user = session.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        user.last_login_at = datetime.now(timezone.utc)
        session.commit()

        token, expires_in = create_token(str(user.id), user.role)
        return user, {"access_token": token, "token_type": "bearer", "expires_in": expires_in}

    @staticmethod
    def verify(user: User) -> dict:
        """Verify current user from token. Called via get_current_user dependency."""
        return {"user": user}