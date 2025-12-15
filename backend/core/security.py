"""
Security Utilities for Echelon
==============================

Provides:
- Rate limiting
- Input validation
- Address validation
- Sanitization helpers
"""

import re
from typing import Optional
from eth_utils import is_address, to_checksum_address
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "general": "100/hour",  # General endpoints
    "betting": "20/minute",  # Betting endpoints
    "auth": "5/minute",  # Authentication endpoints
    "api": "200/hour",  # API endpoints
}


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    if request.client:
        # Check for forwarded IP (from proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain
            return forwarded.split(",")[0].strip()
        return request.client.host
    return "unknown"


# Update limiter to use our IP function
limiter.key_func = get_client_ip


class WalletAddressValidator:
    """Validates Ethereum wallet addresses."""
    
    @staticmethod
    def validate(address: str) -> str:
        """
        Validate and normalize an Ethereum address.
        
        Args:
            address: Ethereum address string
            
        Returns:
            Checksummed address
            
        Raises:
            HTTPException: If address is invalid
        """
        if not address:
            raise HTTPException(
                status_code=400,
                detail="Wallet address is required"
            )
        
        # Remove whitespace
        address = address.strip()
        
        # Check if it's a valid Ethereum address
        if not is_address(address):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Ethereum address format: {address}"
            )
        
        # Return checksummed address
        try:
            return to_checksum_address(address)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid address format: {str(e)}"
            )


class BetAmountValidator:
    """Validates bet amounts."""
    
    MIN_BET = 0.01  # Minimum bet amount in USD
    MAX_BET = 100000.0  # Maximum bet amount in USD
    
    @classmethod
    def validate(cls, amount: float) -> float:
        """
        Validate bet amount.
        
        Args:
            amount: Bet amount in USD
            
        Returns:
            Validated amount
            
        Raises:
            HTTPException: If amount is invalid
        """
        if amount is None:
            raise HTTPException(
                status_code=400,
                detail="Bet amount is required"
            )
        
        if not isinstance(amount, (int, float)):
            raise HTTPException(
                status_code=400,
                detail="Bet amount must be a number"
            )
        
        if amount <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Bet amount must be greater than 0"
            )
        
        if amount < cls.MIN_BET:
            raise HTTPException(
                status_code=400,
                detail=f"Bet amount must be at least ${cls.MIN_BET}"
            )
        
        if amount > cls.MAX_BET:
            raise HTTPException(
                status_code=400,
                detail=f"Bet amount cannot exceed ${cls.MAX_BET}"
            )
        
        # Round to 2 decimal places
        return round(float(amount), 2)


class StringSanitizer:
    """Sanitizes string inputs to prevent XSS and injection attacks."""
    
    # Allowed characters for various input types
    ALPHANUMERIC = re.compile(r'^[a-zA-Z0-9\s\-_]+$')
    ALPHANUMERIC_EXTENDED = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()]+$')
    CLIENT_SEED = re.compile(r'^[a-zA-Z0-9\-_]+$')  # For client_seed validation
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """
        Sanitize text input.
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML (default: False)
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove HTML if not allowed
        if not allow_html:
            # Simple HTML tag removal (for production, use bleach or similar)
            text = re.sub(r'<[^>]+>', '', text)
        
        return text.strip()
    
    @staticmethod
    def validate_client_seed(seed: str) -> str:
        """
        Validate client_seed for subprocess safety.
        
        Args:
            seed: Client seed string
            
        Returns:
            Validated seed
            
        Raises:
            HTTPException: If seed is invalid
        """
        if not seed:
            raise HTTPException(
                status_code=400,
                detail="client_seed is required"
            )
        
        if not StringSanitizer.CLIENT_SEED.match(seed):
            raise HTTPException(
                status_code=400,
                detail="client_seed can only contain alphanumeric characters, hyphens, and underscores"
            )
        
        if len(seed) > 100:
            raise HTTPException(
                status_code=400,
                detail="client_seed cannot exceed 100 characters"
            )
        
        return seed


# Pydantic validators for request models
def validate_wallet_address(v: str) -> str:
    """Pydantic validator for wallet addresses."""
    return WalletAddressValidator.validate(v)


def validate_bet_amount(v: float) -> float:
    """Pydantic validator for bet amounts."""
    return BetAmountValidator.validate(v)


def validate_client_seed(v: str) -> str:
    """Pydantic validator for client seeds."""
    return StringSanitizer.validate_client_seed(v)

