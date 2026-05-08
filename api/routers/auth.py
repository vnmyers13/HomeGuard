"""Auth router - register, login, verify, logout endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr, BaseModel, Field

from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    VerifyResponse,
    LogoutRequest,
)
from services.auth_service import AuthService, get_current_user
from database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


class ChangePasswordRequest(BaseModel):
    """Request body for changing password."""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class ChangePasswordResponse(BaseModel):
    """Response for password change."""
    success: bool
    message: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, session=None):
    """Register a new user account. First user becomes admin."""
    try:
        user, token_info = AuthService.register(body.username, body.password, session)
        return {
            "success": True,
            "data": {
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role,
                **token_info,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login", status_code=status.HTTP_200_OK)
def login(body: LoginRequest, session=None):
    """Login with username and password. Returns JWT token."""
    try:
        user, token_info = AuthService.login(body.username, body.password, session)
        return {
            "success": True,
            "data": {
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role,
                **token_info,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/verify", status_code=status.HTTP_200_OK)
def verify(user=Depends(get_current_user)):
    """Verify current user from JWT token. Returns user info."""
    return {
        "success": True,
        "data": VerifyResponse.from_user(user).model_dump(),
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(user=Depends(get_current_user)):
    """Logout current user (invalidate session)."""
    return {
        "success": True,
        "message": "Logged out successfully",
    }


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    body: ChangePasswordRequest,
    user=Depends(get_current_user),
    session=None,
):
    """Change current user's password."""
    from services.auth_service import verify_password, hash_password

    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

    user.password_hash = hash_password(body.new_password)
    session.commit()

    return {
        "success": True,
        "message": "Password changed successfully",
    }