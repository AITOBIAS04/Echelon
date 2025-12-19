"""
Authentication API Routes
=========================

Endpoints for user registration, login, and token management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr

from backend.auth.jwt import create_access_token, create_refresh_token, TokenData
from backend.auth.password import hash_password, verify_password
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

# Mock user store (replace with database)
USERS = {}


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
async def register(req: RegisterRequest):
    """
    Register a new user.
    
    Returns:
        User ID and success message
    """
    if req.email in USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = f"USR_{len(USERS)+1:04d}"
    USERS[req.email] = {
        "id": user_id,
        "username": req.username,
        "email": req.email,
        "password_hash": hash_password(req.password),
        "tier": "free"
    }
    return {
        "user_id": user_id,
        "message": "Registered successfully"
    }


@router.post("/login")
async def login(req: LoginRequest):
    """
    Login with email and password.
    
    Returns:
        Access token, refresh token, and user info
    """
    user = USERS.get(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token_data = {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "tier": user["tier"]
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
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

