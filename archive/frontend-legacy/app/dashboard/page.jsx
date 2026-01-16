"use client";

import { useState, useEffect } from "react";
import TensionGauge from "@/components/TensionGauge";
// NEW IMPORTS
import EvolutionStatus, { EvolutionStatusCompact } from "@/components/EvolutionStatus";
import PersonalTimeline, { PersonalTimelineCompact } from "@/components/PersonalTimeline";
import { API_BASE } from "@/utils/api";

export default function DashboardPage() {
  const [worldState, setWorldState] = useState(null);
  const [activeBets, setActiveBets] = useState([]); // Mock for now, fetch from /users/me/bets later
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_BASE}/world-state`);
        if (res.ok) {
          const data = await res.json();
          setWorldState(data);
        }
      } catch (error) {
        console.error("Failed to fetch world state", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="min-h-screen bg-gray-950 flex items-center justify-center text-green-500 font-mono">INITIALIZING NEURAL LINK...</div>;

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      <div className="container mx-auto max-w-7xl space-y-6">
        
        {/* HEADER */}
        <div className="flex justify-between items-end border-b border-gray-800 pb-4">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">COMMAND CENTER</h1>
            <p className="text-gray-400 font-mono text-xs mt-1">
              SYSTEM STATUS: <span className="text-green-400">OPTIMAL</span> | 
              LAST SYNC: {new Date().toLocaleTimeString()}
            </p>
          </div>
          <div className="flex gap-3">
            <div className="bg-blue-900/20 border border-blue-500/30 px-3 py-1 rounded text-blue-400 text-xs font-mono">
              BASE SEPOLIA: ACTIVE
            </div>
            <div className="bg-purple-900/20 border border-purple-500/30 px-3 py-1 rounded text-purple-400 text-xs font-mono">
              AGENTS: {worldState?.agent_count || "ONLINE"}
            </div>
          </div>
        </div>

        {/* MAIN GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT COLUMN: SIMULATION STATE */}
          <div className="space-y-6">
            {/* 1. Global Tension */}
            <TensionGauge score={worldState?.global_tension_score} />
            
            {/* 2. Active Simulation (Personal Timeline Compact) */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-1 overflow-hidden">
              <div className="bg-gray-800/50 px-4 py-2 border-b border-gray-800 flex justify-between items-center">
                <span className="text-xs font-bold text-gray-400 uppercase">Active Simulation</span>
                <span className="text-xs text-purple-400 animate-pulse">● Live</span>
              </div>
              <div className="p-4">
                {activeBets.length > 0 ? (
                  <PersonalTimelineCompact bet={activeBets[0]} />
                ) : (
                   <div className="text-center py-6 text-gray-500 text-sm">
                     No active simulations.<br/>
                     <a href="/markets" className="text-purple-400 hover:underline">Launch one now →</a>
                   </div>
                )}
              </div>
            </div>
          </div>

          {/* MIDDLE COLUMN: EVOLUTION & ANALYTICS */}
          <div className="space-y-6">
            <EvolutionStatus domain="financial" />
            
            {/* Console Logs */}
            <div className="bg-black rounded-xl border border-gray-800 p-4 h-64 font-mono text-xs overflow-y-auto text-green-500/80 shadow-inner">
              <div className="mb-2 pb-2 border-b border-gray-900 text-gray-500 font-bold">NEURAL LOGS</div>
              <p>{">"} System initialized.</p>
              <p>{">"} Connected to Base Sepolia (Block 33999458).</p>
              <p>{">"} Fetching news from GNews, NewsAPI...</p>
              <p>{">"} Analysing 30 headlines...</p>
              <p>{">"} Virality Score: 85 (High)</p>
              <p>{">"} Agent 'Director_AI' calculating tension...</p>
              <p className="text-yellow-500">{">"} WARN: Tension increased to 0.15</p>
              {/* In a real app, you'd map these from worldState.event_log */}
            </div>
          </div>

          {/* RIGHT COLUMN: MARKET ACTIVITY */}
          <div className="space-y-6">
             {/* Reuse your MarketCard logic or a simplified "Trending Markets" list here */}
             <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
               <h3 className="text-sm font-bold text-gray-400 uppercase mb-4">Trending Markets</h3>
               <div className="space-y-3">
                 {/* Placeholder / Mock List */}
                 {[1,2,3].map(i => (
                   <div key={i} className="flex justify-between items-center p-3 bg-gray-800/50 rounded hover:bg-gray-800 cursor-pointer transition-colors">
                     <div>
                       <div className="text-sm text-white font-medium">Bitcoin {'>'} $100k?</div>
                       <div className="text-xs text-gray-500">Ends in 4h • Vol: $12k</div>
                     </div>
                     <div className="text-right">
                       <div className="text-green-400 font-bold">65%</div>
                       <div className="text-xs text-gray-600">YES</div>
                     </div>
                   </div>
                 ))}
               </div>
             </div>
          </div>

        </div>
      </div>
    </div>
  );
}
