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

  const bins = useMemo(() => computeBins(trades, 26), [trades]);
  const maxVol = useMemo(() => Math.max(1, ...bins.map((b) => b.volume)), [bins]);
  const poc = useMemo(() => {
    if (bins.length === 0) return null;
    return bins.reduce((acc, cur) => (cur.volume > acc.volume ? cur : acc), bins[0]);
  }, [bins]);

  return (
    <div className="panel chart-container" style={{ flex: '0 0 45%', minHeight: 250 }}>
      <div className="panel-header">
        <span className="panel-title">VOLUME PROFILE</span>
        {poc ? (
          <span className="text-[10px] font-mono text-terminal-text-muted">
            POC ${poc.priceMid.toFixed(2)}
          </span>
        ) : null}
      </div>

      <div ref={containerRef} className="chart-main" style={{ position: 'relative', height: 320, minHeight: 240 }}>
        {bins.length === 0 ? (
          <div className="flex items-center justify-center h-full text-terminal-muted">Loading volume…</div>
        ) : (
          <svg width="100%" height="100%" preserveAspectRatio="none">
            {/* grid */}
            {Array.from({ length: 4 }, (_, i) => i + 1).map((i) => {
              const y = 16 + (i / 4) * (size.height - 44);
              return (
                <line
                  key={i}
                  x1={56}
                  x2={size.width - 16}
                  y1={y}
                  y2={y}
                  stroke="rgba(54, 58, 64, 0.5)"
                  strokeDasharray="2 4"
                />
              );
            })}

            {/* bars */}
            {bins.map((b, i) => {
              const padL = 56;
              const padR = 16;
              const padT = 16;
              const padB = 28;
              const w = Math.max(1, size.width - padL - padR);
              const h = Math.max(1, size.height - padT - padB);
              const rowH = h / bins.length;

              const y = padT + i * rowH + 2;
              const barW = (b.volume / maxVol) * w;
              const isPoc = poc && Math.abs(b.priceMid - poc.priceMid) < 1e-9;

              return (
                <g key={i}>
                  <rect
                    x={padL}
                    y={y}
                    width={barW}
                    height={Math.max(1, rowH - 4)}
                    fill={isPoc ? 'rgba(34, 211, 238, 0.45)' : 'rgba(148, 163, 184, 0.20)'}
                  />
                  {i % 4 === 0 ? (
                    <text
                      x={6}
                      y={y + 10}
                      fill="#64748B"
                      fontSize="10"
                      fontFamily="JetBrains Mono"
                    >
                      ${b.priceMid.toFixed(2)}
                    </text>
                  ) : null}
                </g>
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
}
