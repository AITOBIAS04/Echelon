"""
Coinbase Commerce API Integration for Pizzint Prediction Market
===============================================================
Handles USDC stablecoin payments on Base network for:
- Buying prediction market shares
- Intel access payments (x402)
- Withdrawals to user wallets

Uses Coinbase Commerce API with OnChain Payment Protocol for:
- No gas fees (sponsored by Coinbase)
- Instant settlement on Base L2
- Multi-currency support (converts to USDC)

API Docs: https://docs.cdp.coinbase.com/commerce/introduction/welcome
"""
import os
import hmac
import hashlib
import json
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import aiohttp

# =============================================================================
# CONFIGURATION
# =============================================================================

class PaymentNetwork(Enum):
    """Supported blockchain networks for payments"""
    BASE = "base"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"

class PaymentStatus(Enum):
    """Charge payment status"""
    NEW = "NEW"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"
    CANCELED = "CANCELED"
    REFUND_PENDING = "REFUND_PENDING"
    REFUNDED = "REFUNDED"

class ChargeType(Enum):
    """Types of charges in our system"""
    MARKET_BET = "market_bet"
    INTEL_ACCESS = "intel_access"
    DEPOSIT = "deposit"
    SUBSCRIPTION = "subscription"

@dataclass
class CommerceConfig:
    """Coinbase Commerce configuration"""
    api_key: str = field(default_factory=lambda: os.getenv("COINBASE_COMMERCE_API_KEY", ""))
    webhook_secret: str = field(default_factory=lambda: os.getenv("COINBASE_WEBHOOK_SECRET", ""))
    api_base_url: str = "https://api.commerce.coinbase.com"
    default_currency: str = "USD"
    default_crypto: str = "USDC"
    preferred_network: PaymentNetwork = PaymentNetwork.BASE
    charge_expiry_minutes: int = 60
    
    # Settlement wallet (receives all payments)
    settlement_wallet: str = field(default_factory=lambda: os.getenv(
        "SETTLEMENT_WALLET_ADDRESS",
        "0x0000000000000000000000000000000000000000"  # Replace with actual
    ))

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ChargeMetadata:
    """Metadata attached to each charge"""
    charge_type: ChargeType
    user_id: str
    market_id: Optional[str] = None
    outcome: Optional[str] = None
    shares: Optional[float] = None
    intel_tier: Optional[str] = None
    internal_ref: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to flat dict for API (all values must be strings)"""
        return {
            "charge_type": self.charge_type.value,
            "user_id": self.user_id,
            "market_id": self.market_id or "",
            "outcome": self.outcome or "",
            "shares": str(self.shares) if self.shares else "",
            "intel_tier": self.intel_tier or "",
            "internal_ref": self.internal_ref or str(uuid.uuid4()),
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ChargeMetadata":
        """Reconstruct from API response"""
        return cls(
            charge_type=ChargeType(data.get("charge_type", "deposit")),
            user_id=data.get("user_id", ""),
            market_id=data.get("market_id") or None,
            outcome=data.get("outcome") or None,
            shares=float(data["shares"]) if data.get("shares") else None,
            intel_tier=data.get("intel_tier") or None,
            internal_ref=data.get("internal_ref"),
            created_at=data.get("created_at", "")
        )

@dataclass
class Charge:
    """Represents a Commerce charge"""
    id: str
    code: str
    name: str
    description: str
    amount: float
    currency: str
    status: PaymentStatus
    hosted_url: str
    created_at: datetime
    expires_at: datetime
    metadata: ChargeMetadata
    pricing: Dict[str, Any] = field(default_factory=dict)
    payments: List[Dict[str, Any]] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "hosted_url": self.hosted_url,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata.to_dict(),
            "is_expired": datetime.now(timezone.utc) > self.expires_at,
            "is_paid": self.status == PaymentStatus.COMPLETED
        }
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Charge":
        """Parse from Coinbase Commerce API response"""
        return cls(
            id=data["id"],
            code=data.get("code", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            amount=float(data.get("pricing", {}).get("local", {}).get("amount", 0)),
            currency=data.get("pricing", {}).get("local", {}).get("currency", "USD"),
            status=PaymentStatus(data.get("timeline", [{}])[-1].get("status", "NEW")),
            hosted_url=data.get("hosted_url", ""),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")),
            metadata=ChargeMetadata.from_dict(data.get("metadata", {})),
            pricing=data.get("pricing", {}),
            payments=data.get("payments", []),
            timeline=data.get("timeline", [])
        )

@dataclass
class WebhookEvent:
    """Parsed webhook event from Coinbase Commerce"""
    id: str
    type: str
    api_version: str
    created_at: datetime
    charge: Charge
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "WebhookEvent":
        event_data = payload.get("event", payload)
        return cls(
            id=event_data.get("id", ""),
            type=event_data.get("type", ""),
            api_version=event_data.get("api_version", ""),
            created_at=datetime.fromisoformat(
                event_data.get("created_at", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")
            ),
            charge=Charge.from_api_response(event_data.get("data", {}))
        )

# =============================================================================
# COINBASE COMMERCE CLIENT
# =============================================================================

class CoinbaseCommerceClient:
    """
    Async client for Coinbase Commerce API
    
    Features:
    - Create charges for market bets
    - Create charges for intel access
    - Verify webhook signatures
    - Check payment status
    - Handle refunds
    """
    
    def __init__(self, config: Optional[CommerceConfig] = None):
        self.config = config or CommerceConfig()
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-CC-Api-Key": self.config.api_key,
                    "X-CC-Version": "2018-03-22"
                }
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    # -------------------------------------------------------------------------
    # CHARGE CREATION
    # -------------------------------------------------------------------------
    
    async def create_charge(
        self,
        name: str,
        description: str,
        amount: float,
        metadata: ChargeMetadata,
        currency: str = "USD",
        redirect_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Charge:
        """
        Create a new charge for payment
        
        Args:
            name: Display name for the charge
            description: Description shown to user
            amount: Amount in specified currency
            metadata: Our internal tracking data
            currency: Fiat currency (default USD)
            redirect_url: URL to redirect after success
            cancel_url: URL to redirect on cancel
        
        Returns:
            Charge object with hosted_url for checkout
        """
        session = await self._get_session()
        
        payload = {
            "name": name,
            "description": description,
            "pricing_type": "fixed_price",
            "local_price": {
                "amount": str(amount),
                "currency": currency
            },
            "metadata": metadata.to_dict()
        }
        
        if redirect_url:
            payload["redirect_url"] = redirect_url
        if cancel_url:
            payload["cancel_url"] = cancel_url
        
        async with session.post(
            f"{self.config.api_base_url}/charges",
            json=payload
        ) as resp:
            if resp.status != 201:
                error_text = await resp.text()
                raise Exception(f"Failed to create charge: {resp.status} - {error_text}")
            
            data = await resp.json()
            return Charge.from_api_response(data.get("data", data))
    
    async def create_market_bet_charge(
        self,
        user_id: str,
        market_id: str,
        market_title: str,
        outcome: str,
        shares: float,
        price_per_share: float,
        redirect_url: Optional[str] = None
    ) -> Charge:
        """
        Create a charge for buying prediction market shares
        
        Args:
            user_id: User making the bet
            market_id: Market being bet on
            market_title: Human readable market name
            outcome: Selected outcome (YES/NO/etc)
            shares: Number of shares to buy
            price_per_share: Current price per share
            redirect_url: Where to redirect after payment
        
        Returns:
            Charge for the bet amount
        """
        total_amount = round(shares * price_per_share, 2)
        
        metadata = ChargeMetadata(
            charge_type=ChargeType.MARKET_BET,
            user_id=user_id,
            market_id=market_id,
            outcome=outcome,
            shares=shares
        )
        
        return await self.create_charge(
            name=f"Bet: {outcome} on {market_title[:50]}",
            description=f"Purchase {shares} shares of {outcome} @ ${price_per_share:.2f} each",
            amount=total_amount,
            metadata=metadata,
            redirect_url=redirect_url
        )
    
    async def create_intel_access_charge(
        self,
        user_id: str,
        intel_tier: str,
        market_id: Optional[str] = None,
        redirect_url: Optional[str] = None
    ) -> Charge:
        """
        Create a charge for intel/research access (x402 payment gate)
        
        Tiers:
        - basic: $1 - See additional context
        - premium: $5 - Full analysis + source data
        - alpha: $25 - Real-time updates + alerts
        """
        tier_pricing = {
            "basic": (1.00, "Basic Intel Access"),
            "premium": (5.00, "Premium Analysis"),
            "alpha": (25.00, "Alpha Intelligence")
        }
        
        amount, tier_name = tier_pricing.get(intel_tier, (1.00, "Intel Access"))
        
        metadata = ChargeMetadata(
            charge_type=ChargeType.INTEL_ACCESS,
            user_id=user_id,
            intel_tier=intel_tier,
            market_id=market_id
        )
        
        return await self.create_charge(
            name=f"🔒 {tier_name}",
            description=f"Unlock {intel_tier} intelligence tier for enhanced market insights",
            amount=amount,
            metadata=metadata,
            redirect_url=redirect_url
        )
    
    async def create_deposit_charge(
        self,
        user_id: str,
        amount: float,
        redirect_url: Optional[str] = None
    ) -> Charge:
        """
        Create a charge for depositing funds to user's balance
        """
        metadata = ChargeMetadata(
            charge_type=ChargeType.DEPOSIT,
            user_id=user_id
        )
        
        return await self.create_charge(
            name="💰 Deposit Funds",
            description=f"Add ${amount:.2f} to your Pizzint balance",
            amount=amount,
            metadata=metadata,
            redirect_url=redirect_url
        )
    
    # -------------------------------------------------------------------------
    # CHARGE RETRIEVAL
    # -------------------------------------------------------------------------
    
    async def get_charge(self, charge_id: str) -> Charge:
        """Retrieve a charge by ID"""
        session = await self._get_session()
        
        async with session.get(
            f"{self.config.api_base_url}/charges/{charge_id}"
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Failed to get charge: {resp.status} - {error_text}")
            
            data = await resp.json()
            return Charge.from_api_response(data.get("data", data))
    
    async def get_charge_by_code(self, code: str) -> Charge:
        """Retrieve a charge by its short code"""
        return await self.get_charge(code)
    
    async def list_charges(
        self,
        limit: int = 25,
        start_after: Optional[str] = None
    ) -> List[Charge]:
        """List all charges with pagination"""
        session = await self._get_session()
        
        params = {"limit": limit}
        if start_after:
            params["starting_after"] = start_after
        
        async with session.get(
            f"{self.config.api_base_url}/charges",
            params=params
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Failed to list charges: {resp.status} - {error_text}")
            
            data = await resp.json()
            return [Charge.from_api_response(c) for c in data.get("data", [])]
    
    async def cancel_charge(self, charge_id: str) -> Charge:
        """Cancel a pending charge"""
        session = await self._get_session()
        
        async with session.post(
            f"{self.config.api_base_url}/charges/{charge_id}/cancel"
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Failed to cancel charge: {resp.status} - {error_text}")
            
            data = await resp.json()
            return Charge.from_api_response(data.get("data", data))
    
    # -------------------------------------------------------------------------
    # WEBHOOK VERIFICATION
    # -------------------------------------------------------------------------
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Verify that a webhook came from Coinbase Commerce
        
        Args:
            payload: Raw request body bytes
            signature: X-CC-Webhook-Signature header
        
        Returns:
            True if signature is valid
        """
        if not self.config.webhook_secret:
            print("⚠️ No webhook secret configured - skipping verification")
            return True
        
        expected = hmac.new(
            self.config.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    def parse_webhook(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse a webhook payload into a WebhookEvent"""
        return WebhookEvent.from_payload(payload)

# =============================================================================
# PAYMENT HANDLER
# =============================================================================

class PaymentHandler:
    """
    High-level payment handling for the prediction market
    
    Handles:
    - Processing successful payments
    - Crediting user balances
    - Fulfilling bet orders
    - Granting intel access
    """
    
    def __init__(self, commerce_client: CoinbaseCommerceClient):
        self.client = commerce_client
        
        # In-memory storage (replace with database in production)
        self._user_balances: Dict[str, float] = {}
        self._pending_bets: Dict[str, Dict[str, Any]] = {}
        self._intel_access: Dict[str, Dict[str, datetime]] = {}
        self._processed_charges: set = set()
    
    async def handle_webhook_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Process a webhook event from Coinbase Commerce
        
        Event types:
        - charge:created
        - charge:confirmed
        - charge:failed
        - charge:delayed
        - charge:pending
        - charge:resolved
        """
        charge = event.charge
        event_type = event.type
        
        # Prevent double-processing
        if charge.id in self._processed_charges:
            return {"status": "already_processed", "charge_id": charge.id}
        
        result = {"event_type": event_type, "charge_id": charge.id}
        
        if event_type == "charge:confirmed":
            # Payment successful!
            result.update(await self._process_successful_payment(charge))
            self._processed_charges.add(charge.id)
        
        elif event_type == "charge:failed":
            result["status"] = "payment_failed"
            result["message"] = "Payment was not completed"
        
        elif event_type == "charge:pending":
            result["status"] = "payment_pending"
            result["message"] = "Payment is being processed"
        
        elif event_type == "charge:delayed":
            result["status"] = "payment_delayed"
            result["message"] = "Payment is delayed, awaiting confirmation"
        
        return result
    
    async def _process_successful_payment(self, charge: Charge) -> Dict[str, Any]:
        """Process a confirmed payment based on charge type"""
        metadata = charge.metadata
        charge_type = metadata.charge_type
        user_id = metadata.user_id
        
        if charge_type == ChargeType.MARKET_BET:
            return await self._fulfill_market_bet(charge)
        
        elif charge_type == ChargeType.INTEL_ACCESS:
            return await self._grant_intel_access(charge)
        
        elif charge_type == ChargeType.DEPOSIT:
            return await self._credit_deposit(charge)
        
        else:
            return {"status": "unknown_charge_type", "type": charge_type.value}
    
    async def _fulfill_market_bet(self, charge: Charge) -> Dict[str, Any]:
        """Fulfill a market bet order"""
        metadata = charge.metadata
        
        # In production, this would:
        # 1. Create the bet in the database
        # 2. Update market liquidity pool
        # 3. Mint shares to user's wallet
        
        bet_data = {
            "user_id": metadata.user_id,
            "market_id": metadata.market_id,
            "outcome": metadata.outcome,
            "shares": metadata.shares,
            "amount_paid": charge.amount,
            "charge_id": charge.id,
            "fulfilled_at": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"✅ BET FULFILLED: {metadata.user_id} bought {metadata.shares} shares of {metadata.outcome}")
        
        return {
            "status": "bet_fulfilled",
            "bet": bet_data
        }
    
    async def _grant_intel_access(self, charge: Charge) -> Dict[str, Any]:
        """Grant intel tier access to user"""
        metadata = charge.metadata
        user_id = metadata.user_id
        intel_tier = metadata.intel_tier
        
        # Calculate access duration
        tier_durations = {
            "basic": timedelta(hours=24),
            "premium": timedelta(days=7),
            "alpha": timedelta(days=30)
        }
        duration = tier_durations.get(intel_tier, timedelta(hours=24))
        expires_at = datetime.now(timezone.utc) + duration
        
        # Store access
        if user_id not in self._intel_access:
            self._intel_access[user_id] = {}
        self._intel_access[user_id][intel_tier] = expires_at
        
        print(f"🔓 INTEL ACCESS GRANTED: {user_id} -> {intel_tier} until {expires_at}")
        
        return {
            "status": "intel_access_granted",
            "tier": intel_tier,
            "expires_at": expires_at.isoformat()
        }
    
    async def _credit_deposit(self, charge: Charge) -> Dict[str, Any]:
        """Credit deposit to user's balance"""
        user_id = charge.metadata.user_id
        amount = charge.amount
        
        if user_id not in self._user_balances:
            self._user_balances[user_id] = 0.0
        
        self._user_balances[user_id] += amount
        new_balance = self._user_balances[user_id]
        
        print(f"💰 DEPOSIT CREDITED: {user_id} +${amount:.2f} (new balance: ${new_balance:.2f})")
        
        return {
            "status": "deposit_credited",
            "amount": amount,
            "new_balance": new_balance
        }
    
    def check_intel_access(self, user_id: str, intel_tier: str) -> bool:
        """Check if user has active intel access"""
        user_access = self._intel_access.get(user_id, {})
        expires_at = user_access.get(intel_tier)
        
        if expires_at is None:
            return False
        
        return datetime.now(timezone.utc) < expires_at
    
    def get_user_balance(self, user_id: str) -> float:
        """Get user's current balance"""
        return self._user_balances.get(user_id, 0.0)

# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

_commerce_client: Optional[CoinbaseCommerceClient] = None
_payment_handler: Optional[PaymentHandler] = None

def get_commerce_client() -> CoinbaseCommerceClient:
    """Get the singleton Commerce client"""
    global _commerce_client
    if _commerce_client is None:
        _commerce_client = CoinbaseCommerceClient()
    return _commerce_client

def get_payment_handler() -> PaymentHandler:
    """Get the singleton Payment handler"""
    global _payment_handler
    if _payment_handler is None:
        _payment_handler = PaymentHandler(get_commerce_client())
    return _payment_handler

# =============================================================================
# TESTING
# =============================================================================

async def test_commerce_integration():
    """Test the Commerce integration (requires API key)"""
    print("🧪 Testing Coinbase Commerce Integration")
    print("=" * 60)
    
    client = get_commerce_client()
    handler = get_payment_handler()
    
    if not client.config.api_key:
        print("⚠️ No API key set - running in simulation mode")
        
        # Simulate charge creation
        fake_charge = Charge(
            id="test_charge_123",
            code="TESTCODE",
            name="Test Bet",
            description="Test purchase",
            amount=10.00,
            currency="USD",
            status=PaymentStatus.NEW,
            hosted_url="https://commerce.coinbase.com/charges/TESTCODE",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            metadata=ChargeMetadata(
                charge_type=ChargeType.MARKET_BET,
                user_id="user_001",
                market_id="market_123",
                outcome="YES",
                shares=10
            )
        )
        
        print(f"\n📄 Simulated Charge:")
        print(json.dumps(fake_charge.to_dict(), indent=2))
        
        # Simulate webhook processing
        fake_event = WebhookEvent(
            id="event_456",
            type="charge:confirmed",
            api_version="2018-03-22",
            created_at=datetime.now(timezone.utc),
            charge=fake_charge
        )
        
        print(f"\n📨 Processing simulated webhook...")
        result = await handler.handle_webhook_event(fake_event)
        print(f"Result: {json.dumps(result, indent=2)}")
        
        return
    
    # Real API test
    try:
        # Create a test charge
        print("\n📄 Creating test deposit charge...")
        charge = await client.create_deposit_charge(
            user_id="test_user_001",
            amount=1.00,
            redirect_url="https://pizzint.app/payment/success"
        )
        
        print(f"✅ Charge created:")
        print(f"   ID: {charge.id}")
        print(f"   Code: {charge.code}")
        print(f"   URL: {charge.hosted_url}")
        print(f"   Status: {charge.status.value}")
        print(f"   Expires: {charge.expires_at}")
        
        # Retrieve the charge
        print(f"\n🔍 Retrieving charge {charge.id}...")
        retrieved = await client.get_charge(charge.id)
        print(f"   Status: {retrieved.status.value}")
        
        # List recent charges
        print(f"\n📋 Listing recent charges...")
        charges = await client.list_charges(limit=5)
        print(f"   Found {len(charges)} charges")
        for c in charges:
            print(f"   - {c.code}: {c.name} (${c.amount} {c.currency}) [{c.status.value}]")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.close()
    
    print("\n✅ Commerce integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_commerce_integration())




