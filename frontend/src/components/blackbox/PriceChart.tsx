// Price Chart Component
// Interactive candlestick chart with volume and indicators

import { useMemo, useRef, useEffect, useState } from 'react';
import type { Candle, ChartIndicators, Timeframe } from '../../types/blackbox';

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
      const color = isUp ? '#4ADE80' : '#FB7185';

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
      const color = isUp ? 'rgba(74, 222, 128, 0.3)' : 'rgba(251, 113, 133, 0.3)';

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
    <div className="panel chart-container" style={{ flex: '0 0 45%', minHeight: 250 }}>
      <div className="panel-header">
        <span className="panel-title">PRICE ACTION</span>
        <div className="panel-controls">
          {(Object.keys(TIMEFRAME_LABELS) as Timeframe[]).map((tf) => (
            <button
              key={tf}
              className={`timeframe-btn ${timeframe === tf ? 'active' : ''}`}
              onClick={() => onTimeframeChange(tf)}
            >
              {TIMEFRAME_LABELS[tf]}
            </button>
          ))}
        </div>
      </div>

      <div
        ref={containerRef}
        className="chart-main"
        style={{ position: 'relative', height: containerSize.height - 60, minHeight: 200 }}
      >
        {/* Grid lines */}
        <svg
          style={{ position: 'absolute', width: '100%', height: containerSize.height - 60 }}
          preserveAspectRatio="none"
        >
          {gridLines.map((line, i) => (
            <line
              key={i}
              x1="0"
              y1={line.y}
              x2="100%"
              y2={line.y}
stroke="rgba(54, 58, 64, 0.5)"
              strokeDasharray="2 4"
            />
          ))}
          {/* Price labels */}
          {gridLines.filter((_, i) => i % 2 === 0).map((line, i) => (
            <text
              key={`label-${i}`}
              x="4"
              y={parseFloat(line.y) - 2}
              fill="#64748B"
              fontSize="10"
              fontFamily="JetBrains Mono"
            >
              ${line.price.toFixed(2)}
            </text>
          ))}
        </svg>

        {/* Candles */}
        <svg
          style={{ position: 'absolute', width: '100%', height: containerSize.height - 60 }}
          preserveAspectRatio="none"
        >
          {candlesSvg}
        </svg>

        {/* Current price line */}
        <div
          className="current-price-line"
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: priceLineY,
            borderTop: `1px dashed ${isPositive ? '#4ADE80' : '#FB7185'}`,
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <span
            className="current-price-label"
            style={{
              marginLeft: 'auto',
              background: isPositive ? '#4ADE80' : '#FB7185',
              color: 'white',
              padding: '2px 6px',
              borderRadius: 2,
              fontSize: 10,
            }}
          >
            ${currentPrice.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Volume bars */}
      <div
        className="volume-bars"
        style={{
          height: 40,
          borderTop: '1px solid rgba(54, 58, 64, 0.5)',
          display: 'flex',
          alignItems: 'flex-end',
          paddingTop: 4,
          gap: 1,
        }}
      >
        <svg width="100%" height="40" preserveAspectRatio="none">
          {volumeBars}
        </svg>
      </div>

      {/* Indicators */}
      <div
        className="chart-indicators"
        style={{
          borderTop: '1px solid var(--border-outer)',
          padding: '4px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 10,
          background: 'rgba(18, 20, 23, 0.5)',
        }}
      >
        <div className="indicator-item">
          <span className="indicator-label">RSI</span>{' '}
          <span className="indicator-val">{indicators.rsi.toFixed(1)}</span>
        </div>
        <div className="indicator-item">
          <span className="indicator-label">MACD</span>{' '}
          <span className={`indicator-val ${indicators.macd >= 0 ? 'positive' : 'negative'}`}>
            {indicators.macd >= 0 ? '+' : ''}
            {indicators.macd.toFixed(2)}
          </span>
        </div>
        <div className="indicator-item">
          <span className="indicator-label">VOL</span>{' '}
          <span className="indicator-val">{(indicators.volume / 1000).toFixed(0)}K</span>
        </div>
        <div className="indicator-item">
          <span className="indicator-label">H</span>{' '}
          <span className="indicator-val">${indicators.high.toFixed(2)}</span>
          <span className="indicator-label" style={{ marginLeft: 4 }}>
            L
          </span>{' '}
          <span className="indicator-val">${indicators.low.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}
