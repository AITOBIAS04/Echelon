"""
Authentication API Routes
=========================

Endpoints for user registration, login, and token management.
Uses async database sessions with the canonical User model.
"""
import uuid

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import create_access_token, create_refresh_token, TokenData
from backend.auth.password import hash_password, verify_password
from backend.dependencies import get_current_user, get_db
from backend.database.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    """User registration request."""
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    Returns:
        User ID and success message
    """
    user_id = str(uuid.uuid4())

    user = User(
        id=user_id,
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        tier="free",
        balance_usdc=0.0,
        balance_echelon=0,
    )

    try:
        db.add(user)
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )

    return {
        "user_id": user_id,
        "message": "Registered successfully"
    }


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.

    Returns:
        Access token, refresh token, and user info
    """
    result = await db.execute(
        select(User).where(User.email == req.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token_data = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "tier": user.tier,
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }


@router.get("/me")
async def get_me(user: TokenData = Depends(get_current_user)):
    """
    Get current user info from JWT token.

    Requires:
        Bearer token in Authorization header

    Returns:
        User ID, username, email, and tier
    """
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "tier": user.tier
    }
