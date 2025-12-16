"use client";

/**
 * Wallet Dashboard Page
 * =====================
 * 
 * Full wallet management interface with:
 * - Wallet connection
 * - Balance display (on-chain + platform)
 * - Deposit/withdraw
 * - Transaction history
 * - Intel access management
 */
import { useState, useEffect, useCallback } from "react";
import useSWR from "swr";
import { WalletConnect, WalletIdentity, WalletBalance, WalletCard } from "@/components/wallet/WalletComponents";
import { DepositCheckout, IntelAccessCheckout, INTEL_TIERS } from "@/components/wallet/CheckoutComponents";
import { useAccount } from "wagmi";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const fetcher = (url) => fetch(url).then(res => res.json());

// =============================================================================
// COMPONENTS
// =============================================================================

function BalanceCard({ title, amount, currency, icon, subtext, color = "cyan" }) {
  const colorClasses = {
    cyan: "text-cyan-400 border-cyan-500/30",
    green: "text-green-400 border-green-500/30",
    purple: "text-purple-400 border-purple-500/30",
    yellow: "text-yellow-400 border-yellow-500/30",
  };
  
  return (
    <div className={`bg-gray-800/50 border ${colorClasses[color]} rounded-lg p-4`}>
      <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
        <span>{icon}</span>
        <span>{title}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`text-3xl font-bold font-mono ${colorClasses[color].split(" ")[0]}`}>
          {typeof amount === "number" ? amount.toFixed(2) : amount}
        </span>
        <span className="text-gray-500">{currency}</span>
      </div>
      {subtext && <p className="text-xs text-gray-500 mt-1">{subtext}</p>}
    </div>
  );
}

