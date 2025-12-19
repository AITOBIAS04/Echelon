"""
Password Hashing Utilities
===========================

Functions for hashing and verifying passwords using bcrypt.
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Note: bcrypt has a 72-byte limit. Longer passwords will be truncated.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string (bcrypt format)
    """
    # bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain: Plain text password to verify
        hashed: Hashed password to compare against (bcrypt format)
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        plain_bytes = plain.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        
        # Truncate if necessary (bcrypt limit)
        if len(plain_bytes) > 72:
            plain_bytes = plain_bytes[:72]
        
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False
