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
from models.auth import User, Session as UserModelSession, PasswordResetToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.environ.get("JWT_SECRET", "CHANGE_ME_jwt_secret_key_at_least_32_chars")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60
RESET_CODE_EXPIRY_MINUTES = 15
RESET_TOKEN_SECRET = os.environ.get("RESET_TOKEN_SECRET", JWT_SECRET)


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

    @staticmethod
    def generate_code(email: str, session) -> dict:
        """Generate a 6-digit reset code for the given email. Returns code info."""
        from database import get_session as _gs
        if session is None:
            session = next(_gs())

        # Invalidate any existing unused codes for this email
        session.query(PasswordResetToken).filter(
            PasswordResetToken.email == email,
            PasswordResetToken.used == False,
        ).update({"used": True})

        code = str(random.randint(100000, 999999))
        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_CODE_EXPIRY_MINUTES)

        reset_token = PasswordResetToken(
            email=email,
            code=code,
            token=token,
            expires_at=expires_at,
        )
        session.add(reset_token)
        session.commit()

        return {
            "email": email,
            "code": code,
            "token": token,
            "expires_at": expires_at,
        }

    @staticmethod
    def create_magic_link(email: str, session) -> dict:
        """Create a magic link token for the given email. Returns token info."""
        from database import get_session as _gs
        if session is None:
            session = next(_gs())

        # Invalidate any existing unused codes for this email
        session.query(PasswordResetToken).filter(
            PasswordResetToken.email == email,
            PasswordResetToken.used == False,
        ).update({"used": True})

        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_CODE_EXPIRY_MINUTES)

        reset_token = PasswordResetToken(
            email=email,
            code="",
            token=token,
            expires_at=expires_at,
        )
        session.add(reset_token)
        session.commit()

        return {
            "email": email,
            "token": token,
            "expires_at": expires_at,
        }

    @staticmethod
    def verify_magic_link(token: str, new_password: str, session) -> dict:
        """Verify a magic link token and reset the password. Returns success info."""
        from database import get_session as _gs
        if session is None:
            session = next(_gs())

        reset_token = session.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        ).first()

        if not reset_token:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

        user = session.query(User).filter(User.email == reset_token.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="No account found with this email")

        user.password_hash = hash_password(new_password)
        reset_token.used = True
        session.commit()

        # Revoke all existing sessions for this user
        session.query(UserModelSession).filter(
            UserModelSession.user_id == user.id,
            UserModelSession.revoked_at.is_(None),
        ).update({"revoked_at": datetime.now(timezone.utc)})

        return {"success": True, "message": "Password reset successfully"}

    @staticmethod
    def reset_password_with_code(email: str, code: str, new_password: str, session) -> dict:
        """Reset password using a 6-digit code. Returns success info."""
        from database import get_session as _gs
        if session is None:
            session = next(_gs())

        reset_token = session.query(PasswordResetToken).filter(
            PasswordResetToken.email == email,
            PasswordResetToken.code == code,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        ).first()

        if not reset_token:
            raise HTTPException(status_code=400, detail="Invalid or expired reset code")

        user = session.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="No account found with this email")

        user.password_hash = hash_password(new_password)
        reset_token.used = True
        session.commit()

        # Revoke all existing sessions for this user
        session.query(UserModelSession).filter(
            UserModelSession.user_id == user.id,
            UserModelSession.revoked_at.is_(None),
        ).update({"revoked_at": datetime.now(timezone.utc)})

        return {"success": True, "message": "Password reset successfully"}