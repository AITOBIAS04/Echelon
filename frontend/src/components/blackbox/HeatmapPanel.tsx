import { useMemo, useRef, useEffect, useState } from 'react';
import { useTimeSales } from '../../hooks/useBlackbox';
import type { Trade } from '../../types/blackbox';

type Cell = { r: number; c: number; v: number };

function buildHeatmap(trades: Trade[], cols = 18, rows = 24, windowMs = 60_000) {
  const now = Date.now();
  const recent = trades.filter((t) => now - t.timestamp.getTime() <= windowMs);
  if (recent.length === 0) return { cells: [] as Cell[], rows, cols, minP: 0, maxP: 1, maxV: 1 };

  const prices = recent.map((t) => t.price);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const priceRange = Math.max(1e-6, maxP - minP);

  const grid = Array.from({ length: rows }, () => Array.from({ length: cols }, () => 0));

  for (const t of recent) {
    const age = now - t.timestamp.getTime();
    const c = Math.min(cols - 1, Math.max(0, Math.floor(((windowMs - age) / windowMs) * cols)));
    const r = Math.min(rows - 1, Math.max(0, Math.floor(((t.price - minP) / priceRange) * rows)));
    grid[(rows - 1) - r][c] += t.size; // invert so higher prices top
  }

  let maxV = 1;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) maxV = Math.max(maxV, grid[r][c]);

  const cells: Cell[] = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) cells.push({ r, c, v: grid[r][c] });

  return { cells, rows, cols, minP, maxP, maxV };
}

export function HeatmapPanel() {
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

  const hm = useMemo(() => buildHeatmap(trades, 20, 24, 60_000), [trades]);

  return (
    <div className="panel chart-container" style={{ flex: '0 0 45%', minHeight: 250 }}>
      <div className="panel-header">
        <span className="panel-title">HEATMAP</span>
        <span className="text-[10px] font-mono text-terminal-text-muted">Last 60s</span>
      </div>

      <div ref={containerRef} className="chart-main" style={{ position: 'relative', height: 320, minHeight: 240 }}>
        {hm.cells.length === 0 ? (
          <div className="flex items-center justify-center h-full text-terminal-muted">Loading heatmap…</div>
        ) : (
          <svg width="100%" height="100%" preserveAspectRatio="none">
            {hm.cells.map((cell, i) => {
              const padL = 56;
              const padR = 16;
              const padT = 16;
              const padB = 28;
              const w = Math.max(1, size.width - padL - padR);
              const h = Math.max(1, size.height - padT - padB);
              const cw = w / hm.cols;
              const ch = h / hm.rows;

              const x = padL + cell.c * cw;
              const y = padT + cell.r * ch;

              const n = cell.v / hm.maxV; // 0..1
              const alpha = n <= 0 ? 0 : 0.05 + 0.55 * n;

              return (
                <rect
                  key={i}
                  x={x}
                  y={y}
                  width={Math.max(1, cw)}
                  height={Math.max(1, ch)}
                  fill={`rgba(34, 211, 238, ${alpha})`}
                  stroke="rgba(38, 41, 46, 0.55)"
                  strokeWidth={0.5}
                />
              );
            })}

            {/* Price labels (top/mid/bottom) */}
            <text x={6} y={18} fill="#64748B" fontSize="10" fontFamily="JetBrains Mono">
              ${hm.maxP.toFixed(2)}
            </text>
            <text x={6} y={size.height / 2} fill="#64748B" fontSize="10" fontFamily="JetBrains Mono">
              ${((hm.minP + hm.maxP) / 2).toFixed(2)}
            </text>
            <text x={6} y={size.height - 14} fill="#64748B" fontSize="10" fontFamily="JetBrains Mono">
              ${hm.minP.toFixed(2)}
            </text>

            {/* Time labels */}
            <text x={size.width - 16} y={size.height - 10} fill="#64748B" fontSize="10" fontFamily="JetBrains Mono" textAnchor="end">
              now
            </text>
            <text x={56} y={size.height - 10} fill="#64748B" fontSize="10" fontFamily="JetBrains Mono">
              -60s
            </text>
          </svg>
        )}
      </div>
    </div>
  );
}