function DepositModal({ isOpen, onClose, userId, onSuccess }) {
  const [amount, setAmount] = useState(50);
  const [chargeUrl, setChargeUrl] = useState(null);
  const presets = [10, 25, 50, 100, 250, 500];
  
  const handleDeposit = async () => {
    try {
      const response = await fetch(`${API_BASE}/payments/charges/deposit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          amount: amount,
          redirect_url: window.location.href
        })
      });
      
      if (!response.ok) throw new Error("Failed to create charge");
      
      const data = await response.json();
      setChargeUrl(data.hosted_url);
      
      // Open checkout in new tab
      window.open(data.hosted_url, "_blank");
      
      onSuccess?.();
    } catch (err) {
      console.error("Deposit error:", err);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl p-6 max-w-md w-full border border-gray-700">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-white">💰 Deposit USDC</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>
        
        {chargeUrl ? (
          <div className="text-center py-6">
            <p className="text-green-400 mb-4">✅ Checkout opened in new tab!</p>
            <p className="text-gray-400 text-sm mb-4">
              Complete payment in the Coinbase Commerce checkout page
            </p>
            <button
              onClick={() => window.open(chargeUrl, "_blank")}
              className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded-lg font-bold"
            >
              Reopen Checkout
            </button>
          </div>
        ) : (
          <>
            {/* Preset amounts */}
            <div className="grid grid-cols-3 gap-2 mb-4">
              {presets.map((preset) => (
                <button
                  key={preset}
                  onClick={() => setAmount(preset)}
                  className={`py-3 rounded-lg font-mono font-bold transition-colors ${
                    amount === preset
                      ? "bg-cyan-600 text-white"
                      : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                  }`}
                >
                  ${preset}
                </button>
              ))}
            </div>
            
            {/* Custom amount */}
            <div className="mb-6">
              <label className="block text-sm text-gray-400 mb-1">Custom Amount</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-lg">$</span>
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg py-3 pl-8 pr-4 text-white text-xl font-mono focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>
            
            {/* Info */}
            <div className="bg-gray-800/50 rounded-lg p-3 mb-6 text-sm">
              <div className="flex justify-between text-gray-400">
                <span>Network:</span>
                <span className="text-white">Base (L2)</span>
              </div>
              <div className="flex justify-between text-gray-400 mt-1">
                <span>Currency:</span>
                <span className="text-cyan-400">USDC</span>
              </div>
              <div className="flex justify-between text-gray-400 mt-1">
                <span>Fees:</span>
                <span className="text-green-400">$0.00</span>
              </div>
            </div>
            
            {/* Deposit button */}
            <button
              onClick={handleDeposit}
              disabled={amount < 1}
              className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:from-gray-600 disabled:to-gray-700 text-white py-4 rounded-lg font-bold text-lg transition-all"
            >
              Deposit ${amount} USDC
            </button>
            
            <p className="text-xs text-gray-500 text-center mt-4">
              Powered by Coinbase Commerce • Instant settlement on Base
            </p>
          </>
        )}
      </div>
    </div>
  );
}

function IntelAccessCard({ tier, userId }) {
  const { data: access } = useSWR(
    userId ? `${API_BASE}/payments/intel-access/${userId}/${tier}` : null,
    fetcher
  );
  
  const tierInfo = {
    basic: { icon: "📄", name: "Basic", price: 1 },
    premium: { icon: "⭐", name: "Premium", price: 5 },
    alpha: { icon: "🔮", name: "Alpha", price: 25 },
  };
  
  const info = tierInfo[tier];
  const hasAccess = access?.has_access;
  const expiresAt = access?.expires_at ? new Date(access.expires_at) : null;
  
  return (
    <div className={`bg-gray-800/50 border rounded-lg p-4 ${
      hasAccess ? "border-green-500/30" : "border-gray-700"
    }`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{info.icon}</span>
          <span className="font-bold text-white">{info.name}</span>
        </div>
        {hasAccess ? (
          <span className="bg-green-500/20 text-green-400 text-xs px-2 py-1 rounded">
            ACTIVE
          </span>
        ) : (
          <span className="text-gray-500 text-sm">${info.price}</span>
        )}
      </div>
      
      {hasAccess && expiresAt && (
        <p className="text-xs text-gray-400">
          Expires: {expiresAt.toLocaleDateString()}
        </p>
      )}
    </div>
  );
}

function TransactionHistory({ userId }) {
  // In production, this would fetch from the backend
  const transactions = [
    { id: 1, type: "deposit", amount: 100, date: "2025-11-28", status: "completed" },
    { id: 2, type: "bet", amount: -25, market: "BTC > 100k", date: "2025-11-27", status: "completed" },
    { id: 3, type: "win", amount: 50, market: "ETH Launch", date: "2025-11-26", status: "completed" },
    { id: 4, type: "intel", amount: -5, tier: "Premium", date: "2025-11-25", status: "completed" },
  ];
  
  const typeIcons = {
    deposit: "💰",
    bet: "🎲",
    win: "🏆",
    intel: "🔒",
    withdraw: "📤",
  };
  
  return (
    <div className="bg-gray-800/50 rounded-lg">
      <div className="p-4 border-b border-gray-700">
        <h3 className="font-bold text-white">📜 Transaction History</h3>
      </div>
      <div className="divide-y divide-gray-700">
        {transactions.map((tx) => (
          <div key={tx.id} className="p-4 flex items-center justify-between hover:bg-gray-800/50">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{typeIcons[tx.type]}</span>
              <div>
                <p className="text-white font-medium capitalize">{tx.type}</p>
                <p className="text-xs text-gray-500">
                  {tx.market || tx.tier || tx.date}
                </p>
              </div>
            </div>
            <span className={`font-mono font-bold ${
              tx.amount >= 0 ? "text-green-400" : "text-red-400"
            }`}>
              {tx.amount >= 0 ? "+" : ""}{tx.amount.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function WalletPage() {
  const { address, isConnected } = useAccount();
  const [showDeposit, setShowDeposit] = useState(false);
  
  // Fetch platform balance
  const { data: balanceData, mutate: refreshBalance } = useSWR(
    address ? `${API_BASE}/payments/balance/${address}` : null,
    fetcher
  );
  
  const platformBalance = balanceData?.balance || 0;
  
  // Simulated on-chain balances (in production, use wagmi useBalance)
  const onChainUSDC = 1234.56;
  const onChainETH = 0.0521;
  
  if (!isConnected) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-6">💼</div>
          <h1 className="text-3xl font-bold text-white mb-4">
            Connect Your Wallet
          </h1>
          <p className="text-gray-400 mb-8">
            Connect your wallet to deposit funds, place bets, and manage your prediction market portfolio.
          </p>
          <WalletConnect />
          <div className="mt-8 flex items-center justify-center gap-4 text-gray-500 text-sm">
            <span>Supports:</span>
            <span className="text-cyan-400">Coinbase Wallet</span>
            <span>•</span>
            <span className="text-orange-400">MetaMask</span>
            <span>•</span>
            <span className="text-purple-400">WalletConnect</span>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900/80 backdrop-blur border-b border-gray-800 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-3xl">💼</span>
              <div>
                <h1 className="text-2xl font-black tracking-tight">WALLET</h1>
                <p className="text-xs text-gray-500 font-mono">USDC on Base</p>
              </div>
            </div>
            <WalletIdentity />
          </div>
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Balance Cards */}
        <section className="grid md:grid-cols-4 gap-4">
          <BalanceCard
            title="Platform Balance"
            amount={platformBalance}
            currency="USD"
            icon="🏦"
            subtext="Available for betting"
            color="green"
          />
          <BalanceCard
            title="On-Chain USDC"
            amount={onChainUSDC}
            currency="USDC"
            icon="💵"
            subtext="In your wallet"
            color="cyan"
          />
          <BalanceCard
            title="ETH (Gas)"
            amount={onChainETH}
            currency="ETH"
            icon="⛽"
            subtext="For transactions"
            color="purple"
          />
          <BalanceCard
            title="Lifetime P&L"
            amount="+523.45"
            currency="USD"
            icon="📈"
            subtext="+15.3% all time"
            color="green"
          />
        </section>
        
        {/* Quick Actions */}
        <section className="grid md:grid-cols-3 gap-4">
          <button
            onClick={() => setShowDeposit(true)}
            className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white p-6 rounded-lg font-bold text-lg transition-all flex items-center justify-center gap-3"
          >
            <span className="text-2xl">💰</span>
            Deposit USDC
          </button>
          <button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white p-6 rounded-lg font-bold text-lg transition-all flex items-center justify-center gap-3">
            <span className="text-2xl">📤</span>
            Withdraw
          </button>
          <button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white p-6 rounded-lg font-bold text-lg transition-all flex items-center justify-center gap-3">
            <span className="text-2xl">🔄</span>
            Swap Tokens
          </button>
        </section>
        
        {/* Intel Access */}
        <section>
          <h2 className="text-lg font-bold text-gray-400 mb-4 flex items-center gap-2">
            <span>🔒</span> Intel Access Tiers
          </h2>
          <div className="grid md:grid-cols-3 gap-4">
            <IntelAccessCard tier="basic" userId={address} />
            <IntelAccessCard tier="premium" userId={address} />
            <IntelAccessCard tier="alpha" userId={address} />
          </div>
        </section>
        
        {/* Transaction History */}
        <section>
          <TransactionHistory userId={address} />
        </section>
        
        {/* Network Info */}
        <section className="bg-gray-800/30 rounded-lg p-6">
          <h2 className="text-lg font-bold text-gray-400 mb-4">ℹ️ Network Information</h2>
          <div className="grid md:grid-cols-3 gap-6 text-sm">
            <div>
              <p className="text-gray-500">Network</p>
              <p className="text-white font-bold">Base (Ethereum L2)</p>
            </div>
            <div>
              <p className="text-gray-500">Settlement Currency</p>
              <p className="text-cyan-400 font-bold">USDC</p>
            </div>
            <div>
              <p className="text-gray-500">Transaction Fees</p>
              <p className="text-green-400 font-bold">~$0.01 (Gasless available)</p>
            </div>
          </div>
        </section>
      </main>
      
      {/* Deposit Modal */}
      <DepositModal
        isOpen={showDeposit}
        onClose={() => setShowDeposit(false)}
        userId={address}
        onSuccess={() => {
          refreshBalance();
          setShowDeposit(false);
        }}
      />
    </div>
  );
}




