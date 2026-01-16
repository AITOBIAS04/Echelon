"use client";

/**
 * PaymentModal Component
 * ======================
 * 
 * A comprehensive payment modal for betting on prediction markets.
 * 
 * Features:
 * - Shows wallet balance (USDC on Base)
 * - Displays available payment methods
 * - Handles transaction flow with direct USDC transfers (via wagmi)
 * - Shows transaction confirmation
 * - Integrates with betting flow
 */

import { useState, useEffect, useCallback } from "react";
import { useAccount, useBalance, useWriteContract, useWaitForTransactionReceipt } from "wagmi";
import { formatUnits, parseUnits } from "viem";
import { erc20Abi } from "viem";
import toast from "react-hot-toast";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// USDC contract address on Base Sepolia (testnet)
const USDC_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"; // Base Sepolia USDC

export default function PaymentModal({
  isOpen,
  onClose,
  marketId,
  marketTitle,
  outcome,
  amount,
  pricePerShare,
  onPaymentSuccess,
  onPaymentError,
}) {
  const { address, isConnected } = useAccount();
  const { data: usdcBalance } = useBalance({
    address,
    token: USDC_ADDRESS,
    enabled: isConnected,
  });
  
  const { data: ethBalance } = useBalance({
    address,
    enabled: isConnected,
  });

  // Default to play money if user doesn't have enough USDC
  const [paymentMethod, setPaymentMethod] = useState("play_money"); // "usdc" | "play_money" | "deposit"
  const [isProcessing, setIsProcessing] = useState(false);
  const [playMoneyBalance, setPlayMoneyBalance] = useState(null);
  const [txHash, setTxHash] = useState(null);
  
  // Wagmi hooks for USDC transfer
  const { writeContract, data: hash, isPending: isWriting } = useWriteContract();
  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({
    hash,
  });

  // Fetch play money balance
  useEffect(() => {
    if (isOpen && address) {
      fetchPlayMoneyBalance();
    }
  }, [isOpen, address]);

  const fetchPlayMoneyBalance = async () => {
    try {
      // Try to get balance from backend
      const token = localStorage.getItem("access_token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      if (address) {
        headers["X-Wallet-Address"] = address;
      }

      const res = await fetch(`${API_BASE}/users/me`, { headers });
      if (res.ok) {
        const data = await res.json();
        setPlayMoneyBalance(data.play_money_balance || 0);
      }
    } catch (err) {
      console.error("Failed to fetch play money balance:", err);
    }
  };


  // Handle successful payment confirmation
  useEffect(() => {
    if (isConfirmed && hash) {
      // Payment confirmed, now place the bet
      const placeBetAfterPayment = async () => {
        try {
          const token = localStorage.getItem("access_token");
          const headers = {
            "Content-Type": "application/json",
            ...(token && { Authorization: `Bearer ${token}` }),
            ...(address && { "X-Wallet-Address": address }),
          };

          const betRes = await fetch(`${API_BASE}/markets/${marketId}/bet`, {
            method: "POST",
            headers,
            body: JSON.stringify({
              outcome,
              amount,
              use_play_money: false, // Real USDC bet
            }),
          });

          if (!betRes.ok) {
            const error = await betRes.json();
            throw new Error(error.detail || "Bet placement failed");
          }

          const betData = await betRes.json();
          toast.success(`Payment successful! Bet placed. Potential payout: $${betData.potential_payout || amount}`, {
            icon: "✅",
            style: { background: "#064e3b", color: "#fff", border: "1px solid #059669" },
          });
          onPaymentSuccess?.(betData);
          setTimeout(() => {
            onClose();
            setTxHash(null);
          }, 2000);
        } catch (error) {
          toast.error(error.message || "Failed to place bet after payment");
          onPaymentError?.(error.message);
        } finally {
          setIsProcessing(false);
        }
      };
      
      placeBetAfterPayment();
    }
  }, [isConfirmed, hash, marketId, outcome, amount, address, onPaymentSuccess, onPaymentError, onClose]);


  // Handle play money payment (no blockchain transaction)
  // Handle USDC payment (on-chain transaction)
  const handleUSDCPayment = async () => {
    if (!address || !hasEnoughUSDC) {
      toast.error("Insufficient USDC balance");
      return;
    }

    setIsProcessing(true);
    setTxHash(null);

    try {
      // Transfer USDC to platform contract (or escrow)
      // For now, we'll use a simple approval + transfer flow
      const amountInWei = parseUnits(totalCost.toFixed(6), 6); // USDC has 6 decimals

      writeContract({
        address: USDC_ADDRESS,
        abi: erc20Abi,
        functionName: "transfer",
        args: [
          "0x0000000000000000000000000000000000000000", // Platform address - replace with actual
          amountInWei,
        ],
      });

      // hash will be set by useWriteContract, and useWaitForTransactionReceipt will handle confirmation
      // The useEffect above will call placeBetAfterPayment when isConfirmed is true
    } catch (error) {
      console.error("USDC payment error:", error);
      toast.error(error.message || "Failed to initiate payment");
      setIsProcessing(false);
      onPaymentError?.(error.message);
    }
  };

  const handlePlayMoneyPayment = async () => {
    if (!playMoneyBalance || playMoneyBalance < amount) {
      toast.error("Insufficient play money balance");
      return;
    }

    setIsProcessing(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers = {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
        ...(address && { "X-Wallet-Address": address }),
      };

      const res = await fetch(`${API_BASE}/markets/${marketId}/bet`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          outcome,
          amount,
          use_play_money: true, // Explicitly mark as play money bet
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Bet placement failed");
      }

      const data = await res.json();
      // Refresh play money balance after bet
      fetchPlayMoneyBalance();
      toast.success(`Bet placed with Play Money! Potential payout: $${data.potential_payout}`, {
        icon: "💸",
        style: { background: "#064e3b", color: "#fff", border: "1px solid #059669" },
      });
      onPaymentSuccess?.(data);
      onClose();
    } catch (err) {
      toast.error(err.message);
      onPaymentError?.(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;
  
  // Ensure modal is visible with proper z-index

  const usdcBalanceFormatted = usdcBalance
    ? parseFloat(formatUnits(usdcBalance.value, usdcBalance.decimals || 6)).toFixed(2)
    : "0.00";

  const ethBalanceFormatted = ethBalance
    ? parseFloat(formatUnits(ethBalance.value, 18)).toFixed(4)
    : "0.0000";

  const totalCost = amount || 0;
  const hasEnoughUSDC = parseFloat(usdcBalanceFormatted) >= totalCost;
  const hasEnoughPlayMoney = playMoneyBalance && playMoneyBalance >= totalCost;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="border-b border-gray-700 p-6">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Complete Payment</h2>
              <p className="text-gray-400 text-sm">
                {marketTitle || "Market Bet"} • {outcome}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-2xl transition-colors"
              disabled={isProcessing}
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Payment Summary */}
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-400">Bet Amount</span>
              <span className="text-white font-mono text-lg">${totalCost.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Potential Payout</span>
              <span className="text-green-400 font-mono">
                ${((totalCost / (pricePerShare || 0.5)) * 0.95).toFixed(2)}
              </span>
            </div>
          </div>

          {/* Wallet Balance Display */}
          {isConnected && (
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">
                Wallet Balances
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">💵</span>
                    <span className="text-gray-300">USDC (Base)</span>
                  </div>
                  <span className={`font-mono ${hasEnoughUSDC ? "text-green-400" : "text-red-400"}`}>
                    ${usdcBalanceFormatted}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">⚡</span>
                    <span className="text-gray-300">ETH</span>
                  </div>
                  <span className="font-mono text-gray-400">{ethBalanceFormatted} ETH</span>
                </div>
                {playMoneyBalance !== null && (
                  <div className="flex justify-between items-center pt-2 border-t border-gray-700">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🎮</span>
                      <span className="text-gray-300">Play Money</span>
                    </div>
                    <span className={`font-mono ${hasEnoughPlayMoney ? "text-green-400" : "text-yellow-400"}`}>
                      ${playMoneyBalance.toFixed(2)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Payment Method Selection */}
          <div>
            <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">
              Payment Method
            </h3>
            <div className="space-y-2">
              {/* USDC on Base Option */}
              {isConnected && (
                <button
                  onClick={() => setPaymentMethod("usdc")}
                  disabled={isProcessing}
                  className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                    paymentMethod === "usdc"
                      ? "border-purple-500 bg-purple-900/30"
                      : "border-gray-700 bg-gray-800 hover:border-gray-600"
                  } ${!hasEnoughUSDC ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-white font-semibold">USDC on Base</div>
                      <div className="text-sm text-gray-400 mt-1">
                        Pay with USDC • Secure on-chain transaction
                      </div>
                    </div>
                    {!hasEnoughUSDC && (
                      <span className="text-xs text-red-400">Insufficient</span>
                    )}
                  </div>
                </button>
              )}

              {/* Play Money Option */}
              {playMoneyBalance !== null && (
                <button
                  onClick={() => setPaymentMethod("play_money")}
                  disabled={isProcessing || !hasEnoughPlayMoney}
                  className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                    paymentMethod === "play_money"
                      ? "border-green-500 bg-green-900/30"
                      : "border-gray-700 bg-gray-800 hover:border-gray-600"
                  } ${!hasEnoughPlayMoney ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-white font-semibold">Play Money</div>
                      <div className="text-sm text-gray-400 mt-1">
                        Use your play money balance • No blockchain transaction
                      </div>
                    </div>
                    {!hasEnoughPlayMoney && (
                      <span className="text-xs text-red-400">Insufficient</span>
                    )}
                  </div>
                </button>
              )}

              {/* Deposit Option */}
              {isConnected && !hasEnoughUSDC && (
                <button
                  onClick={() => setPaymentMethod("deposit")}
                  disabled={isProcessing}
                  className="w-full p-4 rounded-lg border-2 border-gray-700 bg-gray-800 hover:border-gray-600 transition-all text-left"
                >
                  <div className="text-white font-semibold">Deposit USDC</div>
                  <div className="text-sm text-gray-400 mt-1">
                    Add funds to your wallet first
                  </div>
                </button>
              )}
            </div>
          </div>

          {/* Payment Action */}
          <div className="pt-4">
            {paymentMethod === "usdc" && isConnected ? (
              <div className="space-y-3">
                <button
                  onClick={handleUSDCPayment}
                  disabled={!hasEnoughUSDC || isProcessing || isWriting || isConfirming}
                  className={`w-full py-4 rounded-lg font-bold text-lg transition-all ${
                    isProcessing || isWriting || isConfirming || !hasEnoughUSDC
                      ? "bg-gray-700 cursor-not-allowed text-gray-500"
                      : "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500"
                  }`}
                >
                  {isProcessing || isWriting || isConfirming
                    ? isConfirming
                    ? "Confirming transaction..."
                    : "Processing..."
                    : `Pay $${totalCost.toFixed(2)} USDC`}
                </button>
                {hash && (
                  <div className="text-xs text-gray-400 text-center">
                    Transaction: {hash.slice(0, 10)}...{hash.slice(-8)}
                  </div>
                )}
                {isConfirmed && (
                  <div className="text-sm text-green-400 text-center">
                    ✅ Payment confirmed! Placing bet...
                  </div>
                )}
              </div>
            ) : paymentMethod === "play_money" ? (
              <button
                onClick={handlePlayMoneyPayment}
                disabled={isProcessing || !hasEnoughPlayMoney}
                className={`w-full py-4 rounded-lg font-bold text-lg transition-all ${
                  isProcessing || !hasEnoughPlayMoney
                    ? "bg-gray-700 cursor-not-allowed text-gray-500"
                    : "bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500"
                }`}
              >
                {isProcessing
                  ? "Processing..."
                  : `Pay $${totalCost.toFixed(2)} with Play Money`}
              </button>
            ) : paymentMethod === "deposit" ? (
              <div className="text-center py-4">
                <p className="text-gray-400 mb-4">
                  Please deposit USDC to your wallet to continue.
                </p>
                <a
                  href="https://bridge.base.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
                >
                  Bridge to Base
                </a>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-gray-400 mb-4">
                  {!isConnected
                    ? "Please connect your wallet to pay with USDC"
                    : "Select a payment method above"}
                </p>
              </div>
            )}
          </div>

          {/* Info Footer */}
          <div className="pt-4 border-t border-gray-700">
            <p className="text-xs text-gray-500 text-center">
              💡 Payments are processed securely on Base network. Play money bets don't require blockchain transactions.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

