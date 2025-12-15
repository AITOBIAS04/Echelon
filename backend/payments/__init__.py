"""
Coinbase Payments Module
========================
Handles USDC stablecoin payments on Base network using Coinbase Commerce.

Components:
- coinbase_commerce.py: Core Commerce API client
- routes.py: FastAPI routes for payment operations

Setup:
1. Get API key from https://commerce.coinbase.com
2. Set environment variables:
   - COINBASE_COMMERCE_API_KEY
   - COINBASE_WEBHOOK_SECRET
3. Add routes to FastAPI app:
   
   from .routes import router as payments_router
   app.include_router(payments_router)

4. Configure webhook URL in Coinbase Commerce dashboard:
   https://your-domain.com/payments/webhook
"""
from .coinbase_commerce import (
    CoinbaseCommerceClient,
    PaymentHandler,
    CommerceConfig,
    Charge,
    ChargeMetadata,
    ChargeType,
    PaymentStatus,
    PaymentNetwork,
    WebhookEvent,
    get_commerce_client,
    get_payment_handler
)
from .routes import router

__all__ = [
    "CoinbaseCommerceClient",
    "PaymentHandler", 
    "CommerceConfig",
    "Charge",
    "ChargeMetadata",
    "ChargeType",
    "PaymentStatus",
    "PaymentNetwork",
    "WebhookEvent",
    "get_commerce_client",
    "get_payment_handler",
    "router"
]
