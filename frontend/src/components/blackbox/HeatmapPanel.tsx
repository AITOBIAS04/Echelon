import { useMemo, useRef, useEffect, useState } from 'react';
import { useTimeSales } from '../../hooks/useBlackbox';
import type { Trade } from '../../types/blackbox';
import { CHART } from '../../constants/colors';

type Cell = { r: number; c: number; v: number };

function buildHeatmap(trades: Trade[], cols = 30, rows = 28, windowMs = 60_000) {
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
    grid[(rows - 1) - r][c] += t.size;
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

  const hm = useMemo(() => buildHeatmap(trades, 32, 26, 60_000), [trades]);

  return (
    <div className="chart-container flex flex-col gap-4 min-h-[300px]" style={{ flex: '1 1 400px' }}>
      <div className="flex items-center justify-between flex-shrink-0">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">Market Heatmap</h3>
        <span className="text-[10px] font-mono text-terminal-text-muted">Last 60s</span>
      </div>

      <div ref={containerRef} className="flex-1 min-h-0 relative">
        {hm.cells.length === 0 ? (
          <div className="flex items-center justify-center h-full text-terminal-text-muted text-xs">Loading heatmap...</div>
        ) : (
          <svg width="100%" height="100%" className="overflow-visible">
            {/* Background grid */}
            <defs>
              <pattern id="heatmapGrid" x="0" y="0" width="100%" height="100%" patternUnits="userSpaceOnUse">
                <rect width="100%" height="100%" fill="#080A0E" fillOpacity="0.2" />
              </pattern>
            </defs>

            <rect x={56} y={14} width={size.width - 72} height={size.height - 32} fill="url(#heatmapGrid)" />

            {/* Cell grid lines (subtle) */}
            <g opacity={0.15}>
              {Array.from({ length: 8 }, (_, i) => i + 1).map((i) => {
                const x = 56 + (i / 8) * (size.width - 72);
                return <line key={`v${i}`} x1={x} x2={x} y1={14} y2={size.height - 18} stroke={CHART.GRID} strokeWidth={0.5} />;
              })}
              {Array.from({ length: 6 }, (_, i) => i + 1).map((i) => {
                const y = 14 + (i / 6) * (size.height - 32);
                return <line key={`h${i}`} x1={56} x2={size.width - 16} y1={y} y2={y} stroke={CHART.GRID} strokeWidth={0.5} />;
              })}
            </g>

            {/* Cells with gradient intensity */}
            {hm.cells.map((cell, i) => {
              const padL = 56;
              const padR = 16;
              const padT = 14;
              const padB = 18;
              const w = Math.max(1, size.width - padL - padR);
              const h = Math.max(1, size.height - padT - padB);
              const cw = w / hm.cols;
              const ch = h / hm.rows;

              const x = padL + cell.c * cw;
              const y = padT + cell.r * ch;

              const n = cell.v / hm.maxV;
              // Use cyan spectrum with varying opacity
              const alpha = n <= 0 ? 0 : 0.08 + 0.7 * Math.pow(n, 0.7);

              if (alpha === 0) return null;

              return (
                <rect
                  key={i}
                  x={x + 0.5}
                  y={y + 0.5}
                  width={Math.max(1, cw - 1)}
                  height={Math.max(1, ch - 1)}
                  fill={`rgba(34, 211, 238, ${alpha})`}
                  className="transition-colors duration-300"
                  rx={1.5}
                />
              );
            })}

            {/* Price axis labels */}
            <g className="text-[10px] font-mono fill-terminal-text-muted" textAnchor="end">
              <text x={48} y={14 + 8}>${hm.maxP.toFixed(2)}</text>
              <text x={48} y={14 + (size.height - 32) / 2 + 4}>${((hm.minP + hm.maxP) / 2).toFixed(2)}</text>
              <text x={48} y={size.height - 18 + 4}>${hm.minP.toFixed(2)}</text>
            </g>

            {/* Time axis labels */}
            <g className="text-[10px] font-mono fill-terminal-text-muted">
              <text x={56} y={size.height - 4} textAnchor="start">-60s</text>
              <text x={size.width - 16} y={size.height - 4} textAnchor="end">now</text>
            </g>

            {/* Border */}
            <rect
              x={56}
              y={14}
              width={size.width - 72}
              height={size.height - 32}
              fill="none"
              className="stroke-terminal-border"
              strokeOpacity={0.5}
              strokeWidth={1}
            />
          </svg>
        )}
      </div>
    </div>
  );
}
