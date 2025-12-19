"""
Authentication Module
====================

JWT token generation, password hashing, and user authentication.
"""

from .config import AuthConfig
from .jwt import (
    TokenData,
    create_access_token,
    create_refresh_token,
    decode_token
)

__all__ = [
    "AuthConfig",
    "TokenData",
    "create_access_token",
    "create_refresh_token",
    "decode_token"
]

