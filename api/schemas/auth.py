"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserOut(BaseModel):
    """User output schema - excludes sensitive fields like password."""
    id: str
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Response returned on successful login."""
    success: bool = True
    user_id: str
    username: str
    role: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutRequest(BaseModel):
    """Request body for logout (optional token refresh info)."""
    pass


class VerifyResponse(BaseModel):
    user: UserResponse

    @classmethod
    def from_user(cls, user):
        return cls(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        )


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetResponse(BaseModel):
    success: bool = True
    message: str
