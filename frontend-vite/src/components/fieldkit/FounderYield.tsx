import { Zap, TrendingUp, Clock, AlertTriangle } from 'lucide-react';

export function FounderYield() {
  // Mock data - would come from API
  const yieldData = {
    pending: 127.50,
    totalEarned: 1842.30,
    hourlyRate: 127.50,
    timelines: [
      { name: 'Oil Crisis - Hormuz Strait', stability: 72, hourlyYield: 52.30, founded: '3 days ago' },
      { name: 'Fed Rate Decision', stability: 65, hourlyYield: 38.10, founded: '5 days ago' },
      { name: 'Contagion Zero - Mumbai', stability: 45, hourlyYield: 37.10, founded: '1 day ago' },
    ],
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="bg-[#0D0D0D] border border-amber-500/30 rounded-lg overflow-hidden">
        {/* Header */}
        <div className="p-4 bg-gradient-to-r from-amber-900/30 to-orange-900/20 border-b border-amber-500/20">
          <div className="flex items-center justify-between">
            <h3 className="text-amber-400 font-bold flex items-center gap-2">
              <Zap className="w-5 h-5" />
              FOUNDER'S YIELD
            </h3>
            <div className="flex items-center gap-1 text-green-400 text-xs">
              <TrendingUp className="w-3 h-3" />
              <span>+12.5% this week</span>
            </div>
          </div>
        </div>

        {/* Main Stats */}
        <div className="p-3 sm:p-4 grid grid-cols-3 gap-2 sm:gap-4 border-b border-gray-800">
          <div className="text-center min-w-0">
            <p className="text-gray-500 text-xs uppercase tracking-wide">Pending</p>
            <p className="text-amber-400 font-bold text-lg sm:text-2xl font-mono tracking-tight truncate">
              ${yieldData.pending.toFixed(2)}
            </p>
          </div>
          <div className="text-center border-x border-gray-800 min-w-0 px-1">
            <p className="text-gray-500 text-xs uppercase tracking-wide">Hourly Rate</p>
            <p className="text-green-400 font-bold text-lg sm:text-2xl font-mono tracking-tight truncate">
              ${yieldData.hourlyRate.toFixed(2)}
            </p>
          </div>
          <div className="text-center min-w-0">
            <p className="text-gray-500 text-xs uppercase tracking-wide">All Time</p>
            <p className="text-cyan-400 font-bold text-lg sm:text-2xl font-mono tracking-tight truncate">
              ${yieldData.totalEarned.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Timeline Breakdown */}
        <div className="p-4">
          <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-3">Your Timelines</h4>
          <div className="space-y-3">
            {yieldData.timelines.map((timeline, i) => (
              <div key={i} className="bg-gray-900/50 rounded-lg p-3">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="text-white font-medium text-sm">{timeline.name}</p>
                    <p className="text-gray-500 text-xs flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Founded {timeline.founded}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-amber-400 font-bold font-mono">${timeline.hourlyYield.toFixed(2)}/hr</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${
                        timeline.stability > 60 ? 'bg-green-500' :
                        timeline.stability > 30 ? 'bg-amber-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${timeline.stability}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500">{timeline.stability}%</span>
                </div>
                {timeline.stability < 50 && (
                  <p className="text-amber-400 text-xs mt-2 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    Low stability reduces yield rate
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Claim Button */}
        <div className="p-4 border-t border-gray-800">
          <button
            disabled
            className="w-full px-4 py-4 bg-gradient-to-r from-amber-900/30 to-orange-900/30 border border-amber-500/30 text-amber-400/50 rounded-lg font-bold cursor-not-allowed flex items-center justify-center gap-2 text-lg"
          >
            <Zap className="w-5 h-5" />
            CLAIM ${yieldData.pending.toFixed(2)}
          </button>
          <div className="flex justify-between items-center mt-3 text-xs text-gray-500">
            <span>Min. claim: $50.00</span>
            <span>Gas: ~$0.02</span>
          </div>
          <div className="mt-3 p-2 bg-amber-900/10 border border-amber-500/20 rounded text-center">
            <p className="text-amber-400 text-xs">🔒 Connect wallet to claim yield</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FounderYield;

