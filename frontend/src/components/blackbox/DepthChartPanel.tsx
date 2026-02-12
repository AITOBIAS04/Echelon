/**
 * LMSR Impact Curve Panel
 *
 * Renders a "Cost to Move" chart showing how much it costs to shift the
 * market probability by a given delta.  X-axis = Target Probability (%),
 * Y-axis = Cost ($).  Single smooth cyan curve, interactive hover tooltip,
 * and a cost-to-move calculator strip below the chart.
 *
 * No order-book artifacts — this is pure CFPM/LMSR.
 */

import { useMemo, useRef, useEffect, useState, useCallback } from 'react';
import { CHART } from '../../constants/colors';
import { lmsrCost, lmsrCostCurve, LIQUIDITY_B } from '../../lib/lmsr';
import { Zap } from 'lucide-react';

// ── Types ───────────────────────────────────────────────────────────────

interface ImpactCurveChartProps {
  currentPrice: number;
}

// ── Component ───────────────────────────────────────────────────────────

export function DepthChartPanel({ currentPrice }: ImpactCurveChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 800, height: 280 });
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  // Current probability derived from price
  const currentProb = Math.min(Math.max(currentPrice / 100, 0.01), 0.99);
  const probPercent = (currentProb * 100).toFixed(1);

  // Generate curve data
  const curveData = useMemo(() => lmsrCostCurve(currentProb), [currentProb]);
  const maxCost = useMemo(() => Math.max(...curveData.map((p) => p.cost), 1), [curveData]);

  // Cost for the calculator strip (+5% move)
  const calcTarget = Math.min(currentProb + 0.05, 0.98);
  const calcCost = lmsrCost(currentProb, calcTarget, LIQUIDITY_B);

  // ── Resize observer ─────────────────────────────────────────────────
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const update = () => {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        setSize({ width: rect.width, height: rect.height });
      }
    };
    update();

    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // ── Chart geometry ──────────────────────────────────────────────────
  const chart = useMemo(() => {
    const { width, height } = size;
    const pad = { l: 56, r: 20, t: 16, b: 32 };
    const w = Math.max(1, width - pad.l - pad.r);
    const h = Math.max(1, height - pad.t - pad.b);

    const xMin = curveData[0]?.targetProb ?? 0;
    const xMax = curveData[curveData.length - 1]?.targetProb ?? 1;
    const yMax = maxCost * 1.1; // 10% headroom

    const xScale = (prob: number) => pad.l + ((prob - xMin) / Math.max(1e-9, xMax - xMin)) * w;
    const yScale = (cost: number) => pad.t + (1 - cost / yMax) * h;
    const yBottom = pad.t + h;

    // Build SVG path
    const curvePath = curveData
      .map((pt, i) => `${i === 0 ? 'M' : 'L'} ${xScale(pt.targetProb).toFixed(2)} ${yScale(pt.cost).toFixed(2)}`)
      .join(' ');

    // Fill path (closed to bottom)
    const fillPath = curveData.length > 0
      ? `${curvePath} L ${xScale(curveData[curveData.length - 1].targetProb).toFixed(2)} ${yBottom} L ${xScale(curveData[0].targetProb).toFixed(2)} ${yBottom} Z`
      : '';

    // Grid — 4 horizontal lines
    const hGridLines = Array.from({ length: 4 }, (_, i) => {
      const val = (yMax / 5) * (i + 1);
      return { y: yScale(val), label: `$${val.toFixed(0)}` };
    });

    // Grid — 5 vertical lines (probability ticks)
    const xRange = xMax - xMin;
    const vGridLines = Array.from({ length: 5 }, (_, i) => {
      const prob = xMin + (xRange / 6) * (i + 1);
      return { x: xScale(prob), label: `${(prob * 100).toFixed(0)}%` };
    });

    // X-axis labels (edges + centre)
    const xLabels = [
      { prob: xMin, x: xScale(xMin), anchor: 'start' as const },
      { prob: (xMin + xMax) / 2, x: xScale((xMin + xMax) / 2), anchor: 'middle' as const },
      { prob: xMax, x: xScale(xMax), anchor: 'end' as const },
    ];

    // Current probability marker
    const currentX = xScale(currentProb);

    return { pad, w, h, yBottom, curvePath, fillPath, hGridLines, vGridLines, xLabels, currentX, xScale, yScale, xMin, xMax, yMax };
  }, [size, curveData, maxCost, currentProb]);

  // ── Hover handler ───────────────────────────────────────────────────
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      const svg = e.currentTarget;
      const rect = svg.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;

      // Find nearest curve point
      let closest = 0;
      let closestDist = Infinity;
      for (let i = 0; i < curveData.length; i++) {
        const px = chart.xScale(curveData[i].targetProb);
        const dist = Math.abs(px - mouseX);
        if (dist < closestDist) {
          closestDist = dist;
          closest = i;
        }
      }
      setHoverIdx(closestDist < 40 ? closest : null);
    },
    [curveData, chart],
  );

  const handleMouseLeave = useCallback(() => setHoverIdx(null), []);

  // Hover point data
  const hoverPoint = hoverIdx !== null ? curveData[hoverIdx] : null;
  const hoverX = hoverPoint ? chart.xScale(hoverPoint.targetProb) : 0;
  const hoverY = hoverPoint ? chart.yScale(hoverPoint.cost) : 0;

  return (
    <div className="chart-container flex flex-col gap-3 min-h-[300px]" style={{ flex: '1 1 400px' }}>
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
            Impact Curve
          </h3>
          <span className="chip chip-info text-[9px]">LMSR</span>
        </div>
        <span className="text-[10px] font-mono tabular-nums text-terminal-text-muted">
          Current: {probPercent}% &middot; b={LIQUIDITY_B}
        </span>
      </div>

      {/* ── SVG Chart ──────────────────────────────────────────────── */}
      <div ref={containerRef} className="flex-1 min-h-0 relative">
        <svg
          width="100%"
          height="100%"
          className="overflow-visible"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          <defs>
            <linearGradient id="gradImpactCurve" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART.COST_CURVE} stopOpacity="0.12" />
              <stop offset="100%" stopColor={CHART.COST_CURVE} stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Horizontal grid */}
          {chart.hGridLines.map((line, i) => (
            <g key={`hg-${i}`}>
              <line
                x1={chart.pad.l}
                x2={chart.pad.l + chart.w}
                y1={line.y}
                y2={line.y}
                stroke={CHART.GRID}
                strokeWidth={1}
                strokeDasharray="4 4"
                strokeOpacity={0.4}
              />
              <text
                x={chart.pad.l - 8}
                y={line.y + 3}
                textAnchor="end"
                className="fill-terminal-text-muted text-[10px] font-mono"
              >
                {line.label}
              </text>
            </g>
          ))}

          {/* Vertical grid */}
          {chart.vGridLines.map((line, i) => (
            <line
              key={`vg-${i}`}
              x1={line.x}
              x2={line.x}
              y1={chart.pad.t}
              y2={chart.yBottom}
              stroke={CHART.GRID}
              strokeWidth={1}
              strokeDasharray="4 4"
              strokeOpacity={0.25}
            />
          ))}

          {/* X-axis labels */}
          {chart.xLabels.map((l, i) => (
            <text
              key={`xl-${i}`}
              x={l.x}
              y={chart.yBottom + 18}
              textAnchor={l.anchor}
              className="fill-terminal-text-muted text-[10px] font-mono"
            >
              {(l.prob * 100).toFixed(0)}%
            </text>
          ))}

          {/* Y-axis title */}
          <text
            x={chart.pad.l - 44}
            y={chart.pad.t + chart.h / 2}
            transform={`rotate(-90, ${chart.pad.l - 44}, ${chart.pad.t + chart.h / 2})`}
            className="fill-terminal-text-muted text-[10px] font-mono opacity-50"
            textAnchor="middle"
          >
            Cost ($)
          </text>

          {/* X-axis title */}
          <text
            x={chart.pad.l + chart.w / 2}
            y={chart.yBottom + 28}
            className="fill-terminal-text-muted text-[10px] font-mono opacity-50"
            textAnchor="middle"
          >
            Target Probability
          </text>

          {/* Filled area under curve */}
          <path d={chart.fillPath} fill="url(#gradImpactCurve)" />

          {/* Curve line */}
          <path
            d={chart.curvePath}
            fill="none"
            stroke={CHART.COST_CURVE}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Current probability vertical marker */}
          <line
            x1={chart.currentX}
            x2={chart.currentX}
            y1={chart.pad.t}
            y2={chart.yBottom}
            className="stroke-status-info"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            strokeOpacity={0.6}
          />
          <text
            x={chart.currentX}
            y={chart.pad.t - 4}
            textAnchor="middle"
            className="fill-status-info text-[10px] font-mono font-semibold"
          >
            Current
          </text>

          {/* Hover crosshair + dot */}
          {hoverPoint && (
            <>
              {/* Vertical crosshair */}
              <line
                x1={hoverX}
                x2={hoverX}
                y1={chart.pad.t}
                y2={chart.yBottom}
                stroke={CHART.COST_CURVE}
                strokeWidth={1}
                strokeDasharray="2 2"
                strokeOpacity={0.4}
              />
              {/* Horizontal crosshair */}
              <line
                x1={chart.pad.l}
                x2={chart.pad.l + chart.w}
                y1={hoverY}
                y2={hoverY}
                stroke={CHART.COST_CURVE}
                strokeWidth={1}
                strokeDasharray="2 2"
                strokeOpacity={0.4}
              />
              {/* Dot */}
              <circle
                cx={hoverX}
                cy={hoverY}
                r={4}
                fill={CHART.COST_CURVE}
                stroke="#030305"
                strokeWidth={2}
              />
              {/* Tooltip background */}
              <rect
                x={hoverX + (hoverX > size.width / 2 ? -130 : 12)}
                y={hoverY - 24}
                width={118}
                height={26}
                rx={6}
                fill="#10141A"
                fillOpacity={0.95}
                stroke={CHART.COST_CURVE}
                strokeWidth={1}
                strokeOpacity={0.3}
              />
              {/* Tooltip text */}
              <text
                x={hoverX + (hoverX > size.width / 2 ? -71 : 71)}
                y={hoverY - 7}
                textAnchor="middle"
                className="text-[11px] font-mono font-semibold"
                fill={CHART.COST_CURVE}
              >
                &rarr; {(hoverPoint.targetProb * 100).toFixed(1)}% | ${hoverPoint.cost.toFixed(2)}
              </text>
            </>
          )}
        </svg>
      </div>

      {/* ── Cost-to-move calculator strip ──────────────────────────── */}
      <div className="flex-shrink-0 bg-terminal-card/50 border border-terminal-border/50 rounded-lg px-4 py-2.5 flex items-center gap-3">
        <Zap className="w-3.5 h-3.5 text-echelon-amber flex-shrink-0" />
        <div className="flex items-center gap-1.5 text-xs">
          <span className="data-label">To move</span>
          <span className="font-mono tabular-nums text-echelon-cyan font-semibold">{probPercent}%</span>
          <span className="text-terminal-text-muted">&rarr;</span>
          <span className="font-mono tabular-nums text-echelon-green font-semibold">{(calcTarget * 100).toFixed(1)}%</span>
          <span className="data-label">costs</span>
          <span className="font-mono tabular-nums text-terminal-text font-bold text-sm">${calcCost.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}
