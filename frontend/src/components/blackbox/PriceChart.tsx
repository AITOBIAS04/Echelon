// Price Chart Component
// Interactive candlestick chart with volume and indicators

import { useMemo, useRef, useEffect, useState } from 'react';
import type { Candle, ChartIndicators, Timeframe } from '../../types/blackbox';
import { CHART } from '../../constants/colors';

interface PriceChartProps {
  candles: Candle[];
  currentPrice: number;
  indicators: ChartIndicators;
  timeframe: Timeframe;
  onTimeframeChange: (tf: Timeframe) => void;
}

const TIMEFRAME_LABELS: Record<Timeframe, string> = {
  '1m': '1m',
  '5m': '5m',
  '15m': '15m',
  '1H': '1H',
  '4H': '4H',
  '1D': '1D',
};

export function PriceChart({
  candles,
  currentPrice,
  indicators,
  timeframe,
  onTimeframeChange,
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 800, height: 300 });
  const priceRange = useMemo(() => {
    if (candles.length === 0) return { min: 0, max: 10 };
    const highs = candles.map((c) => c.high);
    const lows = candles.map((c) => c.low);
    const min = Math.min(...lows);
    const max = Math.max(...highs);
    const padding = (max - min) * 0.1;
    return { min: min - padding, max: max + padding };
  }, [candles]);

  // Handle resize
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setContainerSize({ width: rect.width, height: rect.height });
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Generate grid lines
  const gridLines = useMemo(() => {
    const lines = [];
    const { min, max } = priceRange;
    const range = max - min;
    for (let i = 0; i <= 4; i++) {
      const y = (i / 4) * 100;
      const price = max - (range * i) / 4;
      lines.push({ y: `${y}%`, price });
    }
    return lines;
  }, [priceRange]);

  // Generate candles SVG
  const candlesSvg = useMemo(() => {
    if (candles.length === 0) return '';
    const candleWidth = containerSize.width / candles.length - 2;
    const range = priceRange.max - priceRange.min;
    const chartHeight = containerSize.height - 60; // Reserve space for volume

    return candles.map((candle, i) => {
      const x = (i / candles.length) * containerSize.width;
      const bodyTop = ((priceRange.max - Math.max(candle.open, candle.close)) / range) * chartHeight;
      const bodyHeight = Math.max(1, (Math.abs(candle.close - candle.open) / range) * chartHeight);
      const isUp = candle.close > candle.open;
      const color = isUp ? CHART.BID : CHART.ASK;

      return (
        <g key={i}>
          {/* Wick */}
          <line
            x1={x + candleWidth / 2}
            y1={((priceRange.max - candle.high) / range) * chartHeight}
            x2={x + candleWidth / 2}
            y2={((priceRange.max - candle.low) / range) * chartHeight}
            stroke={color}
            strokeWidth={1}
          />
          {/* Body */}
          <rect
            x={x}
            y={bodyTop}
            width={candleWidth}
            height={bodyHeight}
            fill={color}
          />
        </g>
      );
    });
  }, [candles, containerSize, priceRange]);

  // Generate volume bars
  const volumeBars = useMemo(() => {
    if (candles.length === 0) return '';
    const maxVolume = Math.max(...candles.map((c) => c.volume));
    const volumeHeight = 40;
    const barWidth = containerSize.width / candles.length - 1;

    return candles.map((candle, i) => {
      const x = i * (containerSize.width / candles.length);
      const barH = (candle.volume / maxVolume) * volumeHeight;
      const isUp = candle.close > candle.open;
      const color = isUp ? 'rgba(74, 222, 128, 0.3)' : 'rgba(239, 68, 68, 0.3)';

      return (
        <rect
          key={i}
          x={x}
          y={volumeHeight - barH}
          width={barWidth}
          height={barH}
          fill={color}
        />
      );
    });
  }, [candles, containerSize]);

  // Current price line position
  const priceLineY = useMemo(() => {
    const range = priceRange.max - priceRange.min;
    const chartHeight = containerSize.height - 60;
    return ((priceRange.max - currentPrice) / range) * chartHeight;
  }, [currentPrice, priceRange, containerSize]);

  const isPositive = currentPrice >= 3.74;

  return (
    <div className="rounded-2xl border border-terminal-border bg-terminal-panel flex flex-col min-h-0">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
        <span className="text-sm font-semibold text-terminal-text">PRICE ACTION</span>
        <div className="flex items-center gap-1">
          {(Object.keys(TIMEFRAME_LABELS) as Timeframe[]).map((tf) => (
            <button
              key={tf}
              onClick={() => onTimeframeChange(tf)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                timeframe === tf
                  ? 'bg-terminal-card text-terminal-text'
                  : 'text-terminal-text-muted hover:text-terminal-text-secondary hover:bg-terminal-card'
              }`}
            >
              {TIMEFRAME_LABELS[tf]}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Body */}
      <div
        ref={containerRef}
        className="flex-1 min-h-0 relative"
        style={{ minHeight: 200 }}
      >
        {/* Grid lines */}
        <svg
          className="absolute inset-0 w-full h-full"
          preserveAspectRatio="none"
        >
          {gridLines.map((line, i) => (
            <line
              key={i}
              x1="0"
              y1={line.y}
              x2="100%"
              y2={line.y}
              stroke={CHART.GRID}
              strokeDasharray="2 4"
            />
          ))}
          {/* Price labels */}
          {gridLines.filter((_, i) => i % 2 === 0).map((line, i) => (
            <text
              key={`label-${i}`}
              x="4"
              y={parseFloat(line.y) - 2}
              fill={CHART.LABEL}
              fontSize="10"
              fontFamily="JetBrains Mono"
            >
              ${line.price.toFixed(2)}
            </text>
          ))}
        </svg>

        {/* Candles */}
        <svg
          className="absolute inset-0 w-full h-full"
          preserveAspectRatio="none"
        >
          {candlesSvg}
        </svg>

        {/* Current price line */}
        <div
          className="absolute left-0 right-0 border-t border-dashed flex items-center"
          style={{
            top: priceLineY,
            borderColor: isPositive ? CHART.BID : CHART.ASK,
          }}
        >
          <span
            className="ml-auto px-2 py-0.5 text-xs text-white rounded"
            style={{
              background: isPositive ? CHART.BID : CHART.ASK,
            }}
          >
            ${currentPrice.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Volume bars */}
      <div
        className="h-10 flex items-end gap-0.5 pt-1"
        style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        }}
      >
        <svg width="100%" height="40" preserveAspectRatio="none">
          {volumeBars}
        </svg>
      </div>

      {/* Indicators Footer */}
      <div
        className="flex items-center justify-between px-4 py-2 text-xs"
        style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          background: 'rgba(8, 10, 14, 0.5)',
        }}
      >
        <div className="flex items-center gap-4">
          <span className="text-terminal-text-muted">
            RSI <span className="text-terminal-text">{indicators.rsi.toFixed(1)}</span>
          </span>
          <span className="text-terminal-text-muted">
            MACD <span className={indicators.macd >= 0 ? 'text-echelon-green' : 'text-echelon-red'}>
              {indicators.macd >= 0 ? '+' : ''}{indicators.macd.toFixed(2)}
            </span>
          </span>
          <span className="text-terminal-text-muted">
            VOL <span className="text-terminal-text">{(indicators.volume / 1000).toFixed(0)}K</span>
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-terminal-text-muted">
            H <span className="text-terminal-text">${indicators.high.toFixed(2)}</span>
          </span>
          <span className="text-terminal-text-muted">
            L <span className="text-terminal-text">${indicators.low.toFixed(2)}</span>
          </span>
        </div>
      </div>
    </div>
  );
}
