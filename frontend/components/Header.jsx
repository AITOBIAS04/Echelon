"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { logout } from "@/utils/auth";
import { WalletConnect } from "@/components/wallet/WalletComponents";
import { useAccount } from "wagmi";

export default function Header() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const { isConnected, address } = useAccount();

  useEffect(() => {
    if (typeof window !== 'undefined' && localStorage.getItem("access_token")) {
      setIsLoggedIn(true);
    }
  }, []);

  return (
    <div className="fixed top-4 left-0 right-0 z-50 flex justify-center">
      <nav className="glass-panel rounded-full px-8 py-3 flex items-center gap-8 min-w-[600px] justify-between transition-all duration-300">
        
        {/* Logo Area */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-gradient-to-tr from-purple-600 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-purple-500/20 group-hover:shadow-purple-500/40 transition-all">
            <span className="text-white font-bold">S</span>
          </div>
          <span className="font-bold text-lg tracking-tight text-white group-hover:text-purple-200 transition-colors">
            Project Seed
          </span>
        </Link>

        {/* Navigation Links */}
        <div className="flex items-center gap-6 text-sm font-medium text-gray-400">
          {isLoggedIn || isConnected ? (
            <>
              <Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
              <Link href="/markets" className="hover:text-white transition-colors">Markets</Link>
              <Link href="/situation-room" className="hover:text-red-400 text-red-300 transition-colors flex items-center gap-1">
                <span>🎭</span> Situation Room
              </Link>
              <Link href="/timelines" className="hover:text-white transition-colors">Timelines</Link>
              <div className="h-4 w-[1px] bg-white/10 mx-2" /> {/* Divider */}
              {isConnected ? (
                <WalletConnect />
              ) : (
                <button 
                  onClick={logout} 
                  className="text-red-400 hover:text-red-300 transition-colors"
                >
                  Disconnect
                </button>
              )}
            </>
          ) : (
            <>
              <Link href="/markets" className="hover:text-white transition-colors">Markets</Link>
              <Link href="/situation-room" className="hover:text-red-400 text-red-300 transition-colors flex items-center gap-1">
                <span>🎭</span> Situation Room
              </Link>
              <Link href="/login" className="hover:text-white transition-colors">Login</Link>
              <WalletConnect />
              <Link 
                href="/signup" 
                className="bg-white text-black px-5 py-2 rounded-full font-bold hover:bg-purple-50 transition-all hover:scale-105"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </nav>
    </div>
  );
}
