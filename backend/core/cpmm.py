"""
Constant Product Market Maker (CPMM) for Binary Markets
========================================================

Implements Uniswap-style AMM for prediction markets.

Formula: x * y = k (constant product)
- x = YES shares (liquidity)
- y = NO shares (liquidity)
- k = constant product

Price calculation:
- Price of YES = NO_shares / (YES_shares + NO_shares)
- Price of NO = YES_shares / (YES_shares + NO_shares)

Price impact:
- When buying YES shares, NO shares increase (price goes up)
- Maintains no-arbitrage: YES_price + NO_price = 1.00 (with small spread)

Reference: Uniswap V2 AMM
"""

from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class CPMMState:
    """State of a CPMM market."""
    yes_shares: float  # Liquidity for YES outcome
    no_shares: float   # Liquidity for NO outcome
    
    @property
    def constant_product(self) -> float:
        """Calculate k = x * y"""
        return self.yes_shares * self.no_shares
    
    @property
    def total_liquidity(self) -> float:
        """Total liquidity in the pool"""
        return self.yes_shares + self.no_shares
    
    def get_price(self, outcome: str) -> float:
        """Get current price for an outcome (0.0 to 1.0)"""
        if outcome.upper() == "YES":
            if self.total_liquidity == 0:
                return 0.5  # Default to 50/50 if no liquidity
            return self.no_shares / self.total_liquidity
        elif outcome.upper() == "NO":
            if self.total_liquidity == 0:
                return 0.5
            return self.yes_shares / self.total_liquidity
        else:
            raise ValueError(f"Unknown outcome: {outcome}")
    
    def get_all_prices(self) -> Dict[str, float]:
        """Get prices for all outcomes"""
        return {
            "YES": self.get_price("YES"),
            "NO": self.get_price("NO")
        }
    
    def verify_no_arbitrage(self, tolerance: float = 0.01) -> bool:
        """Verify that YES + NO ≈ 1.00 (within tolerance)"""
        yes_price = self.get_price("YES")
        no_price = self.get_price("NO")
        total = yes_price + no_price
        return abs(total - 1.0) <= tolerance


