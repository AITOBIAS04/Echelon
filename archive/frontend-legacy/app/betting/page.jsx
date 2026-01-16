"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";

export default function BettingPageWrapper() {
  return (
    <Suspense fallback={<BettingLoadingState />}>
      <BettingPage />
    </Suspense>
  );
}

function BettingLoadingState() {
  return (
    <div className="container mx-auto max-w-lg mt-10 p-6 text-center">
      <div className="animate-pulse">
        <div className="h-8 bg-gray-700 rounded w-3/4 mx-auto mb-4"></div>
        <div className="h-4 bg-gray-700 rounded w-1/2 mx-auto"></div>
      </div>
    </div>
  );
}

function BettingPage() {
  const [wager, setWager] = useState(100);
  const [clientSeed, setClientSeed] = useState("my-provably-fair-seed");
  const [balance, setBalance] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [token, setToken] = useState(null);

  const [isSimulating, setIsSimulating] = useState(false);
  const [simStage, setSimStage] = useState("");
  const [simProgress, setSimProgress] = useState(0);

  const searchParams = useSearchParams();
  const engineName = searchParams.get("engine") || "market";
  const betOn = searchParams.get("bet_on") || "outcome";

  const potentialPayout = (parseFloat(wager) || 0) * 1.95;
  const isValidWager =
    parseFloat(wager) > 0 && parseFloat(wager) <= (balance || 0);

  useEffect(() => {
    const storedToken = localStorage.getItem("access_token");
    if (!storedToken) {
      setError("You are not logged in. Redirecting...");
      setTimeout(() => (window.location.href = "/login"), 2000);
      return;
    }
    setToken(storedToken);

    const fetchUser = async () => {
      const res = await fetch("http://localhost:8000/users/me", {
        headers: { Authorization: `Bearer ${storedToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setBalance(data.play_money_balance);
      }
    };
    fetchUser();
  }, []);

  const SIMULATION_STAGES = [
    { text: "Initializing Neural Engine...", duration: 600, progress: 15 },
    { text: "Loading Market State...", duration: 400, progress: 30 },
    { text: "Spawning AI Agents...", duration: 500, progress: 45 },
    { text: "Agents Placing Orders...", duration: 700, progress: 60 },
    { text: "Processing Volatility...", duration: 400, progress: 75 },
    { text: "Collapsing Wave Function...", duration: 500, progress: 90 },
    { text: "Finalizing Outcome...", duration: 300, progress: 100 },
  ];

  const runSimulationStages = async () => {
    for (const stage of SIMULATION_STAGES) {
      setSimStage(stage.text);
      setSimProgress(stage.progress);
      await new Promise((r) => setTimeout(r, stage.duration));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");
    setIsSimulating(true);
    setSimProgress(0);

    try {
      const simulationPromise = runSimulationStages();

      const apiPromise = fetch("http://localhost:8000/play-match/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          wager: parseFloat(wager),
          client_seed: clientSeed,
          engine_name: engineName,
        }),
      });

      const [_, res] = await Promise.all([simulationPromise, apiPromise]);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Simulation failed");
      }

      await new Promise((r) => setTimeout(r, 300));

      setMessage(`${data.message} (Result: ${data.game_result})`);
      setBalance(data.new_balance);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSimulating(false);
      setSimStage("");
      setSimProgress(0);
    }
  };

  if (!engineName) {
    return (
      <div className="container mx-auto max-w-lg mt-10 p-6 text-center bg-gray-900 rounded-lg border border-gray-700">
        <h1 className="text-2xl font-bold text-red-500">⚠️ No Game Selected</h1>
        <p className="mt-4 text-gray-400">
          Please go to the{" "}
          <a
            href="/lobby"
            className="text-blue-400 underline hover:text-blue-300"
          >
            Game Lobby
          </a>{" "}
          to select a simulation.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 py-10 px-4">
      <div className="container mx-auto max-w-lg">
        <div className="bg-gray-900 border border-gray-700 rounded-t-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="ml-2 text-gray-500 text-sm font-mono">
              seed://betting-terminal
            </span>
          </div>
        </div>

        <div className="bg-gray-900/90 border-x border-b border-gray-700 rounded-b-lg p-6 backdrop-blur">
          <h1 className="text-3xl font-bold mb-2 text-center">
            <span className="text-gray-400">BET ON:</span>{" "}
            <span className="text-blue-400">{engineName.toUpperCase()}</span>
          </h1>
          <p className="text-center text-gray-500 mb-6 font-mono text-sm">
            {betOn || "Outcome Prediction"}
          </p>

          <div className="bg-gray-800/50 rounded-lg p-4 mb-6 border border-gray-700">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Your Balance</span>
              <span className="text-2xl font-bold font-mono text-green-400">
                {balance === null ? (
                  <span className="animate-pulse">Loading...</span>
                ) : (
                  `$${balance.toFixed(2)}`
                )}
              </span>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label
                className="block text-sm font-medium mb-2 text-gray-400"
                htmlFor="wager"
              >
                WAGER AMOUNT
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                  $
                </span>
                <input
                  id="wager"
                  type="number"
                  value={wager}
                  onChange={(e) => setWager(e.target.value)}
                  className="w-full p-3 pl-8 bg-gray-800 border border-gray-600 rounded-lg text-white font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                  required
                  disabled={isSimulating}
                  min="1"
                  max={balance || 10000}
                />
              </div>

              <div className="flex gap-2 mt-2">
                {[10, 50, 100, 500].map((amount) => (
                  <button
                    key={amount}
                    type="button"
                    onClick={() => setWager(amount)}
                    disabled={isSimulating || amount > (balance || 0)}
                    className={`flex-1 py-1 px-2 rounded text-sm font-mono transition-all ${
                      amount > (balance || 0)
                        ? "bg-gray-800 text-gray-600 cursor-not-allowed"
                        : "bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white"
                    }`}
                  >
                    ${amount}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-4 p-4 bg-gradient-to-r from-green-900/30 to-blue-900/30 rounded-lg border border-green-700/50">
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Potential Payout</span>
                <span
                  className={`text-2xl font-bold font-mono ${
                    isValidWager ? "text-green-400" : "text-gray-500"
                  }`}
                >
                  ${isValidWager ? potentialPayout.toFixed(2) : "0.00"}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Odds: 1.95x (includes 5% platform fee)
              </div>
            </div>

            <details className="mb-6">
              <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-400">
                Advanced: Provably Fair Seed
              </summary>
              <div className="mt-2">
                <input
                  id="clientSeed"
                  type="text"
                  value={clientSeed}
                  onChange={(e) => setClientSeed(e.target.value)}
                  className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white font-mono text-sm"
                  required
                  disabled={isSimulating}
                />
              </div>
            </details>

            <button
              type="submit"
              disabled={isSimulating || balance === null || !isValidWager}
              className={`w-full py-4 rounded-lg font-bold text-lg transition-all relative overflow-hidden ${
                isSimulating
                  ? "bg-purple-900 cursor-wait"
                  : !isValidWager
                  ? "bg-gray-700 cursor-not-allowed text-gray-500"
                  : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 shadow-lg hover:shadow-blue-500/25"
              }`}
            >
              {isSimulating ? (
                <>
                  <div
                    className="absolute inset-0 bg-purple-600/30 transition-all duration-300"
                    style={{ width: `${simProgress}%` }}
                  />
                  <span className="relative flex items-center justify-center gap-3">
                    <span className="animate-spin text-xl">⚙️</span>
                    <span className="font-mono text-sm">{simStage}</span>
                  </span>
                </>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <span>🚀</span> RUN SIMULATION
                </span>
              )}
            </button>
          </form>

          {message && (
            <div className="mt-6 p-4 bg-green-900/30 border border-green-700 rounded-lg">
              <div className="flex items-center gap-2 text-green-400">
                <span>✅</span>
                <span className="font-mono">{message}</span>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-6 p-4 bg-red-900/30 border border-red-700 rounded-lg">
              <div className="flex items-center gap-2 text-red-400">
                <span>❌</span>
                <span>{error}</span>
              </div>
            </div>
          )}

          <div className="mt-6 text-center text-xs text-gray-600 font-mono">
            <p>All simulations are cryptographically verifiable</p>
            <p className="mt-1">Server Seed revealed after bet resolution</p>
          </div>
        </div>
      </div>
    </div>
  );
}




