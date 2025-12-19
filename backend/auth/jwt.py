"""
JWT Token Utilities
===================

Functions for creating and decoding JWT access and refresh tokens.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from pydantic import BaseModel

from .config import AuthConfig


class TokenData(BaseModel):
    """Token payload data model."""
    user_id: str
    username: str
    email: str
    tier: str


def create_access_token(data: Dict) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing user data (user_id, username, email, tier)
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, AuthConfig.JWT_SECRET, algorithm=AuthConfig.JWT_ALGORITHM)


def create_refresh_token(data: Dict) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Dictionary containing user data (user_id, username, email, tier)
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, AuthConfig.JWT_SECRET, algorithm=AuthConfig.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        TokenData if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, AuthConfig.JWT_SECRET, algorithms=[AuthConfig.JWT_ALGORITHM])
        
        # Validate required fields
        user_id = payload.get("user_id")
        username = payload.get("username")
        email = payload.get("email")
        tier = payload.get("tier")
        
        if not all([user_id, username, email, tier]):
            return None
        
        return TokenData(
            user_id=user_id,
            username=username,
            email=email,
            tier=tier
        )
    except JWTError:
        return None