class CPMM:
    """
    Constant Product Market Maker for binary prediction markets.
    
    Maintains x * y = k where:
    - x = YES shares
    - y = NO shares
    - k = constant product
    """
    
    def __init__(self, initial_liquidity: float = 1000.0):
        """
        Initialize CPMM with equal liquidity for both outcomes.
        
        Args:
            initial_liquidity: Starting liquidity for each outcome (default: 1000)
        """
        self.state = CPMMState(
            yes_shares=initial_liquidity,
            no_shares=initial_liquidity
        )
        self.fee_rate = 0.03  # 3% fee (like Uniswap)
    
    def calculate_shares_out(
        self,
        outcome: str,
        amount_in: float,
        apply_fee: bool = True
    ) -> Tuple[float, float]:
        """
        Calculate how many shares you get for a given amount.
        
        Formula: 
        - For buying YES: amount_in buys YES shares
        - New YES shares = old_YES + amount_in
        - New NO shares = k / new_YES
        - Shares received = new_YES - old_YES
        
        Args:
            outcome: "YES" or "NO"
            amount_in: Amount of capital to invest
            apply_fee: Whether to apply trading fee
        
        Returns:
            Tuple of (shares_out, price_impact)
        """
        if amount_in <= 0:
            return 0.0, 0.0
        
        # Apply fee
        if apply_fee:
            amount_after_fee = amount_in * (1 - self.fee_rate)
        else:
            amount_after_fee = amount_in
        
        k = self.state.constant_product
        
        if outcome.upper() == "YES":
            # Buying YES shares
            old_yes = self.state.yes_shares
            new_yes = old_yes + amount_after_fee
            new_no = k / new_yes if new_yes > 0 else self.state.no_shares
            
            shares_out = new_yes - old_yes
            price_impact = (new_yes / (new_yes + new_no)) - (old_yes / (old_yes + self.state.no_shares))
            
        elif outcome.upper() == "NO":
            # Buying NO shares
            old_no = self.state.no_shares
            new_no = old_no + amount_after_fee
            new_yes = k / new_no if new_no > 0 else self.state.yes_shares
            
            shares_out = new_no - old_no
            price_impact = (new_no / (new_yes + new_no)) - (old_no / (self.state.yes_shares + old_no))
            
        else:
            raise ValueError(f"Unknown outcome: {outcome}")
        
        return shares_out, abs(price_impact)
    
    def calculate_amount_in(
        self,
        outcome: str,
        shares_out: float,
        apply_fee: bool = True
    ) -> float:
        """
        Calculate how much capital is needed to get a certain number of shares.
        
        This is the inverse of calculate_shares_out.
        
        Args:
            outcome: "YES" or "NO"
            shares_out: Desired number of shares
            apply_fee: Whether to account for trading fee
        
        Returns:
            Amount of capital needed
        """
        if shares_out <= 0:
            return 0.0
        
        k = self.state.constant_product
        
        if outcome.upper() == "YES":
            new_yes = self.state.yes_shares + shares_out
            new_no = k / new_yes if new_yes > 0 else self.state.no_shares
            amount_needed = new_yes - self.state.yes_shares
            
        elif outcome.upper() == "NO":
            new_no = self.state.no_shares + shares_out
            new_yes = k / new_no if new_no > 0 else self.state.yes_shares
            amount_needed = new_no - self.state.no_shares
            
        else:
            raise ValueError(f"Unknown outcome: {outcome}")
        
        # Account for fee
        if apply_fee:
            return amount_needed / (1 - self.fee_rate)
        else:
            return amount_needed
    
    def execute_trade(
        self,
        outcome: str,
        amount_in: float,
        apply_fee: bool = True
    ) -> Tuple[float, float, Dict[str, float]]:
        """
        Execute a trade and update the market state.
        
        Args:
            outcome: "YES" or "NO"
            amount_in: Amount of capital to invest
            apply_fee: Whether to apply trading fee
        
        Returns:
            Tuple of (shares_received, price_impact, new_prices)
        """
        shares_out, price_impact = self.calculate_shares_out(outcome, amount_in, apply_fee)
        
        # Update state
        if apply_fee:
            amount_after_fee = amount_in * (1 - self.fee_rate)
        else:
            amount_after_fee = amount_in
        
        k = self.state.constant_product
        
        if outcome.upper() == "YES":
            self.state.yes_shares += amount_after_fee
            self.state.no_shares = k / self.state.yes_shares if self.state.yes_shares > 0 else self.state.no_shares
        elif outcome.upper() == "NO":
            self.state.no_shares += amount_after_fee
            self.state.yes_shares = k / self.state.no_shares if self.state.no_shares > 0 else self.state.yes_shares
        else:
            raise ValueError(f"Unknown outcome: {outcome}")
        
        new_prices = self.state.get_all_prices()
        
        return shares_out, price_impact, new_prices
    
    def get_current_odds(self) -> Dict[str, float]:
        """
        Get current odds (prices) for all outcomes.
        
        Returns:
            Dictionary mapping outcome to price (0.0 to 1.0)
        """
        return self.state.get_all_prices()
    
    def get_liquidity(self) -> Dict[str, float]:
        """Get current liquidity for each outcome"""
        return {
            "YES": self.state.yes_shares,
            "NO": self.state.no_shares,
            "total": self.state.total_liquidity
        }
    
    def add_initial_liquidity(self, yes_amount: float, no_amount: float):
        """
        Add initial liquidity to bootstrap the market.
        Used when creating a new market.
        
        Args:
            yes_amount: Initial YES liquidity
            no_amount: Initial NO liquidity
        """
        if yes_amount <= 0 or no_amount <= 0:
            raise ValueError("Liquidity amounts must be positive")
        
        self.state.yes_shares = yes_amount
        self.state.no_shares = no_amount

