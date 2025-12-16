"use client";

/**
 * ClientProviders Component
 * =========================
 * 
 * Wraps all client-side providers that need to run in the browser.
 * This allows the root layout to remain a server component (for metadata).
 */

import { OnchainProviders } from "@/providers/OnchainProviders";
import Header from "@/components/Header";
import { Toaster } from "react-hot-toast";

export default function ClientProviders({ children }) {
  return (
    <OnchainProviders>
      {/* THE NEW BACKGROUND */}
      <div className="nebula-bg" />
      
      {/* Content Container (Added padding-top for fixed header) */}
      <div className="relative z-10 pt-24">
        <Header />
        <main>{children}</main>
      </div>
      
      {/* CYBERPUNK TOASTER CONFIGURATION */}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: 'rgba(17, 24, 39, 0.95)',
            border: '1px solid #374151',
            color: '#e5e7eb',
            fontFamily: 'monospace',
            backdropFilter: 'blur(10px)',
            padding: '16px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)',
          },
          success: {
            iconTheme: { primary: '#4ade80', secondary: '#052e16' },
            style: { borderLeft: '4px solid #4ade80' }
          },
          error: {
            iconTheme: { primary: '#f87171', secondary: '#450a0a' },
            style: { borderLeft: '4px solid #f87171' }
          },
        }}
      />
    </OnchainProviders>
  );
}

