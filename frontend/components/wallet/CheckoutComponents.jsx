"use client";

/**
 * Checkout Components using OnchainKit
 * =====================================
 * 
 * USDC payment components for the prediction market.
 * 
 * Components:
 * - MarketBetCheckout: Pay for market shares
 * - IntelAccessCheckout: Pay for intel access (x402)
 * - DepositCheckout: Add funds to balance
 * - QuickCheckout: Simple one-click checkout
 * 
 * Uses OnchainKit's Checkout component with Coinbase Commerce backend.
 */
import { useState, useCallback } from "react";
import {
  Checkout,
  CheckoutButton,
  CheckoutStatus,
} from "@coinbase/onchainkit/checkout";
import { useAccount } from "wagmi";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// CHARGE HANDLER (Backend API)
// =============================================================================

async function createCharge(
  type,
  userId,
  params
) {
  const response = await fetch(`${API_BASE}/payments/onchain/create-charge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      type,
      user_id: userId,
      ...params,
    }),
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to create charge: ${error}`);
  }
  
  const data = await response.json();
  return data.id; // Return charge ID for OnchainKit
}

// =============================================================================
// MARKET BET CHECKOUT
// =============================================================================

export function MarketBetCheckout({
  marketId,
  marketTitle,
  outcome,
  shares,
  pricePerShare,
  onSuccess,
  onError,
  className = "",
}) {
  const { address, isConnected } = useAccount();
  const [isLoading, setIsLoading] = useState(false);
  
  const totalAmount = shares * pricePerShare;
  
  const chargeHandler = useCallback(async () => {
    if (!address) throw new Error("Wallet not connected");
    
    setIsLoading(true);
    try {
      return await createCharge("bet", address, {
        market_id: marketId,
        market_title: marketTitle,
        outcome,
        shares,
        price_per_share: pricePerShare,
      });
    } finally {
      setIsLoading(false);
    }
  }, [address, marketId, marketTitle, outcome, shares, pricePerShare]);
  
  const handleStatus = useCallback(
    (status) => {
      const { statusName, statusData } = status;
      
      switch (statusName) {
        case "success":
          onSuccess?.(statusData?.chargeId);
          break;
        case "error":
          onError?.(statusData?.message || "Payment failed");
          break;
      }
    },
    [onSuccess, onError]
  );
  
  if (!isConnected) {
    return (
      <div className={`text-center p-4 bg-gray-800 rounded-lg ${className}`}>
        <p className="text-gray-400 mb-2">Connect wallet to place bet</p>
      </div>
    );
  }
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Bet Summary */}
      <div className="bg-gray-800/50 rounded-lg p-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Outcome:</span>
          <span className="text-white font-bold">{outcome}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Shares:</span>
          <span className="text-white">{shares}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Price/Share:</span>
          <span className="text-white">${pricePerShare.toFixed(2)}</span>
        </div>
        <div className="border-t border-gray-700 pt-2 flex justify-between">
          <span className="text-gray-400">Total:</span>
          <span className="text-cyan-400 font-bold text-lg">
            ${totalAmount.toFixed(2)}
          </span>
        </div>
      </div>
      
      {/* Checkout Button */}
      <Checkout chargeHandler={chargeHandler} onStatus={handleStatus}>
        <CheckoutButton
          coinbaseBranded
          text={isLoading ? "Creating..." : `Pay $${totalAmount.toFixed(2)} USDC`}
          disabled={isLoading}
          className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 text-white py-3 rounded-lg font-bold transition-colors"
        />
        <CheckoutStatus />
      </Checkout>
      
      <p className="text-xs text-gray-500 text-center">
        Payments are processed on Base network with USDC
      </p>
    </div>
  );
}

// =============================================================================
// INTEL ACCESS CHECKOUT (x402 Payment Gate)
// =============================================================================

export const INTEL_TIERS = {
  basic: { price: 1, name: "Basic Intel", duration: "24 hours", features: ["Additional context", "Source links"] },
  premium: { price: 5, name: "Premium Analysis", duration: "7 days", features: ["Full analysis", "Source data", "Historical trends"] },
  alpha: { price: 25, name: "Alpha Intelligence", duration: "30 days", features: ["Real-time updates", "SMS/Email alerts", "Priority access", "API access"] },
};

export function IntelAccessCheckout({
  tier,
  marketId,
  onSuccess,
  onError,
  className = "",
}) {
  const { address, isConnected } = useAccount();
  const [isLoading, setIsLoading] = useState(false);
  
  const tierInfo = INTEL_TIERS[tier];
  
  const chargeHandler = useCallback(async () => {
    if (!address) throw new Error("Wallet not connected");
    
    setIsLoading(true);
    try {
      return await createCharge("intel", address, {
        intel_tier: tier,
        market_id: marketId,
      });
    } finally {
      setIsLoading(false);
    }
  }, [address, tier, marketId]);
  
  const handleStatus = useCallback(
    (status) => {
      if (status.statusName === "success") {
        onSuccess?.(status.statusData?.chargeId);
      } else if (status.statusName === "error") {
        onError?.(status.statusData?.message || "Payment failed");
      }
    },
    [onSuccess, onError]
  );
  
  if (!isConnected) {
    return (
      <div className={`text-center p-4 bg-gray-800 rounded-lg ${className}`}>
        <p className="text-gray-400">Connect wallet to unlock intel</p>
      </div>
    );
  }
  
  return (
    <div className={`bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg p-6 border border-cyan-500/20 ${className}`}>
      {/* Tier Header */}
      <div className="text-center mb-4">
        <span className="text-3xl">🔒</span>
        <h3 className="text-xl font-bold text-white mt-2">{tierInfo.name}</h3>
        <p className="text-gray-400 text-sm">Access for {tierInfo.duration}</p>
      </div>
      
      {/* Price */}
      <div className="text-center mb-4">
        <span className="text-4xl font-bold text-cyan-400">${tierInfo.price}</span>
        <span className="text-gray-400 ml-2">USDC</span>
      </div>
      
      {/* Features */}
      <ul className="space-y-2 mb-6">
        {tierInfo.features.map((feature, i) => (
          <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
            <span className="text-green-400">✓</span>
            {feature}
          </li>
        ))}
      </ul>
      
      {/* Checkout */}
      <Checkout chargeHandler={chargeHandler} onStatus={handleStatus}>
        <CheckoutButton
          coinbaseBranded
          text={isLoading ? "Processing..." : `Unlock for $${tierInfo.price}`}
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white py-3 rounded-lg font-bold transition-all"
        />
        <CheckoutStatus />
      </Checkout>
    </div>
  );
}

