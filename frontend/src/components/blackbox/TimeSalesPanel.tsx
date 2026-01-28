// Time & Sales Component
// Real-time trade feed

import type { Trade } from '../../types/blackbox';

interface TimeSalesProps {
  trades: Trade[];
}

export function TimeSalesPanel({ trades }: TimeSalesProps) {
  const formatTime = (date: Date) => {
    return date.toISOString().substr(11, 8);
  };

  const formatSize = (size: number) => {
    if (size >= 1000) {
      return (size / 1000).toFixed(1) + 'K';
    }
    return size.toString();
  };

  return (
    <div className="rounded-2xl border border-[#26292E] bg-[#0F1113] flex flex-col min-h-0">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#26292E]">
        <span className="text-sm font-semibold text-[#F1F5F9]">TIME & SALES</span>
        <span className="text-xs font-mono text-[#64748B]">LIVE FEED</span>
      </div>

      {/* Table */}
      <div className="flex-1 min-h-0 overflow-y-auto pr-1">
        <table className="w-full table-fixed">
          <thead className="sticky top-0 bg-[#0F1113] z-10">
            <tr>
              <th className="w-[88px] px-3 py-2 text-left text-xs font-medium text-[#64748B]">TIME</th>
              <th className="w-[72px] px-3 py-2 text-left text-xs font-medium text-[#64748B]">PRICE</th>
              <th className="w-[56px] px-3 py-2 text-left text-xs font-medium text-[#64748B]">SIZE</th>
              <th className="w-[56px] px-3 py-2 text-left text-xs font-medium text-[#64748B]">SIDE</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-[#64748B]">AGENT</th>
            </tr>
</thead>
          <tbody>
            {trades.map((trade) => (
              <tr key={trade.id} className="hover:bg-[#1A1D23] transition-colors">
                <td className="px-3 py-1.5 text-xs font-mono text-[#94A3B8]">{formatTime(trade.timestamp)}</td>
                <td className={`px-3 py-1.5 text-xs font-mono ${trade.side === 'buy' ? 'text-[#4ADE80]' : 'text-[#FB7185]'}`}>
                  ${trade.price.toFixed(2)}
                </td>
                <td className="px-3 py-1.5 text-xs text-[#F1F5F9]">{formatSize(trade.size)}</td>
                <td className="px-3 py-1.5">
                  <span className={`inline-block px-1.5 py-0.5 text-xs font-medium rounded ${
                    trade.side === 'buy'
                      ? 'bg-[rgba(74,222,128,0.15)] text-[#4ADE80]'
                      : 'bg-[rgba(251,113,133,0.15)] text-[#FB7185]'
                  }`}>
                    {trade.side.toUpperCase()}
                  </span>
                </td>
                <td className="px-3 py-1.5 text-xs text-[#F1F5F9] truncate">{trade.agent}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
