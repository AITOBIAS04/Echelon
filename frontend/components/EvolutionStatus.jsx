"use client";

import { useState, useEffect } from "react";
import useSWR from "swr";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const fetcher = (url) => fetch(url).then(res => res.json());

/**
 * Evolution Status Widget
 * =======================
 * Shows real-time status of the evolutionary AI system.
 * Displays generation, dominant species, and learning progress.
 */

// Archetype icons and colors
const ARCHETYPE_CONFIG = {
  SHARK: { icon: "🦈", color: "text-blue-400", bg: "bg-blue-900/30" },
  WHALE: { icon: "🐋", color: "text-purple-400", bg: "bg-purple-900/30" },
  DEGEN: { icon: "🎲", color: "text-red-400", bg: "bg-red-900/30" },
  VALUE: { icon: "📊", color: "text-green-400", bg: "bg-green-900/30" },
  MOMENTUM: { icon: "🚀", color: "text-yellow-400", bg: "bg-yellow-900/30" },
  CONTRARIAN: { icon: "🔄", color: "text-orange-400", bg: "bg-orange-900/30" },
  NOISE: { icon: "📢", color: "text-gray-400", bg: "bg-gray-900/30" },
};

// Progress bar component
function ProgressBar({ value, max = 100, color = "purple" }) {
  const percentage = Math.min((value / max) * 100, 100);
  const colorClasses = {
    purple: "bg-purple-500",
    green: "bg-green-500",
    blue: "bg-blue-500",
    red: "bg-red-500",
    yellow: "bg-yellow-500",
  };
  
  return (
    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
      <div 
        className={`h-full ${colorClasses[color]} transition-all duration-500`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

// Single archetype display
function ArchetypeBar({ name, percentage, count }) {
  const config = ARCHETYPE_CONFIG[name] || ARCHETYPE_CONFIG.NOISE;
  const isOP = percentage > 40;
  const isWeak = percentage < 5;
  
  return (
    <div className="flex items-center gap-3">
      <span className="text-xl" title={name}>{config.icon}</span>
      <div className="flex-1">
        <div className="flex justify-between text-xs mb-1">
          <span className={config.color}>{name}</span>
          <span className="text-gray-400">
            {percentage.toFixed(0)}%
            {isOP && <span className="text-red-400 ml-1">⚠️ OP</span>}
            {isWeak && <span className="text-yellow-400 ml-1">⚠️ Weak</span>}
          </span>
        </div>
        <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className={`h-full ${config.bg.replace('/30', '')} transition-all duration-500`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// Main component
export default function EvolutionStatus({ domain = "financial" }) {
  // Fetch evolution stats from API
  const { data: evolutionData, error } = useSWR(
    `${API_BASE}/evolution/status?domain=${domain}`,
    fetcher,
    { 
      refreshInterval: 30000, // Refresh every 30s
      fallbackData: null,
    }
  );
  
  // Mock data for when API isn't available
  const mockData = {
    generation: 12,
    population_size: 88,
    average_fitness: 84.5,
    fitness_change: 12.3,
    dominant_archetype: "SHARK",
    dominant_percentage: 42,
    archetype_distribution: {
      SHARK: 42,
      WHALE: 25,
      DEGEN: 15,
      VALUE: 10,
      MOMENTUM: 5,
      CONTRARIAN: 3,
    },
    is_learning: true,
    last_evolution: new Date().toISOString(),
  };
  
  const data = evolutionData || mockData;
  const dominantConfig = ARCHETYPE_CONFIG[data.dominant_archetype] || ARCHETYPE_CONFIG.SHARK;
  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            🧬 Evolutionary Status
          </h3>
          <p className="text-sm text-gray-400">
            {domain.charAt(0).toUpperCase() + domain.slice(1)} Domain
          </p>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs ${
          data.is_learning ? 'bg-green-900/50 text-green-400' : 'bg-yellow-900/50 text-yellow-400'
        }`}>
          {data.is_learning ? '✓ Learning' : '⚠ Stagnant'}
        </div>
      </div>
      
      {/* Key Stats Grid */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center">
          <div className="text-gray-400 text-xs mb-1">Generation</div>
          <div className="text-2xl font-mono text-purple-400">
            Gen {data.generation}
          </div>
        </div>
        <div className="text-center">
          <div className="text-gray-400 text-xs mb-1">Dominant Species</div>
          <div className={`text-2xl font-mono ${dominantConfig.color}`}>
            {dominantConfig.icon} {data.dominant_archetype}
          </div>
          <div className="text-xs text-gray-500">
            ({data.dominant_percentage}%)
          </div>
        </div>
        <div className="text-center">
          <div className="text-gray-400 text-xs mb-1">Avg Intelligence</div>
          <div className="text-2xl font-mono text-green-400">
            {data.average_fitness.toFixed(1)}
          </div>
          <div className={`text-xs ${data.fitness_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {data.fitness_change >= 0 ? '+' : ''}{data.fitness_change.toFixed(1)}%
          </div>
        </div>
      </div>
      
      {/* Population Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-xs text-gray-400 mb-2">
          <span>Population Health</span>
          <span>{data.population_size} / 100 agents</span>
        </div>
        <ProgressBar value={data.population_size} max={100} color="green" />
      </div>
      
      {/* Archetype Distribution */}
      <div className="space-y-3">
        <div className="text-sm font-semibold text-gray-300 mb-2">
          Species Distribution
        </div>
        {Object.entries(data.archetype_distribution)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 5)
          .map(([name, percentage]) => (
            <ArchetypeBar 
              key={name} 
              name={name} 
              percentage={percentage}
            />
          ))
        }
      </div>
      
      {/* Last Evolution */}
      {data.last_evolution && (
        <div className="mt-4 pt-4 border-t border-gray-700 text-xs text-gray-500">
          Last evolution: {new Date(data.last_evolution).toLocaleString()}
        </div>
      )}
    </div>
  );
}

// Compact version for sidebar
export function EvolutionStatusCompact({ domain = "financial" }) {
  const mockData = {
    generation: 12,
    dominant_archetype: "SHARK",
    dominant_percentage: 42,
    fitness: 84.5,
    is_learning: true,
  };
  
  const dominantConfig = ARCHETYPE_CONFIG[mockData.dominant_archetype];
  
  return (
    <div className="bg-gray-800/30 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">🧬</span>
          <span className="text-sm font-semibold text-white">Gen {mockData.generation}</span>
        </div>
        <div className={`flex items-center gap-1 ${dominantConfig.color}`}>
          <span>{dominantConfig.icon}</span>
          <span className="text-sm">{mockData.dominant_percentage}%</span>
        </div>
      </div>
      <div className="mt-2 flex justify-between text-xs">
        <span className="text-gray-500">Intelligence</span>
        <span className="text-green-400">{mockData.fitness} (+12%)</span>
      </div>
    </div>
  );
}




