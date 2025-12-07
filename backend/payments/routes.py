"""
Coinbase Payment API Routes
===========================
FastAPI routes for handling Coinbase Commerce payments.

Endpoints:
- POST /payments/charges - Create a new charge
- GET /payments/charges/{id} - Get charge status
- POST /payments/webhook - Coinbase webhook handler
- GET /payments/balance - Get user balance
- GET /payments/intel-access - Check intel access

Required Environment Variables:
- COINBASE_COMMERCE_API_KEY: Your Commerce API key
- COINBASE_WEBHOOK_SECRET: Webhook signature secret
"""
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import json
from .coinbase_commerce import (
    get_commerce_client,
    get_payment_handler,
    ChargeMetadata,
    ChargeType,
    WebhookEvent
)

router = APIRouter(prefix="/payments", tags=["payments"])

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CreateBetChargeRequest(BaseModel):
    """Request to create a charge for a market bet"""
    user_id: str = Field(..., description="User making the bet")
    market_id: str = Field(..., description="Market to bet on")
    market_title: str = Field(..., description="Human readable market title")
    outcome: str = Field(..., description="Selected outcome (YES/NO/etc)")
    shares: float = Field(..., gt=0, description="Number of shares to buy")
    price_per_share: float = Field(..., gt=0, description="Current price per share")
    redirect_url: Optional[str] = Field(None, description="Success redirect URL")

class CreateIntelChargeRequest(BaseModel):
    """Request to create a charge for intel access"""
    user_id: str = Field(..., description="User requesting access")
    intel_tier: str = Field(..., description="Tier: basic, premium, or alpha")
    market_id: Optional[str] = Field(None, description="Optional specific market")
    redirect_url: Optional[str] = Field(None, description="Success redirect URL")

class CreateDepositChargeRequest(BaseModel):
    """Request to create a deposit charge"""
    user_id: str = Field(..., description="User making deposit")
    amount: float = Field(..., gt=0, le=10000, description="Amount to deposit (USD)")
    redirect_url: Optional[str] = Field(None, description="Success redirect URL")

class ChargeResponse(BaseModel):
    """Response containing charge details"""
    id: str
    code: str
    hosted_url: str
    amount: float
    currency: str
    status: str
    expires_at: str
    metadata: Dict[str, str]
    
    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    """User balance response"""
    user_id: str
    balance: float
    currency: str = "USD"

class IntelAccessResponse(BaseModel):
    """Intel access check response"""
    user_id: str
    tier: str
    has_access: bool
    expires_at: Optional[str] = None

# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/charges/bet", response_model=ChargeResponse)
async def create_bet_charge(request: CreateBetChargeRequest):
    """
    Create a charge for purchasing prediction market shares.
    
    Returns a hosted checkout URL where users can pay with USDC on Base.
    """
    client = get_commerce_client()
    
    try:
        charge = await client.create_market_bet_charge(
            user_id=request.user_id,
            market_id=request.market_id,
            market_title=request.market_title,
            outcome=request.outcome,
            shares=request.shares,
            price_per_share=request.price_per_share,
            redirect_url=request.redirect_url
        )
        
        return ChargeResponse(
            id=charge.id,
            code=charge.code,
            hosted_url=charge.hosted_url,
            amount=charge.amount,
            currency=charge.currency,
            status=charge.status.value,
            expires_at=charge.expires_at.isoformat(),
            metadata=charge.metadata.to_dict()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create charge: {str(e)}")

@router.post("/charges/intel", response_model=ChargeResponse)
async def create_intel_charge(request: CreateIntelChargeRequest):
    """
    Create a charge for intel/research access (x402 payment gate).
    
    Tiers:
    - basic ($1): 24h access to additional context
    - premium ($5): 7-day access to full analysis
    - alpha ($25): 30-day access with real-time updates
    """
    if request.intel_tier not in ["basic", "premium", "alpha"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid tier. Must be: basic, premium, or alpha"
        )
    
    client = get_commerce_client()
    
    try:
        charge = await client.create_intel_access_charge(
            user_id=request.user_id,
            intel_tier=request.intel_tier,
            market_id=request.market_id,
            redirect_url=request.redirect_url
        )
        
        return ChargeResponse(
            id=charge.id,
            code=charge.code,
            hosted_url=charge.hosted_url,
            amount=charge.amount,
            currency=charge.currency,
            status=charge.status.value,
            expires_at=charge.expires_at.isoformat(),
            metadata=charge.metadata.to_dict()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create charge: {str(e)}")

@router.post("/charges/deposit", response_model=ChargeResponse)
async def create_deposit_charge(request: CreateDepositChargeRequest):
    """
    Create a charge for depositing funds to user's balance.
    
    Users can deposit between $1 and $10,000.
    """
    client = get_commerce_client()
    
    try:
        charge = await client.create_deposit_charge(
            user_id=request.user_id,
            amount=request.amount,
            redirect_url=request.redirect_url
        )
        
        return ChargeResponse(
            id=charge.id,
            code=charge.code,
            hosted_url=charge.hosted_url,
            amount=charge.amount,
            currency=charge.currency,
            status=charge.status.value,
            expires_at=charge.expires_at.isoformat(),
            metadata=charge.metadata.to_dict()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create charge: {str(e)}")

@router.get("/charges/{charge_id}")
async def get_charge(charge_id: str):
    """
    Get the current status of a charge.
    
    Use this to check if a payment has been completed.
    """
    client = get_commerce_client()
    
    try:
        charge = await client.get_charge(charge_id)
        return charge.to_dict()
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Charge not found: {str(e)}")

@router.post("/webhook")
async def coinbase_webhook(
    request: Request,
    x_cc_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle webhooks from Coinbase Commerce.
    
    This endpoint receives payment status updates:
    - charge:confirmed - Payment successful
    - charge:failed - Payment failed
    - charge:pending - Payment processing
    - charge:delayed - Payment delayed
    
    Configure this URL in your Coinbase Commerce dashboard:
    https://your-domain.com/payments/webhook
    """
    client = get_commerce_client()
    handler = get_payment_handler()
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify webhook signature
    if x_cc_webhook_signature:
        if not client.verify_webhook_signature(body, x_cc_webhook_signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Parse the webhook payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Parse and handle the event
    try:
        event = client.parse_webhook(payload)
        result = await handler.handle_webhook_event(event)
        
        return JSONResponse(content={
            "status": "ok",
            "event_type": event.type,
            "charge_id": event.charge.id,
            "result": result
        })
    
    except Exception as e:
        # Log but don't fail - Coinbase will retry
        print(f"⚠️ Webhook processing error: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        })

@router.get("/balance/{user_id}", response_model=BalanceResponse)
async def get_user_balance(user_id: str):
    """
    Get a user's current balance.
    """
    handler = get_payment_handler()
    balance = handler.get_user_balance(user_id)
    
    return BalanceResponse(
        user_id=user_id,
        balance=balance,
        currency="USD"
    )

@router.get("/intel-access/{user_id}/{tier}", response_model=IntelAccessResponse)
async def check_intel_access(user_id: str, tier: str):
    """
    Check if a user has active intel access for a specific tier.
    
    Returns access status and expiration time if active.
    """
    if tier not in ["basic", "premium", "alpha"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid tier. Must be: basic, premium, or alpha"
        )
    
    handler = get_payment_handler()
    has_access = handler.check_intel_access(user_id, tier)
    
    # Get expiration if has access
    expires_at = None
    if has_access:
        user_access = handler._intel_access.get(user_id, {})
        exp = user_access.get(tier)
        if exp:
            expires_at = exp.isoformat()
    
    return IntelAccessResponse(
        user_id=user_id,
        tier=tier,
        has_access=has_access,
        expires_at=expires_at
    )

# =============================================================================
# ONCHAINKIT INTEGRATION ENDPOINTS
# =============================================================================

@router.post("/onchain/create-charge")
async def create_onchain_charge(request: Request):
    """
    Create a charge for OnchainKit Checkout component.
    
    This endpoint is called by the chargeHandler prop in the frontend
    Checkout component to dynamically create charges.
    
    Expected body:
    {
        "type": "bet" | "intel" | "deposit",
        "user_id": "...",
        ... (type-specific fields)
    }
    
    Returns:
    {
        "id": "charge_id_to_pass_to_checkout"
    }
    """
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    charge_type = body.get("type")
    user_id = body.get("user_id")
    
    if not charge_type or not user_id:
        raise HTTPException(status_code=400, detail="Missing type or user_id")
    
    client = get_commerce_client()
    
    try:
        if charge_type == "bet":
            charge = await client.create_market_bet_charge(
                user_id=user_id,
                market_id=body.get("market_id", ""),
                market_title=body.get("market_title", "Market Bet"),
                outcome=body.get("outcome", ""),
                shares=float(body.get("shares", 1)),
                price_per_share=float(body.get("price_per_share", 0.5))
            )
        
        elif charge_type == "intel":
            charge = await client.create_intel_access_charge(
                user_id=user_id,
                intel_tier=body.get("intel_tier", "basic"),
                market_id=body.get("market_id")
            )
        
        elif charge_type == "deposit":
            charge = await client.create_deposit_charge(
                user_id=user_id,
                amount=float(body.get("amount", 10))
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown charge type: {charge_type}")
        
        # OnchainKit expects just the charge ID
        return {"id": charge.id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/onchain/verify-charge/{charge_id}")
async def verify_onchain_charge(charge_id: str):
    """
    Verify a charge status for OnchainKit.
    
    Called after payment to confirm success.
    """
    client = get_commerce_client()
    
    try:
        charge = await client.get_charge(charge_id)
        
        return {
            "charge_id": charge.id,
            "status": charge.status.value,
            "is_paid": charge.status.value == "COMPLETED",
            "amount": charge.amount,
            "currency": charge.currency,
            "metadata": charge.metadata.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def payments_health():
    """Check if the payments system is operational"""
    client = get_commerce_client()
    
    return {
        "status": "ok",
        "api_key_configured": bool(client.config.api_key),
        "webhook_secret_configured": bool(client.config.webhook_secret),
        "settlement_wallet": client.config.settlement_wallet[:10] + "..." if client.config.settlement_wallet else None
    }
