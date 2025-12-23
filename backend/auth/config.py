"""
Authentication Configuration
============================

Configuration for JWT tokens, password hashing, and authentication settings.
"""
import os
from datetime import timedelta


class AuthConfig:
    """Authentication configuration from environment variables."""
    
    # JWT Settings
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Token expiration as timedelta objects
    ACCESS_TOKEN_EXPIRE = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    REFRESH_TOKEN_EXPIRE = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Password hashing
    PASSWORD_HASH_ALGORITHM = "bcrypt"  # Using passlib with bcrypt
    
    # Security settings
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = False



