// app/lobby/page.jsx
"use client";
import Link from "next/link";

// This list defines all the games your platform offers
const games = [
  {
    name: "Sim-Election",
    description: "Bet on the winner of a 30-day political simulation.",
    engine_name: "election",
    bet_on: "Candidate A"
  },
  {
    name: "Sim-Market",
    description: "Bet on 'SAPL' stock in a 100-turn agent-based market.",
    engine_name: "market",
    bet_on: "SAPL to go UP"
  },
  {
    name: "Sim-Geopolitics",
    description: "Bet on whether 'Red Nation' declares war in 10 turns.",
    engine_name: "geopolitics",
    bet_on: "WAR"
  },
  {
    name: "Agent Duel",
    description: "Bet on 'Agent A' in a provably fair digital combat.",
    engine_name: "duel",
    bet_on: "Agent A"
  },
  {
    name: "AI Chess",
    description: "Bet on 'White' in a fast-paced Stockfish match.",
    engine_name: "chess",
    bet_on: "White"
  },
];

export default function LobbyPage() {
  return (
    <div className="container mx-auto max-w-2xl mt-10 p-6">
      <h1 className="text-4xl font-bold mb-8 text-center">Game Lobby</h1>
      <div className="space-y-4">
        {games.map((game) => (
          <div key={game.engine_name} className="p-6 border rounded-lg shadow-lg">
            <h2 className="text-2xl font-semibold">{game.name}</h2>
            <p className="text-gray-600 mt-2">{game.description}</p>
            <Link 
              href={`/betting?engine=${game.engine_name}&bet_on=${game.bet_on}`}
              className="inline-block mt-4 bg-blue-600 text-white px-5 py-2 rounded hover:bg-blue-700"
            >
              Place Bet (on {game.bet_on})
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}