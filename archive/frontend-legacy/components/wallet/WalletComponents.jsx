"use client";

/**
 * Wallet Components using OnchainKit
 * ===================================
 * 
 * Ready-to-use wallet connection and management components.
 * 
 * Components:
 * - WalletConnect: Connect button with dropdown
 * - WalletIdentity: Show connected wallet with avatar/name
 * - WalletBalance: Display USDC and ETH balances
 * - WalletDeposit: Deposit funds to balance
 * 
 * Requires OnchainProviders wrapper in layout.
 */
import { useState, useCallback } from "react";
import {
  ConnectWallet,
  Wallet,
  WalletDropdown,
  WalletDropdownLink,
  WalletDropdownDisconnect,
  WalletDropdownBasename,
  WalletDropdownFundLink,
} from "@coinbase/onchainkit/wallet";
import {
  Address,
  Avatar,
  Name,
  Identity,
  EthBalance,
} from "@coinbase/onchainkit/identity";
import { useAccount, useBalance, useDisconnect } from "wagmi";

// =============================================================================
// WALLET CONNECT BUTTON
// =============================================================================

export function WalletConnect({ 
  className = "",
  onConnect,
  onDisconnect 
}) {
  const { address, isConnected } = useAccount();
  const { disconnect } = useDisconnect();
  
  // Notify parent on connection
  if (isConnected && address && onConnect) {
    onConnect(address);
  }
  
  return (
    <div className={`wallet-connect ${className}`}>
      <Wallet>
        <ConnectWallet 
          withWalletAggregator
          text="Connect Wallet"
          className="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-lg font-bold transition-colors"
        >
          <Avatar className="h-6 w-6" />
          <Name />
        </ConnectWallet>
        <WalletDropdown>
          <Identity className="px-4 pt-3 pb-2" hasCopyAddressOnClick>
            <Avatar />
            <Name />
            <Address />
            <EthBalance />
          </Identity>
          <WalletDropdownBasename />
          <WalletDropdownLink 
            icon="wallet" 
            href="https://wallet.coinbase.com"
            target="_blank"
          >
            Coinbase Wallet
          </WalletDropdownLink>
          <WalletDropdownFundLink />
          <WalletDropdownDisconnect />
        </WalletDropdown>
      </Wallet>
    </div>
  );
}

// =============================================================================
// WALLET IDENTITY DISPLAY
// =============================================================================

export function WalletIdentity({ 
  className = "",
  showBalance = true 
}) {
  const { address, isConnected } = useAccount();
  
  if (!isConnected || !address) {
    return (
      <div className={`text-gray-500 ${className}`}>
        Not connected
      </div>
    );
  }
  
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <Identity
        address={address}
        className="flex items-center gap-2"
        hasCopyAddressOnClick
      >
        <Avatar className="h-8 w-8" />
        <div className="flex flex-col">
          <Name className="text-white font-medium" />
          <Address className="text-gray-400 text-xs" />
        </div>
      </Identity>
      {showBalance && (
        <div className="text-cyan-400 font-mono text-sm">
          <EthBalance address={address} />
        </div>
      )}
    </div>
  );
}

// =============================================================================
// WALLET BALANCE DISPLAY
// =============================================================================

// USDC contract address on Base
export const USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";
export const USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e";

export function WalletBalance({
  className = "",
  showUSDC = true,
  showETH = true,
}) {
  const { address, isConnected, chain } = useAccount();
  
  // Get ETH balance
  const { data: ethBalance, isLoading: ethLoading } = useBalance({
    address,
    query: { enabled: isConnected && showETH },
  });
  
  // Get USDC balance
  const usdcAddress = chain?.id === 8453 ? USDC_BASE : USDC_BASE_SEPOLIA;
  const { data: usdcBalance, isLoading: usdcLoading } = useBalance({
    address,
    token: usdcAddress,
    query: { enabled: isConnected && showUSDC },
  });
  
  if (!isConnected) {
    return null;
  }
  
  return (
    <div className={`flex items-center gap-4 ${className}`}>
      {showETH && (
        <div className="flex items-center gap-2">
          <span className="text-gray-400">ETH:</span>
          <span className="text-white font-mono">
            {ethLoading ? "..." : `${Number(ethBalance?.formatted || 0).toFixed(4)}`}
          </span>
        </div>
      )}
      {showUSDC && (
        <div className="flex items-center gap-2">
          <span className="text-gray-400">USDC:</span>
          <span className="text-cyan-400 font-mono font-bold">
            {usdcLoading ? "..." : `$${Number(usdcBalance?.formatted || 0).toFixed(2)}`}
          </span>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// FULL WALLET CARD
// =============================================================================

export function WalletCard({
  className = "",
  onDeposit,
  platformBalance = 0,
}) {
  const { address, isConnected, chain } = useAccount();
  
  if (!isConnected) {
    return (
      <div className={`bg-gray-800 rounded-lg p-6 ${className}`}>
        <h3 className="text-lg font-bold text-white mb-4">💼 Wallet</h3>
        <p className="text-gray-400 mb-4">Connect your wallet to start trading</p>
        <WalletConnect />
      </div>
    );
  }
  
  return (
    <div className={`bg-gray-800 rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">💼 Wallet</h3>
        <span className="text-xs text-gray-500 bg-gray-700 px-2 py-1 rounded">
          {chain?.name || "Unknown Network"}
        </span>
      </div>
      
      {/* Identity */}
      <div className="mb-4 p-3 bg-gray-900/50 rounded-lg">
        <WalletIdentity showBalance={false} />
      </div>
      
      {/* Balances */}
      <div className="space-y-3 mb-4">
        {/* On-chain balance */}
        <div className="flex justify-between items-center">
          <span className="text-gray-400">On-chain:</span>
          <WalletBalance showETH={false} showUSDC={true} />
        </div>
        
        {/* Platform balance */}
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Platform:</span>
          <span className="text-green-400 font-mono font-bold">
            ${platformBalance.toFixed(2)}
          </span>
        </div>
        {/* ETH for gas */}
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-500">Gas (ETH):</span>
          <WalletBalance showETH={true} showUSDC={false} className="text-gray-400" />
        </div>
      </div>
      
      {/* Actions */}
      <div className="flex gap-2">
        {onDeposit && (
          <button
            onClick={onDeposit}
            className="flex-1 bg-cyan-600 hover:bg-cyan-500 text-white py-2 rounded-lg font-bold transition-colors"
          >
            Deposit
          </button>
        )}
        <button
          className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg font-bold transition-colors"
        >
          Withdraw
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// COMPACT WALLET BUTTON (FOR HEADER)
// =============================================================================

export function WalletButton({ className = "" }) {
  const { isConnected } = useAccount();
  
  return (
    <div className={className}>
      <Wallet>
        <ConnectWallet
          withWalletAggregator
          text={isConnected ? undefined : "Connect"}
          className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white px-3 py-1.5 rounded-lg text-sm font-bold transition-all"
        >
          <Avatar className="h-5 w-5" />
          <Name className="text-sm" />
        </ConnectWallet>
        <WalletDropdown>
          <Identity className="px-4 pt-3 pb-2" hasCopyAddressOnClick>
            <Avatar />
            <Name />
            <Address />
            <EthBalance />
          </Identity>
          <WalletDropdownBasename />
          <WalletDropdownFundLink />
          <WalletDropdownDisconnect />
        </WalletDropdown>
      </Wallet>
    </div>
  );
}




