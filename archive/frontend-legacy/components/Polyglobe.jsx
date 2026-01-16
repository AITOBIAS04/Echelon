// Temporarily disabled due to Three.js/React version conflicts
// The globe visualization will be re-enabled once dependencies stabilize

"use client";

import { useMemo } from 'react';

export default function Polyglobe({ data, onGlobeClick, signals = [] }) {
  // Generate stable star positions
  const stars = useMemo(() => {
    return Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: (i * 37) % 100, // Pseudo-random but stable
      top: (i * 23) % 100,
      delay: (i * 0.1) % 2,
    }));
  }, []);

  return (
    <div className="w-full h-80 bg-gradient-to-b from-gray-900 to-black rounded-xl flex items-center justify-center border border-gray-700 relative overflow-hidden">
      {/* Animated background stars */}
      <div className="absolute inset-0 opacity-30">
        {stars.map((star) => (
          <div
            key={star.id}
            className="absolute w-1 h-1 bg-white rounded-full animate-pulse"
            style={{
              left: `${star.left}%`,
              top: `${star.top}%`,
              animationDelay: `${star.delay}s`,
            }}
          />
        ))}
      </div>
      
      {/* Globe placeholder */}
      <div className="text-center z-10">
        <div className="text-6xl mb-3 animate-spin" style={{ animationDuration: '3s' }}>🌍</div>
        <p className="text-gray-400 font-medium">Global Operations Map</p>
        <p className="text-xs text-gray-600 mt-1">Interactive globe loading...</p>
        {signals && signals.length > 0 && (
          <p className="text-xs text-green-400 mt-2">
            {signals.length} active signal{signals.length !== 1 ? 's' : ''} detected
          </p>
        )}
      </div>
    </div>
  );
}
