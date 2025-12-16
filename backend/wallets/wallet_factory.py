"""
Multi-Chain Wallet Factory
==========================

Creates and manages wallets for AI agents across multiple chains:
- Base: Agent identity via Virtuals Protocol (ERC-6551)
- Polygon: Polymarket trading via Gnosis Safe
- Solana: Kalshi trading via programmatic keypairs

Implements the "Sandwich Architecture" where:
- Brain (intelligence) is separate from Body (wallet/execution)
- Each agent has coordinated wallets across chains
- x402 protocol for autonomous micropayments

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class Chain(str, Enum):
    """Supported blockchain networks."""
    BASE = "base"
    BASE_SEPOLIA = "base_sepolia"
    POLYGON = "polygon"
    POLYGON_MUMBAI = "polygon_mumbai"
    SOLANA = "solana"
    SOLANA_DEVNET = "solana_devnet"


class WalletType(str, Enum):
    """Types of wallets."""
    EOA = "eoa"                     # Externally Owned Account
    ERC6551 = "erc6551"             # Token Bound Account (Virtuals)
    GNOSIS_SAFE = "gnosis_safe"     # Multi-sig Safe
    SOLANA_KEYPAIR = "solana_keypair"  # Solana programmatic wallet


class WalletStatus(str, Enum):
    """Wallet lifecycle status."""
    PENDING = "pending"
    ACTIVE = "active"
    LOCKED = "locked"
    DEPRECATED = "deprecated"


# =============================================================================
# CONFIGURATION
# =============================================================================

class ChainConfig(BaseModel):
    """Configuration for a blockchain network."""
    
    chain: Chain
    chain_id: int
    rpc_url: str
    explorer_url: str
    
    # Token addresses
    native_token: str = Field("ETH", description="Native token symbol")
    usdc_address: Optional[str] = Field(None)
    
    # Contract addresses
    safe_factory: Optional[str] = Field(None)
    erc6551_registry: Optional[str] = Field(None)
    erc6551_implementation: Optional[str] = Field(None)
    
    # Gas settings
    default_gas_limit: int = Field(200000)
    max_priority_fee_gwei: int = Field(2)


# Default configurations
CHAIN_CONFIGS = {
    Chain.BASE: ChainConfig(
        chain=Chain.BASE,
        chain_id=8453,
        rpc_url="https://mainnet.base.org",
        explorer_url="https://basescan.org",
        native_token="ETH",
        usdc_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        erc6551_registry="0x000000006551c19487814612e58FE06813775758",
        erc6551_implementation="0x55266d75D1a14E4572138116aF39863Ed6596E7F",
    ),
    Chain.BASE_SEPOLIA: ChainConfig(
        chain=Chain.BASE_SEPOLIA,
        chain_id=84532,
        rpc_url="https://sepolia.base.org",
        explorer_url="https://sepolia.basescan.org",
        native_token="ETH",
        usdc_address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        erc6551_registry="0x000000006551c19487814612e58FE06813775758",
        erc6551_implementation="0x55266d75D1a14E4572138116aF39863Ed6596E7F",
    ),
    Chain.POLYGON: ChainConfig(
        chain=Chain.POLYGON,
        chain_id=137,
        rpc_url="https://polygon-rpc.com",
        explorer_url="https://polygonscan.com",
        native_token="MATIC",
        usdc_address="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        safe_factory="0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2",
    ),
    Chain.POLYGON_MUMBAI: ChainConfig(
        chain=Chain.POLYGON_MUMBAI,
        chain_id=80001,
        rpc_url="https://rpc-mumbai.maticvigil.com",
        explorer_url="https://mumbai.polygonscan.com",
        native_token="MATIC",
        usdc_address="0xe11A86849d99F524cAC3E7A0Ec1241828e332C62",
        safe_factory="0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2",
    ),
    Chain.SOLANA: ChainConfig(
        chain=Chain.SOLANA,
        chain_id=0,  # Solana doesn't use chain IDs
        rpc_url="https://api.mainnet-beta.solana.com",
        explorer_url="https://solscan.io",
        native_token="SOL",
    ),
    Chain.SOLANA_DEVNET: ChainConfig(
        chain=Chain.SOLANA_DEVNET,
        chain_id=0,
        rpc_url="https://api.devnet.solana.com",
        explorer_url="https://solscan.io?cluster=devnet",
        native_token="SOL",
    ),
}


# =============================================================================
# WALLET MODELS
# =============================================================================

class WalletCredentials(BaseModel):
    """Secure wallet credentials (encrypted in production)."""
    
    # For EOA/ERC6551
    private_key: Optional[str] = Field(None, description="Encrypted private key")
    mnemonic: Optional[str] = Field(None, description="Encrypted mnemonic")
    derivation_path: Optional[str] = Field(None)
    
    # For Gnosis Safe
    safe_owners: list[str] = Field(default_factory=list)
    safe_threshold: int = Field(1)
    
    # For Solana
    solana_secret_key: Optional[str] = Field(None, description="Base58 encoded secret")
    
    # Encryption metadata
    encryption_version: str = Field("v1")
    encrypted_at: datetime = Field(default_factory=datetime.utcnow)


class WalletBalance(BaseModel):
    """Wallet balance information."""
    
    native_balance: Decimal = Field(Decimal("0"))
    usdc_balance: Decimal = Field(Decimal("0"))
    
    # Additional tokens
    token_balances: dict[str, Decimal] = Field(default_factory=dict)
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ChainWallet(BaseModel):
    """Wallet on a specific chain."""
    
    wallet_id: str = Field(..., description="Unique wallet identifier")
    
    chain: Chain = Field(...)
    wallet_type: WalletType = Field(...)
    
    address: str = Field(..., description="Wallet address")
    
    status: WalletStatus = Field(WalletStatus.PENDING)
    
    # Credentials (stored separately in production)
    credentials_id: Optional[str] = Field(None)
    
    # Balance cache
    balance: WalletBalance = Field(default_factory=WalletBalance)
    
    # Transaction tracking
    nonce: int = Field(0)
    total_transactions: int = Field(0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = Field(None)
    
    # For ERC6551
    bound_token_contract: Optional[str] = Field(None)
    bound_token_id: Optional[str] = Field(None)
    
    # For Gnosis Safe
    safe_version: Optional[str] = Field(None)


class AgentWalletSet(BaseModel):
    """Complete set of wallets for an agent across all chains."""
    
    agent_id: str = Field(..., description="Agent this wallet set belongs to")
    
    # Primary identity wallet (Base/Virtuals)
    identity_wallet: Optional[ChainWallet] = Field(None)
    
    # Trading wallets
    polymarket_wallet: Optional[ChainWallet] = Field(None)  # Polygon
    kalshi_wallet: Optional[ChainWallet] = Field(None)      # Solana
    
    # Additional wallets
    auxiliary_wallets: list[ChainWallet] = Field(default_factory=list)
    
    # x402 payment configuration
    x402_enabled: bool = Field(True)
    x402_spending_limit_daily: Decimal = Field(Decimal("100"))  # USDC
    x402_spent_today: Decimal = Field(Decimal("0"))
    
    # Bridging state
    pending_bridges: list[dict] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# WALLET FACTORY
# =============================================================================

class MultiChainWalletFactory:
    """
    Factory for creating and managing multi-chain agent wallets.
    
    Architecture:
    - Each agent gets a coordinated set of wallets
    - Identity lives on Base (ERC-6551 via Virtuals)
    - Trading happens on Polygon (Polymarket) and Solana (Kalshi)
    - Wallets are linked via deterministic derivation
    """
    
    def __init__(
        self,
        master_seed: Optional[str] = None,
        use_testnet: bool = True,
        encryption_key: Optional[str] = None
    ):
        self.master_seed = master_seed or secrets.token_hex(32)
        self.use_testnet = use_testnet
        self.encryption_key = encryption_key
        
        # Select chains based on testnet flag
        if use_testnet:
            self.base_chain = Chain.BASE_SEPOLIA
            self.polygon_chain = Chain.POLYGON_MUMBAI
            self.solana_chain = Chain.SOLANA_DEVNET
        else:
            self.base_chain = Chain.BASE
            self.polygon_chain = Chain.POLYGON
            self.solana_chain = Chain.SOLANA
        
        # Storage
        self._wallet_sets: dict[str, AgentWalletSet] = {}
        self._credentials: dict[str, WalletCredentials] = {}
        self._wallets: dict[str, ChainWallet] = {}
    
    # =========================================================================
    # WALLET SET CREATION
    # =========================================================================
    
    async def create_agent_wallet_set(
        self,
        agent_id: str,
        agent_token_contract: Optional[str] = None,
        agent_token_id: Optional[str] = None,
        create_identity: bool = True,
        create_polymarket: bool = True,
        create_kalshi: bool = True
    ) -> AgentWalletSet:
        """
        Create a complete wallet set for an agent.
        
        Uses HD derivation from master seed for coordinated wallets:
        - m/44'/60'/0'/0/{agent_index} for EVM chains
        - Separate derivation for Solana
        """
        # Generate agent-specific seed
        agent_seed = self._derive_agent_seed(agent_id)
        
        wallet_set = AgentWalletSet(agent_id=agent_id)
        
        # Create identity wallet on Base (ERC-6551)
        if create_identity:
            identity_wallet = await self._create_identity_wallet(
                agent_id=agent_id,
                agent_seed=agent_seed,
                token_contract=agent_token_contract,
                token_id=agent_token_id
            )
            wallet_set.identity_wallet = identity_wallet
        
        # Create Polymarket wallet on Polygon (Gnosis Safe)
        if create_polymarket:
            polymarket_wallet = await self._create_polymarket_wallet(
                agent_id=agent_id,
                agent_seed=agent_seed
            )
            wallet_set.polymarket_wallet = polymarket_wallet
        
        # Create Kalshi wallet on Solana
        if create_kalshi:
            kalshi_wallet = await self._create_kalshi_wallet(
                agent_id=agent_id,
                agent_seed=agent_seed
            )
            wallet_set.kalshi_wallet = kalshi_wallet
        
        self._wallet_sets[agent_id] = wallet_set
        
        return wallet_set
    
    async def _create_identity_wallet(
        self,
        agent_id: str,
        agent_seed: str,
        token_contract: Optional[str] = None,
        token_id: Optional[str] = None
    ) -> ChainWallet:
        """Create ERC-6551 identity wallet on Base."""
        wallet_id = f"identity_{agent_id}"
        
        # Derive address from seed
        address = self._derive_evm_address(agent_seed, 0)
        
        # Create credentials
        credentials = WalletCredentials(
            private_key=self._derive_private_key(agent_seed, 0),
            derivation_path="m/44'/60'/0'/0/0"
        )
        self._credentials[wallet_id] = credentials
        
        wallet = ChainWallet(
            wallet_id=wallet_id,
            chain=self.base_chain,
            wallet_type=WalletType.ERC6551 if token_contract else WalletType.EOA,
            address=address,
            status=WalletStatus.PENDING,
            credentials_id=wallet_id,
            bound_token_contract=token_contract,
            bound_token_id=token_id
        )
        
        self._wallets[wallet_id] = wallet
        
        return wallet
    
    async def _create_polymarket_wallet(
        self,
        agent_id: str,
        agent_seed: str
    ) -> ChainWallet:
        """Create Gnosis Safe wallet on Polygon for Polymarket trading."""
        wallet_id = f"polymarket_{agent_id}"
        
        # For Gnosis Safe, we need an owner EOA first
        owner_address = self._derive_evm_address(agent_seed, 1)
        
        # Safe address is deterministically computed
        # In production, this would call the Safe factory
        safe_address = self._compute_safe_address(owner_address, agent_id)
        
        # Create credentials
        credentials = WalletCredentials(
            private_key=self._derive_private_key(agent_seed, 1),
            derivation_path="m/44'/60'/0'/0/1",
            safe_owners=[owner_address],
            safe_threshold=1
        )
        self._credentials[wallet_id] = credentials
        
        wallet = ChainWallet(
            wallet_id=wallet_id,
            chain=self.polygon_chain,
            wallet_type=WalletType.GNOSIS_SAFE,
            address=safe_address,
            status=WalletStatus.PENDING,
            credentials_id=wallet_id,
            safe_version="1.3.0"
        )
        
        self._wallets[wallet_id] = wallet
        
        return wallet
    
    async def _create_kalshi_wallet(
        self,
        agent_id: str,
        agent_seed: str
    ) -> ChainWallet:
        """Create Solana wallet for Kalshi trading."""
        wallet_id = f"kalshi_{agent_id}"
        
        # Derive Solana keypair
        solana_address, solana_secret = self._derive_solana_keypair(agent_seed)
        
        # Create credentials
        credentials = WalletCredentials(
            solana_secret_key=solana_secret
        )
        self._credentials[wallet_id] = credentials
        
        wallet = ChainWallet(
            wallet_id=wallet_id,
            chain=self.solana_chain,
            wallet_type=WalletType.SOLANA_KEYPAIR,
            address=solana_address,
            status=WalletStatus.PENDING,
            credentials_id=wallet_id
        )
        
        self._wallets[wallet_id] = wallet
        
        return wallet
    
    # =========================================================================
    # KEY DERIVATION
    # =========================================================================
    
    def _derive_agent_seed(self, agent_id: str) -> str:
        """Derive agent-specific seed from master seed."""
        data = f"{self.master_seed}:{agent_id}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _derive_evm_address(self, agent_seed: str, index: int) -> str:
        """Derive EVM address from seed and index."""
        # In production, use proper HD derivation (BIP-32/BIP-44)
        # This is a simplified deterministic derivation for demo
        data = f"{agent_seed}:evm:{index}"
        hash_bytes = hashlib.sha256(data.encode()).digest()
        
        # Take last 20 bytes as address
        address_bytes = hash_bytes[-20:]
        return "0x" + address_bytes.hex()
    
    def _derive_private_key(self, agent_seed: str, index: int) -> str:
        """Derive private key from seed and index."""
        # In production, use proper HD derivation
        data = f"{agent_seed}:privkey:{index}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _derive_solana_keypair(self, agent_seed: str) -> tuple[str, str]:
        """Derive Solana keypair from seed."""
        # In production, use proper Ed25519 derivation
        data = f"{agent_seed}:solana"
        seed_bytes = hashlib.sha256(data.encode()).digest()
        
        # Simplified - in production use nacl/ed25519
        # Address is base58 encoded public key
        import base64
        address = base64.b64encode(seed_bytes[:32]).decode()[:44]
        secret = base64.b64encode(seed_bytes).decode()
        
        return address, secret
    
    def _compute_safe_address(self, owner: str, salt: str) -> str:
        """Compute deterministic Safe address."""
        # In production, this would use Safe's CREATE2 address computation
        data = f"safe:{owner}:{salt}"
        hash_bytes = hashlib.sha256(data.encode()).digest()
        return "0x" + hash_bytes[-20:].hex()
    
    # =========================================================================
    # WALLET ACTIVATION
    # =========================================================================
    
    async def activate_wallet(self, wallet_id: str) -> ChainWallet:
        """
        Activate a wallet by deploying necessary contracts.
        
        For different wallet types:
        - EOA: Just mark as active
        - ERC6551: Deploy token bound account
        - Gnosis Safe: Deploy Safe contract
        - Solana: Fund account to create it
        """
        wallet = self._wallets.get(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")
        
        if wallet.status == WalletStatus.ACTIVE:
            return wallet
        
        if wallet.wallet_type == WalletType.EOA:
            # EOA just needs funding
            wallet.status = WalletStatus.ACTIVE
            
        elif wallet.wallet_type == WalletType.ERC6551:
            # Deploy token bound account
            # In production: call ERC6551Registry.createAccount()
            wallet.status = WalletStatus.ACTIVE
            
        elif wallet.wallet_type == WalletType.GNOSIS_SAFE:
            # Deploy Safe
            # In production: call SafeProxyFactory.createProxyWithNonce()
            wallet.status = WalletStatus.ACTIVE
            
        elif wallet.wallet_type == WalletType.SOLANA_KEYPAIR:
            # Fund to create account
            # In production: transfer SOL to activate
            wallet.status = WalletStatus.ACTIVE
        
        return wallet
    
    async def activate_wallet_set(self, agent_id: str) -> AgentWalletSet:
        """Activate all wallets in an agent's wallet set."""
        wallet_set = self._wallet_sets.get(agent_id)
        if not wallet_set:
            raise ValueError(f"Wallet set not found for agent: {agent_id}")
        
        if wallet_set.identity_wallet:
            await self.activate_wallet(wallet_set.identity_wallet.wallet_id)
        
        if wallet_set.polymarket_wallet:
            await self.activate_wallet(wallet_set.polymarket_wallet.wallet_id)
        
        if wallet_set.kalshi_wallet:
            await self.activate_wallet(wallet_set.kalshi_wallet.wallet_id)
        
        return wallet_set
    
    # =========================================================================
    # BALANCE MANAGEMENT
    # =========================================================================
    
    async def get_wallet_balance(self, wallet_id: str) -> WalletBalance:
        """Fetch current balance for a wallet."""
        wallet = self._wallets.get(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")
        
        config = CHAIN_CONFIGS.get(wallet.chain)
        if not config:
            raise ValueError(f"Unknown chain: {wallet.chain}")
        
        # In production, this would call the actual RPC
        # For now, return cached balance
        
        return wallet.balance
    
    async def get_agent_total_balance(self, agent_id: str) -> dict[str, Decimal]:
        """Get total balance across all agent wallets."""
        wallet_set = self._wallet_sets.get(agent_id)
        if not wallet_set:
            raise ValueError(f"Wallet set not found: {agent_id}")
        
        total = {
            "native_eth": Decimal("0"),
            "native_matic": Decimal("0"),
            "native_sol": Decimal("0"),
            "usdc": Decimal("0"),
        }
        
        for wallet in [wallet_set.identity_wallet, wallet_set.polymarket_wallet]:
            if wallet:
                balance = await self.get_wallet_balance(wallet.wallet_id)
                if wallet.chain in [Chain.BASE, Chain.BASE_SEPOLIA]:
                    total["native_eth"] += balance.native_balance
                elif wallet.chain in [Chain.POLYGON, Chain.POLYGON_MUMBAI]:
                    total["native_matic"] += balance.native_balance
                total["usdc"] += balance.usdc_balance
        
        if wallet_set.kalshi_wallet:
            balance = await self.get_wallet_balance(wallet_set.kalshi_wallet.wallet_id)
            total["native_sol"] += balance.native_balance
        
        return total
    
    # =========================================================================
    # x402 PROTOCOL
    # =========================================================================
    
    async def check_x402_allowance(
        self,
        agent_id: str,
        amount: Decimal
    ) -> bool:
        """Check if agent can spend amount via x402."""
        wallet_set = self._wallet_sets.get(agent_id)
        if not wallet_set:
            return False
        
        if not wallet_set.x402_enabled:
            return False
        
        remaining = wallet_set.x402_spending_limit_daily - wallet_set.x402_spent_today
        return amount <= remaining
    
    async def record_x402_payment(
        self,
        agent_id: str,
        amount: Decimal,
        recipient: str,
        purpose: str
    ) -> bool:
        """Record an x402 micropayment."""
        wallet_set = self._wallet_sets.get(agent_id)
        if not wallet_set:
            return False
        
        if not await self.check_x402_allowance(agent_id, amount):
            return False
        
        wallet_set.x402_spent_today += amount
        
        # In production, execute actual transaction
        
        return True
    
    async def reset_daily_x402_limits(self):
        """Reset daily x402 spending limits (called daily)."""
        for wallet_set in self._wallet_sets.values():
            wallet_set.x402_spent_today = Decimal("0")
    
    # =========================================================================
    # CROSS-CHAIN BRIDGING
    # =========================================================================
    
    async def initiate_bridge(
        self,
        agent_id: str,
        from_chain: Chain,
        to_chain: Chain,
        token: str,
        amount: Decimal
    ) -> dict:
        """
        Initiate cross-chain bridge transfer.
        
        Uses CCIP (Chainlink) or Wormhole depending on chains.
        """
        wallet_set = self._wallet_sets.get(agent_id)
        if not wallet_set:
            raise ValueError(f"Wallet set not found: {agent_id}")
        
        bridge_id = hashlib.sha256(
            f"{agent_id}:{from_chain}:{to_chain}:{amount}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        bridge_request = {
            "bridge_id": bridge_id,
            "agent_id": agent_id,
            "from_chain": from_chain.value,
            "to_chain": to_chain.value,
            "token": token,
            "amount": str(amount),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        wallet_set.pending_bridges.append(bridge_request)
        
        # In production, this would:
        # 1. Lock funds on source chain
        # 2. Submit to bridge protocol
        # 3. Wait for confirmation
        # 4. Mint/release on destination
        
        return bridge_request
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    async def get_wallet_set(self, agent_id: str) -> Optional[AgentWalletSet]:
        """Get wallet set for an agent."""
        return self._wallet_sets.get(agent_id)
    
    async def get_wallet(self, wallet_id: str) -> Optional[ChainWallet]:
        """Get a specific wallet."""
        return self._wallets.get(wallet_id)
    
    async def get_wallet_by_address(
        self,
        address: str,
        chain: Optional[Chain] = None
    ) -> Optional[ChainWallet]:
        """Find wallet by address."""
        for wallet in self._wallets.values():
            if wallet.address.lower() == address.lower():
                if chain is None or wallet.chain == chain:
                    return wallet
        return None
    
    async def list_agent_wallets(self, agent_id: str) -> list[ChainWallet]:
        """List all wallets for an agent."""
        wallet_set = self._wallet_sets.get(agent_id)
        if not wallet_set:
            return []
        
        wallets = []
        if wallet_set.identity_wallet:
            wallets.append(wallet_set.identity_wallet)
        if wallet_set.polymarket_wallet:
            wallets.append(wallet_set.polymarket_wallet)
        if wallet_set.kalshi_wallet:
            wallets.append(wallet_set.kalshi_wallet)
        wallets.extend(wallet_set.auxiliary_wallets)
        
        return wallets


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def example_usage():
    """Example usage of wallet factory."""
    
    factory = MultiChainWalletFactory(
        use_testnet=True
    )
    
    # Create wallet set for an agent
    wallet_set = await factory.create_agent_wallet_set(
        agent_id="SHARK_001",
        agent_token_contract="0xVirtualsContract",
        agent_token_id="12345"
    )
    
    print(f"Created wallet set for agent: {wallet_set.agent_id}")
    
    if wallet_set.identity_wallet:
        print(f"Identity (Base Sepolia): {wallet_set.identity_wallet.address}")
    
    if wallet_set.polymarket_wallet:
        print(f"Polymarket (Polygon Mumbai): {wallet_set.polymarket_wallet.address}")
    
    if wallet_set.kalshi_wallet:
        print(f"Kalshi (Solana Devnet): {wallet_set.kalshi_wallet.address}")
    
    # Activate wallets
    await factory.activate_wallet_set("SHARK_001")
    print("Wallets activated!")
    
    # Check x402 allowance
    can_spend = await factory.check_x402_allowance("SHARK_001", Decimal("50"))
    print(f"Can spend $50 via x402: {can_spend}")
    
    # Record payment
    await factory.record_x402_payment(
        agent_id="SHARK_001",
        amount=Decimal("10"),
        recipient="0xSpyAgent",
        purpose="intel_purchase"
    )
    print("x402 payment recorded")
    
    # Get total balance
    total = await factory.get_agent_total_balance("SHARK_001")
    print(f"Total balances: {total}")


if __name__ == "__main__":
    asyncio.run(example_usage())
