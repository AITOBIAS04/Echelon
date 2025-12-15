"use client";

/**
 * OnchainKit Provider Configuration
 * =================================
 * 
 * Sets up Coinbase Wallet integration using OnchainKit.
 * 
 * Features:
 * - Wallet connection (Coinbase Wallet, MetaMask, etc.)
 * - USDC checkout on Base network
 * - Identity/ENS resolution
 * - Transaction handling
 * 
 * Required environment variables:
 * - NEXT_PUBLIC_ONCHAINKIT_API_KEY: From https://portal.cdp.coinbase.com
 * - NEXT_PUBLIC_COINBASE_COMMERCE_API_KEY: For checkout (optional, can use backend)
 * 
 * Setup:
 * 1. npm install @coinbase/onchainkit viem wagmi @tanstack/react-query
 * 2. Wrap your app with <OnchainProviders>
 */
import { ReactNode } from "react";
import { OnchainKitProvider } from "@coinbase/onchainkit";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WagmiProvider, createConfig, http } from "wagmi";
import { base, baseSepolia } from "wagmi/chains";
import { coinbaseWallet, injected, metaMask } from "wagmi/connectors";
import { RainbowKitProvider } from "@rainbow-me/rainbowkit";
import "@rainbow-me/rainbowkit/styles.css";

// =============================================================================
// CONFIGURATION
// =============================================================================

// Use testnet for development, mainnet for production
const CHAIN = process.env.NODE_ENV === "production" ? base : baseSepolia;

// Wagmi configuration for wallet connections
const wagmiConfig = createConfig({
  chains: [base, baseSepolia],
  connectors: [
    coinbaseWallet({
      appName: "Pizzint Prediction Market",
      appLogoUrl: "https://pizzint.app/logo.png", // Replace with your logo
      preference: "smartWalletOnly", // Use smart wallet for gasless txs
    }),
    metaMask(),
    injected(),
  ],
  transports: {
    [base.id]: http(),
    [baseSepolia.id]: http(),
  },
});

// React Query client for data fetching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      refetchOnWindowFocus: false,
    },
  },
});

// OnchainKit configuration
const onchainKitConfig = {
  apiKey: process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY,
  chain: CHAIN,
  config: {
    appearance: {
      name: "Pizzint",
      logo: "https://pizzint.app/logo.png",
      mode: "auto", // auto, light, or dark
      theme: "base", // base, cyberpunk, default, hacker
    },
  },
};

// =============================================================================
// PROVIDER COMPONENT
// =============================================================================

export function OnchainProviders({ children }) {
  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider>
          <OnchainKitProvider
            apiKey={onchainKitConfig.apiKey}
            chain={onchainKitConfig.chain}
            config={onchainKitConfig.config}
          >
            {children}
          </OnchainKitProvider>
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}

// =============================================================================
// EXPORTS
// =============================================================================

export { wagmiConfig, queryClient, CHAIN };
export { base, baseSepolia } from "wagmi/chains";

