"""
Password Hashing Utilities
===========================

Functions for hashing and verifying passwords using bcrypt.
"""
from passlib.context import CryptContext

# Configure password hashing context
# Using bcrypt as specified in AuthConfig
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Note: bcrypt has a 72-byte limit. Longer passwords will be truncated.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    # bcrypt has a 72-byte limit, truncate if necessary
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain: Plain text password to verify
        hashed: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain, hashed)

