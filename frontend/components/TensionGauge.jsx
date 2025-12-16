"use client";

export default function TensionGauge({ score }) {
  // 1. Safe Data Handling
  // If score is null/undefined, we default to 0 but mark as "loading"
  const isDataMissing = score === undefined || score === null || isNaN(Number(score));
  const validScore = isDataMissing ? 0 : Number(score);
  
  // 2. Calculate Metrics
  const percentage = Math.min(Math.max(validScore * 100, 0), 100);
  
  let color = "bg-green-500";
  let glowColor = "shadow-green-500/50";
  let status = "PEACEFUL";
  
  if (percentage > 30) { color = "bg-yellow-500"; glowColor = "shadow-yellow-500/50"; status = "UNEASY"; }
  if (percentage > 60) { color = "bg-orange-500"; glowColor = "shadow-orange-500/50"; status = "HIGH TENSION"; }
  if (percentage > 80) { color = "bg-red-600"; glowColor = "shadow-red-600/50"; status = "CRITICAL"; }
  return (
    <div className="p-6 border border-gray-700 rounded-lg shadow-lg bg-gray-900/90 backdrop-blur text-white text-center relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none opacity-10 bg-gradient-to-b from-transparent via-gray-500/10 to-transparent bg-[length:100%_4px]" />
      
      <h2 className="text-2xl font-bold mb-4 tracking-wider">
        <span className="text-gray-400">GLOBAL</span> TENSION INDEX
      </h2>
      
      {/* Gauge Bar */}
      <div className="w-full bg-gray-800 rounded-full h-8 mb-2 relative overflow-hidden border border-gray-600">
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'linear-gradient(90deg, transparent 24%, rgba(255,255,255,.05) 25%, rgba(255,255,255,.05) 26%, transparent 27%)', backgroundSize: '20px 100%' }} />
        
        <div 
          className={`${color} h-8 rounded-full transition-all duration-1000 ease-out shadow-lg ${glowColor}`} 
          style={{ width: `${isDataMissing ? 0 : percentage}%` }}
        >
          {!isDataMissing && <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />}
        </div>
      </div>
      
      <div className="flex justify-between text-xs text-gray-500 font-mono mb-4">
        <span>0% PEACE</span>
        <span className="text-yellow-500">50% TENSION</span>
        <span className="text-red-500">100% WAR</span>
      </div>
      
      {/* Display Value */}
      <div className="mt-4">
        <span className={`text-4xl font-mono font-bold tracking-widest ${isDataMissing ? 'text-gray-500 animate-pulse' : color.replace('bg-', 'text-')}`}>
          {isDataMissing ? "CALCULATING..." : `${percentage.toFixed(2)}%`}
        </span>
        <p className={`mt-3 text-xl font-bold tracking-[0.3em] ${isDataMissing ? 'text-gray-600' : ''}`}>
          {isDataMissing ? '...' : status}
        </p>
      </div>
    </div>
  );
}