// =============================================================================
// DEPOSIT CHECKOUT
// =============================================================================

export function DepositCheckout({
  amount,
  onSuccess,
  onError,
  className = "",
}) {
  const { address, isConnected } = useAccount();
  const [isLoading, setIsLoading] = useState(false);
  const [customAmount, setCustomAmount] = useState(amount);
  
  const chargeHandler = useCallback(async () => {
    if (!address) throw new Error("Wallet not connected");
    
    setIsLoading(true);
    try {
      return await createCharge("deposit", address, {
        amount: customAmount,
      });
    } finally {
      setIsLoading(false);
    }
  }, [address, customAmount]);
  
  const handleStatus = useCallback(
    (status) => {
      if (status.statusName === "success") {
        onSuccess?.(status.statusData?.chargeId);
      } else if (status.statusName === "error") {
        onError?.(status.statusData?.message || "Deposit failed");
      }
    },
    [onSuccess, onError]
  );
  
  if (!isConnected) {
    return (
      <div className={`text-center p-4 bg-gray-800 rounded-lg ${className}`}>
        <p className="text-gray-400">Connect wallet to deposit</p>
      </div>
    );
  }
  
  const presetAmounts = [10, 25, 50, 100, 250, 500];
  
  return (
    <div className={`bg-gray-800 rounded-lg p-6 ${className}`}>
      <h3 className="text-lg font-bold text-white mb-4">💰 Deposit Funds</h3>
      
      {/* Preset Amounts */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        {presetAmounts.map((preset) => (
          <button
            key={preset}
            onClick={() => setCustomAmount(preset)}
            className={`py-2 rounded-lg font-mono text-sm transition-colors ${
              customAmount === preset
                ? "bg-cyan-600 text-white"
                : "bg-gray-700 text-gray-300 hover:bg-gray-600"
            }`}
          >
            ${preset}
          </button>
        ))}
      </div>
      
      {/* Custom Amount */}
      <div className="mb-4">
        <label className="block text-sm text-gray-400 mb-1">Custom Amount</label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
          <input
            type="number"
            min="1"
            max="10000"
            value={customAmount}
            onChange={(e) => setCustomAmount(Number(e.target.value))}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg py-2 pl-8 pr-4 text-white font-mono focus:border-cyan-500 focus:outline-none"
          />
        </div>
      </div>
      
      {/* Checkout */}
      <Checkout chargeHandler={chargeHandler} onStatus={handleStatus}>
        <CheckoutButton
          coinbaseBranded
          text={isLoading ? "Processing..." : `Deposit $${customAmount} USDC`}
          disabled={isLoading || customAmount < 1}
          className="w-full bg-green-600 hover:bg-green-500 disabled:bg-gray-700 text-white py-3 rounded-lg font-bold transition-colors"
        />
        <CheckoutStatus />
      </Checkout>
      
      <p className="text-xs text-gray-500 text-center mt-4">
        Funds will be added to your platform balance instantly
      </p>
    </div>
  );
}

// =============================================================================
// QUICK CHECKOUT (Inline, Minimal)
// =============================================================================

export function QuickCheckout({
  type,
  amount,
  label,
  params = {},
  onSuccess,
  onError,
  className = "",
  disabled = false,
}) {
  const { address, isConnected } = useAccount();
  const [isLoading, setIsLoading] = useState(false);
  
  const chargeHandler = useCallback(async () => {
    if (!address) throw new Error("Wallet not connected");
    
    setIsLoading(true);
    try {
      return await createCharge(type, address, { amount, ...params });
    } finally {
      setIsLoading(false);
    }
  }, [address, type, amount, params]);
  
  const handleStatus = useCallback(
    (status) => {
      if (status.statusName === "success") {
        onSuccess?.(status.statusData?.chargeId);
      } else if (status.statusName === "error") {
        onError?.(status.statusData?.message || "Payment failed");
      }
    },
    [onSuccess, onError]
  );
  
  if (!isConnected) {
    return null;
  }
  
  return (
    <Checkout chargeHandler={chargeHandler} onStatus={handleStatus}>
      <CheckoutButton
        text={isLoading ? "..." : label || `$${amount}`}
        disabled={disabled || isLoading}
        className={`bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg font-bold transition-colors ${className}`}
      />
    </Checkout>
  );
}




