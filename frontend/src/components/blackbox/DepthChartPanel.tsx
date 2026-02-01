import { useMemo, useRef, useEffect, useState } from 'react';
import { useOrderBook } from '../../hooks/useBlackbox';

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
    const pad = { l: 44, r: 16, t: 18, b: 28 };
    const w = Math.max(1, width - pad.l - pad.r);
    const h = Math.max(1, height - pad.t - pad.b);

    const xScale = (p: number) => pad.l + ((p - xMin) / Math.max(1e-9, xMax - xMin)) * w;
    const yScale = (v: number) => pad.t + (1 - v / yMax) * h;

    const toPathStep = (pts: Array<{ price: number; total: number }>) => {
      if (pts.length === 0) return '';
      let d = `M ${xScale(pts[0].price)} ${yScale(pts[0].total)}`;
      for (let i = 1; i < pts.length; i++) {
        const prev = pts[i - 1];
        const cur = pts[i];
        // step: horizontal then vertical
        d += ` L ${xScale(cur.price)} ${yScale(prev.total)}`;
        d += ` L ${xScale(cur.price)} ${yScale(cur.total)}`;
      }
      return d;
    };

    const bidsPath = toPathStep(bidsCum);
    const asksPath = toPathStep(asksCum);

    const gridLines = Array.from({ length: 4 }, (_, i) => i + 1).map((i) => {
      const y = pad.t + (i / 4) * h;
      return y;
    });

    const xLabels = [xMin, (xMin + xMax) / 2, xMax].map((p) => ({ p, x: xScale(p) }));
    const yLabels = [0, yMax / 2, yMax].map((v) => ({ v, y: yScale(v) }));

    const mid = orderBook?.midPrice ?? (xMin + xMax) / 2;
    const midX = xScale(mid);

    return { bidsPath, asksPath, gridLines, xLabels, yLabels, midX, pad, w, h };
  }, [size, bidsCum, asksCum, xMin, xMax, yMax, orderBook]);

  return (
    <div className="panel chart-container" style={{ flex: '0 0 45%', minHeight: 250 }}>
      <div className="panel-header">
        <span className="panel-title">DEPTH CHART</span>
        {orderBook ? (
          <span className="text-[10px] font-mono text-terminal-text-muted">
            Spread ${orderBook.spread.toFixed(3)} ({orderBook.spreadPercent.toFixed(2)}%)
          </span>
        ) : null}
      </div>

      <div ref={containerRef} className="chart-main" style={{ position: 'relative', height: 320, minHeight: 240 }}>
        {!orderBook ? (
          <div className="flex items-center justify-center h-full text-terminal-muted">Loading depth…</div>
        ) : (
          <svg width="100%" height="100%" preserveAspectRatio="none">
            {/* grid */}
            {chart.gridLines.map((y, i) => (
              <line
                key={i}
                x1={chart.pad.l}
                x2={chart.pad.l + chart.w}
                y1={y}
                y2={y}
                stroke="rgba(54, 58, 64, 0.5)"
                strokeDasharray="2 4"
              />
            ))}

            {/* axes labels */}
            {chart.yLabels.map((l, i) => (
              <text
                key={`yl-${i}`}
                x={6}
                y={l.y + 3}
                fill="#64748B"
                fontSize="10"
                fontFamily="JetBrains Mono"
              >
                {(l.v / 1000).toFixed(0)}K
              </text>
            ))}
            {chart.xLabels.map((l, i) => (
              <text
                key={`xl-${i}`}
                x={l.x}
                y={size.height - 10}
                textAnchor={i === 0 ? 'start' : i === 2 ? 'end' : 'middle'}
                fill="#64748B"
                fontSize="10"
                fontFamily="JetBrains Mono"
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
              stroke="rgba(34, 211, 238, 0.25)"
            />

            {/* paths */}
            <path d={chart.bidsPath} fill="none" stroke="#4ADE80" strokeWidth={2} />
            <path d={chart.asksPath} fill="none" stroke="#FB7185" strokeWidth={2} />
          </svg>
        )}
      </div>
    </div>
  );
}
