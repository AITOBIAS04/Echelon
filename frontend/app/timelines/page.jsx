"use client";

import { useEffect, useState } from "react";
import PersonalTimeline from "@/components/PersonalTimeline";
import Header from "@/components/Header";

export default function TimelinesPage() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("token");
    if (token) {
      // Decode JWT to get user info (simplified)
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setUser(payload);
      } catch {
        // Invalid token
      }
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <Header user={user} />
      
      <main className="container mx-auto px-4 py-8">
        {/* Page title */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🦋 Butterfly Effect
          </h1>
          <p className="text-gray-400 max-w-2xl">
            Watch reality fork into divergent simulations. Each timeline represents 
            a "what if" scenario powered by AI agents. Bet on which simulation 
            will best predict reality.
          </p>
        </div>

        {/* How it works */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800/50 backdrop-blur rounded-lg p-6 border border-gray-700">
            <div className="text-3xl mb-3">📸</div>
            <h3 className="text-lg font-semibold text-white mb-2">1. Snapshot</h3>
            <p className="text-gray-400 text-sm">
              We capture the current state of reality - market prices, team standings, 
              political polls - at key moments.
            </p>
          </div>
          
          <div className="bg-gray-800/50 backdrop-blur rounded-lg p-6 border border-gray-700">
            <div className="text-3xl mb-3">🔀</div>
            <h3 className="text-lg font-semibold text-white mb-2">2. Fork</h3>
            <p className="text-gray-400 text-sm">
              From each snapshot, we create divergent timelines. "What if earnings beat?" 
              "What if the star player gets injured?"
            </p>
          </div>
          
          <div className="bg-gray-800/50 backdrop-blur rounded-lg p-6 border border-gray-700">
            <div className="text-3xl mb-3">🎰</div>
            <h3 className="text-lg font-semibold text-white mb-2">3. Bet</h3>
            <p className="text-gray-400 text-sm">
              Bet on which simulation timeline will most closely match what actually 
              happens. The closer your timeline, the bigger your payout.
            </p>
          </div>
        </div>

        {/* Main visualization */}
        <PersonalTimeline />

        {/* Recent activity */}
        <div className="mt-8 bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-4">📊 Recent Fork Activity</h2>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="text-left py-3 px-4">Event</th>
                  <th className="text-left py-3 px-4">Domain</th>
                  <th className="text-center py-3 px-4">Forks</th>
                  <th className="text-center py-3 px-4">Total Bets</th>
                  <th className="text-right py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-700/50 hover:bg-gray-700/30">
                  <td className="py-3 px-4 text-white">Apple Q4 Earnings</td>
                  <td className="py-3 px-4">
                    <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs">Finance</span>
                  </td>
                  <td className="py-3 px-4 text-center text-purple-400">3</td>
                  <td className="py-3 px-4 text-center text-green-400">$12,450</td>
                  <td className="py-3 px-4 text-right">
                    <span className="text-green-400">🟢 Active</span>
                  </td>
                </tr>
                <tr className="border-b border-gray-700/50 hover:bg-gray-700/30">
                  <td className="py-3 px-4 text-white">Man City vs Arsenal</td>
                  <td className="py-3 px-4">
                    <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-xs">Sports</span>
                  </td>
                  <td className="py-3 px-4 text-center text-purple-400">2</td>
                  <td className="py-3 px-4 text-center text-green-400">$8,230</td>
                  <td className="py-3 px-4 text-right">
                    <span className="text-blue-400">✅ Settled</span>
                  </td>
                </tr>
                <tr className="border-b border-gray-700/50 hover:bg-gray-700/30">
                  <td className="py-3 px-4 text-white">Bitcoin ETF News</td>
                  <td className="py-3 px-4">
                    <span className="bg-orange-500/20 text-orange-400 px-2 py-1 rounded text-xs">Crypto</span>
                  </td>
                  <td className="py-3 px-4 text-center text-purple-400">5</td>
                  <td className="py-3 px-4 text-center text-green-400">$45,120</td>
                  <td className="py-3 px-4 text-right">
                    <span className="text-green-400">🟢 Active</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-12 py-6">
        <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
          <p>Project Seed • Counterfactual Prediction Markets</p>
          <p className="mt-1">Powered by AI Agents on Base</p>
        </div>
      </footer>
    </div>
  );
}

