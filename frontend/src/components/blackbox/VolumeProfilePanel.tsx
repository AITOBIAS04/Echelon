import { useMemo, useRef, useEffect, useState } from 'react';
import { useTimeSales } from '../../hooks/useBlackbox';
import type { Trade } from '../../types/blackbox';

type Bin = { priceMid: number; volume: number };

function computeBins(trades: Trade[], binCount = 24): Bin[] {
  if (trades.length === 0) return [];
  const prices = trades.map((t) => t.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = Math.max(1e-6, max - min);
  const step = range / binCount;

  const bins: Bin[] = Array.from({ length: binCount }, (_, i) => ({
    priceMid: min + (i + 0.5) * step,
    volume: 0,
  }));

  for (const t of trades) {
    const idx = Math.min(binCount - 1, Math.max(0, Math.floor((t.price - min) / step)));
    bins[idx].volume += t.size;
  }

  return bins;
}

export function VolumeProfilePanel() {
  const trades = useTimeSales();
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 800, height: 320 });

  useEffect(() => {
    const update = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      setSize({ width: rect.width, height: rect.height });
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  const bins = useMemo(() => computeBins(trades, 28), [trades]);
  const maxVol = useMemo(() => Math.max(1, ...bins.map((b) => b.volume)), [bins]);
  const poc = useMemo(() => {
    if (bins.length === 0) return null;
    return bins.reduce((acc, cur) => (cur.volume > acc.volume ? cur : acc), bins[0]);
  }, [bins]);

  // Sort bins for display: High price at index 0 (Top)
  const displayBins = useMemo(() => [...bins].sort((a, b) => b.priceMid - a.priceMid), [bins]);

  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4 flex flex-col gap-4 min-h-[300px]" style={{ flex: '1 1 400px' }}>
      <div className="flex items-center justify-between flex-shrink-0">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">Volume Profile</h3>
        {poc ? (
          <span className="text-[10px] font-mono text-status-info">
            POC ${poc.priceMid.toFixed(2)}
          </span>
        ) : null}
      </div>

      <div ref={containerRef} className="flex-1 min-h-0 relative">
        {bins.length === 0 ? (
          <div className="flex items-center justify-center h-full text-terminal-text-muted text-xs">Loading volume...</div>
        ) : (
          <svg width="100%" height="100%" className="overflow-visible">
            <defs>
              <linearGradient id="gradVolNormal" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#475569" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#475569" stopOpacity="0.15" />
              </linearGradient>
              <linearGradient id="gradPoc" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.2" />
              </linearGradient>
              <pattern id="bgBands" x="0" y="0" width="100%" height="18" patternUnits="userSpaceOnUse">
                <rect x="0" y="0" width="100%" height="9" fill="#0f172a" fillOpacity="0.3" />
              </pattern>
            </defs>

            {/* Background bands for readability */}
            <rect x={56} y={10} width={size.width - 56} height={size.height - 30} fill="url(#bgBands)" />

            {/* Horizontal grid lines */}
            {Array.from({ length: 5 }, (_, i) => i + 1).map((i) => {
              const y = 10 + (i / 5) * (size.height - 40);
              return (
                <line
                  key={i}
                  x1={56}
                  x2={size.width - 16}
                  y1={y}
                  y2={y}
                  stroke="#334155"
                  strokeDasharray="2 4"
                  strokeOpacity={0.4}
                />
              );
            })}

            {/* Volume scale hint */}
            <text
              x={size.width - 8}
              y={12}
              textAnchor="end"
              className="fill-terminal-text-muted text-[9px] font-mono"
            >
              {(maxVol / 1000).toFixed(1)}K
            </text>

            {/* bars */}
            {displayBins.map((b, i) => {
              const padL = 56;
              const padR = 16;
              const padT = 10;
              const padB = 20;
              const w = Math.max(1, size.width - padL - padR);
              const h = Math.max(1, size.height - padT - padB);
              const rowH = h / displayBins.length;

              const y = padT + i * rowH;
              const barW = (b.volume / maxVol) * w;
              const isPoc = poc && Math.abs(b.priceMid - poc.priceMid) < 1e-9;

              return (
                <g key={i}>
                  <rect
                    x={padL}
                    y={y + 1}
                    width={barW}
                    height={Math.max(1, rowH - 2)}
                    rx={2}
                    fill={isPoc ? 'url(#gradPoc)' : 'url(#gradVolNormal)'}
                    stroke={isPoc ? '#22d3ee' : 'transparent'}
                    strokeWidth={isPoc ? 1 : 0}
                  />
                  {/* Price labels on left */}
                  {i % 4 === 0 || i === displayBins.length - 1 ? (
                    <text
                      x={padL - 8}
                      y={y + rowH / 2 + 3}
                      className="fill-terminal-text-muted text-[10px] font-mono"
                      textAnchor="end"
                    >
                      ${b.priceMid.toFixed(2)}
                    </text>
                  ) : null}
                </g>
              );
            })}

            {/* POC indicator line */}
            {poc && displayBins.findIndex(b => Math.abs(b.priceMid - poc.priceMid) < 1e-9) >= 0 && (
              <line
                x1={56}
                x2={size.width - 16}
                y1={10 + (displayBins.findIndex(b => Math.abs(b.priceMid - poc.priceMid) < 1e-9) / displayBins.length) * (size.height - 40) + (size.height - 40) / displayBins.length / 2}
                y2={10 + (displayBins.findIndex(b => Math.abs(b.priceMid - poc.priceMid) < 1e-9) / displayBins.length) * (size.height - 40) + (size.height - 40) / displayBins.length / 2}
                stroke="#22d3ee"
                strokeWidth={1}
                strokeDasharray="3 3"
                strokeOpacity={0.4}
              />
            )}
          </svg>
        )}
      </div>
    </div>
  );
}
