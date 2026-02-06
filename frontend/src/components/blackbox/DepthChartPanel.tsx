import { useMemo, useRef, useEffect, useState } from 'react';
import { useOrderBook } from '../../hooks/useBlackbox';
import { CHART } from '../../constants/colors';

export function DepthChartPanel() {
  const orderBook = useOrderBook();
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

  const { bidsCum, asksCum, xMin, xMax, yMax } = useMemo(() => {
    if (!orderBook) {
      return {
        bidsCum: [] as Array<{ price: number; total: number }>,
        asksCum: [] as Array<{ price: number; total: number }>,
        xMin: 0,
        xMax: 1,
        yMax: 1,
      };
    }

    const bids = [...orderBook.bids].sort((a, b) => a.price - b.price);
    const asks = [...orderBook.asks].sort((a, b) => a.price - b.price);

    const bidsCum: Array<{ price: number; total: number }> = bids.map((b) => ({ price: b.price, total: b.total }));
    const asksCum: Array<{ price: number; total: number }> = asks.map((a) => ({ price: a.price, total: a.total }));

    const prices = [...bidsCum.map((p) => p.price), ...asksCum.map((p) => p.price)];
    const xMin = Math.min(...prices);
    const xMax = Math.max(...prices);

    const yMax = Math.max(
      bidsCum.length ? bidsCum[bidsCum.length - 1].total : 0,
      asksCum.length ? asksCum[asksCum.length - 1].total : 0,
      1
    );

    return { bidsCum, asksCum, xMin, xMax, yMax };
  }, [orderBook]);

  const chart = useMemo(() => {
    const width = size.width;
    const height = size.height;
    const pad = { l: 48, r: 16, t: 24, b: 24 }; // Increased left padding for labels, top for legend space
    const w = Math.max(1, width - pad.l - pad.r);
    const h = Math.max(1, height - pad.t - pad.b);
    const yBottom = pad.t + h;

    const xScale = (p: number) => pad.l + ((p - xMin) / Math.max(1e-9, xMax - xMin)) * w;
    const yScale = (v: number) => pad.t + (1 - v / yMax) * h;

    const toPathStep = (pts: Array<{ price: number; total: number }>) => {
      if (pts.length === 0) return '';
      let d = `M ${xScale(pts[0].price)} ${yScale(pts[0].total)}`;
      for (let i = 1; i < pts.length; i++) {
        const prev = pts[i - 1];
        const cur = pts[i];
        d += ` L ${xScale(cur.price)} ${yScale(prev.total)}`;
        d += ` L ${xScale(cur.price)} ${yScale(cur.total)}`;
      }
      return d;
    };

    const bidsPath = toPathStep(bidsCum);
    const asksPath = toPathStep(asksCum);

    const bidsFill = bidsCum.length > 0 
      ? `${bidsPath} L ${xScale(bidsCum[bidsCum.length - 1].price)} ${yBottom} L ${xScale(bidsCum[0].price)} ${yBottom} Z`
      : '';
    
    const asksFill = asksCum.length > 0
      ? `${asksPath} L ${xScale(asksCum[asksCum.length - 1].price)} ${yBottom} L ${xScale(asksCum[0].price)} ${yBottom} Z`
      : '';

    const gridLines = Array.from({ length: 5 }, (_, i) => i + 1).map((i) => {
      const y = pad.t + (i / 5) * h;
      return y;
    });

    const xLabels = [xMin, (xMin + xMax) / 2, xMax].map((p) => ({ p, x: xScale(p) }));
    const yLabels = [0, yMax / 4, yMax / 2, yMax * 0.75, yMax].map((v) => ({ v, y: yScale(v) }));

    const mid = orderBook?.midPrice ?? (xMin + xMax) / 2;
    const midX = xScale(mid);

    return { bidsPath, asksPath, bidsFill, asksFill, gridLines, xLabels, yLabels, midX, pad, w, h };
  }, [size, bidsCum, asksCum, xMin, xMax, yMax, orderBook]);

  return (
    <div className="chart-container flex flex-col gap-4 min-h-[300px]" style={{ flex: '1 1 400px' }}>
      <div className="flex items-center justify-between flex-shrink-0">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">Depth Chart</h3>
        {orderBook ? (
          <span className="text-[10px] font-mono text-terminal-text-muted">
            Spread ${orderBook.spread.toFixed(3)} ({orderBook.spreadPercent.toFixed(2)}%)
          </span>
        ) : null}
      </div>

      <div ref={containerRef} className="flex-1 min-h-0 relative">
        {!orderBook ? (
          <div className="flex items-center justify-center h-full text-terminal-text-muted text-xs">Loading depth...</div>
        ) : (
          <svg width="100%" height="100%" className="overflow-visible">
            <defs>
              <linearGradient id="gradBids" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={CHART.BID} stopOpacity="0.2" />
                <stop offset="100%" stopColor={CHART.BID} stopOpacity="0.05" />
              </linearGradient>
              <linearGradient id="gradAsks" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={CHART.ASK} stopOpacity="0.2" />
                <stop offset="100%" stopColor={CHART.ASK} stopOpacity="0.05" />
              </linearGradient>
            </defs>

            {/* Legend */}
            <g transform={`translate(${size.width - 100}, ${chart.pad.t - 15})`}>
              <rect width="10" height="10" fill={CHART.BID} fillOpacity="0.8" rx="2" />
              <text x="14" y="9" className="fill-terminal-text text-[10px] font-medium">Bids</text>
              
              <rect x="45" width="10" height="10" fill={CHART.ASK} fillOpacity="0.8" rx="2" />
              <text x="59" y="9" className="fill-terminal-text text-[10px] font-medium">Asks</text>
            </g>

            {/* grid */}
            {chart.gridLines.map((y, i) => (
              <line
                key={i}
                x1={chart.pad.l}
                x2={chart.pad.l + chart.w}
                y1={y}
                y2={y}
                stroke={CHART.GRID}
                strokeWidth={1}
                strokeDasharray="4 4"
                strokeOpacity={0.4}
              />
            ))}
            
            {/* Axis Titles */}
            <text 
              x={chart.pad.l - 40} 
              y={chart.pad.t + chart.h / 2} 
              transform={`rotate(-90, ${chart.pad.l - 40}, ${chart.pad.t + chart.h / 2})`}
              className="fill-terminal-text-muted text-[10px] font-mono opacity-50"
              textAnchor="middle"
            >
              Cumulative Vol
            </text>

            {/* axes labels */}
            {chart.yLabels.map((l, i) => (
              <text
                key={`yl-${i}`}
                x={chart.pad.l - 8}
                y={l.y + 3}
                className="fill-terminal-text-muted text-[10px] font-mono"
                textAnchor="end"
              >
                {(l.v / 1000).toFixed(1)}K
              </text>
            ))}
            {chart.xLabels.map((l, i) => (
              <text
                key={`xl-${i}`}
                x={l.x}
                y={size.height - 4}
                textAnchor={i === 0 ? 'start' : i === 2 ? 'end' : 'middle'}
                className="fill-terminal-text-muted text-[10px] font-mono"
              >
                ${l.p.toFixed(2)}
              </text>
            ))}

            {/* mid line */}
            <line
              x1={chart.midX}
              x2={chart.midX}
              y1={chart.pad.t}
              y2={chart.pad.t + chart.h}
              className="stroke-status-info"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              strokeOpacity={0.6}
            />
            {/* Mid Label */}
            <text
              x={chart.midX}
              y={chart.pad.t - 5}
              textAnchor="middle"
              className="fill-status-info text-[10px] font-mono font-semibold"
            >
              Mid
            </text>

            {/* areas */}
            <path d={chart.bidsFill} fill="url(#gradBids)" />
            <path d={chart.asksFill} fill="url(#gradAsks)" />

            {/* lines */}
            <path d={chart.bidsPath} fill="none" stroke={CHART.BID} strokeWidth={2} strokeLinejoin="round" />
            <path d={chart.asksPath} fill="none" stroke={CHART.ASK} strokeWidth={2} strokeLinejoin="round" />
          </svg>
        )}
      </div>
    </div>
  );
}
