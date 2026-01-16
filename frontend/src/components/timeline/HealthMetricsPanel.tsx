import { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
  Area,
  AreaChart,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import type { TimelineHealthSnapshot } from '../../types/timeline-detail';

/**
 * HealthMetricsPanel Props
 */
export interface HealthMetricsPanelProps {
  /** Historical health snapshots */
  history: TimelineHealthSnapshot[];
  /** Current stability value */
  currentStability: number;
  /** Current logic gap value */
  currentLogicGap: number;
  /** Current entropy rate value */
  currentEntropyRate: number;
}

type TimeRange = '24H' | '7D';

/**
 * Filter history by time range
 */
function filterHistoryByRange(
  history: TimelineHealthSnapshot[],
  range: TimeRange
): TimelineHealthSnapshot[] {
  if (history.length === 0) return [];
  
  const now = new Date().getTime();
  const rangeMs = range === '24H' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000;
  const cutoffTime = now - rangeMs;
  
  return history.filter((snapshot) => {
    const snapshotTime = new Date(snapshot.timestamp).getTime();
    return snapshotTime >= cutoffTime;
  });
}

/**
 * Format timestamp for X-axis
 */
function formatTimestamp(timestamp: string, range: TimeRange): string {
  const date = new Date(timestamp);
  if (range === '24H') {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Custom tooltip component
 */
function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#1A1A1A] border border-[#333] rounded p-2 text-xs">
        <p className="text-[#666] mb-1">{label}</p>
        <p className="text-white font-mono">
          {payload[0].value.toFixed(1)}
          {payload[0].dataKey === 'entropyRate' ? '%/hr' : '%'}
        </p>
      </div>
    );
  }
  return null;
}

/**
 * HealthMetricsPanel Component
 * 
 * Displays three time-series charts for timeline health metrics:
 * - Stability (green line with danger zones)
 * - Logic Gap (amber/red line with reference lines)
 * - Entropy Rate (purple line)
 */
export function HealthMetricsPanel({
  history,
  currentStability,
  currentLogicGap,
  currentEntropyRate,
}: HealthMetricsPanelProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>('24H');
  
  // Filter history based on selected time range
  const filteredHistory = useMemo(
    () => filterHistoryByRange(history, timeRange),
    [history, timeRange]
  );
  
  // Prepare chart data
  const chartData = filteredHistory.map((snapshot) => ({
    timestamp: snapshot.timestamp,
    stability: snapshot.stability,
    logicGap: snapshot.logicGap,
    entropyRate: snapshot.entropyRate,
  }));
  
  // Determine Logic Gap line color
  const logicGapColor = currentLogicGap >= 50 ? '#FF3B3B' : '#FF9500';
  
  return (
    <div className="bg-[#111111] rounded-lg p-4">
      {/* Header with time range toggle */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
          Health Metrics
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setTimeRange('24H')}
            className={`px-3 py-1 text-xs rounded transition ${
              timeRange === '24H'
                ? 'bg-terminal-panel border border-[#00FF41] text-[#00FF41]'
                : 'bg-terminal-bg border border-[#333] text-terminal-muted hover:text-terminal-text'
            }`}
          >
            24H
          </button>
          <button
            onClick={() => setTimeRange('7D')}
            className={`px-3 py-1 text-xs rounded transition ${
              timeRange === '7D'
                ? 'bg-terminal-panel border border-[#00FF41] text-[#00FF41]'
                : 'bg-terminal-bg border border-[#333] text-terminal-muted hover:text-terminal-text'
            }`}
          >
            7D
          </button>
        </div>
      </div>
      
      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Chart 1: Stability */}
        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-terminal-text uppercase">STABILITY</h4>
            <span className="text-xs font-mono text-[#00FF41]">
              {currentStability.toFixed(1)}%
            </span>
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="stabilityGreen" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00FF41" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#00FF41" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="stabilityAmber" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#FF9500" stopOpacity={0.1} />
                  <stop offset="100%" stopColor="#FF9500" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="stabilityRed" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#FF3B3B" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#FF3B3B" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1A1A1A" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => formatTimestamp(value, timeRange)}
                tick={{ fill: '#666666', fontSize: 10 }}
                axisLine={{ stroke: '#1A1A1A' }}
                tickLine={{ stroke: '#1A1A1A' }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#666666', fontSize: 10 }}
                axisLine={{ stroke: '#1A1A1A' }}
                tickLine={{ stroke: '#1A1A1A' }}
              />
              <Tooltip content={<CustomTooltip />} />
              {/* Red area below 30% */}
              <ReferenceArea y1={0} y2={30} fill="#FF3B3B" fillOpacity={0.2} />
              {/* Amber area 30-50% */}
              <ReferenceArea y1={30} y2={50} fill="#FF9500" fillOpacity={0.1} />
              {/* Green line and area */}
              <Area
                type="monotone"
                dataKey="stability"
                stroke="#00FF41"
                strokeWidth={2}
                fill="url(#stabilityGreen)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        {/* Chart 2: Logic Gap */}
        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-terminal-text uppercase">LOGIC GAP</h4>
            <span
              className="text-xs font-mono"
              style={{ color: logicGapColor }}
            >
              {currentLogicGap.toFixed(0)}%
            </span>
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1A1A1A" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => formatTimestamp(value, timeRange)}
                tick={{ fill: '#666666', fontSize: 10 }}
                axisLine={{ stroke: '#1A1A1A' }}
                tickLine={{ stroke: '#1A1A1A' }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#666666', fontSize: 10 }}
                axisLine={{ stroke: '#1A1A1A' }}
                tickLine={{ stroke: '#1A1A1A' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine
                y={40}
                stroke="#666666"
                strokeDasharray="3 3"
                label={{ value: 'Brittle', position: 'right', fill: '#666666', fontSize: 10 }}
              />
              <ReferenceLine
                y={60}
                stroke="#666666"
                strokeDasharray="3 3"
                label={{ value: 'Paradox', position: 'right', fill: '#666666', fontSize: 10 }}
              />
              <Line
                type="monotone"
                dataKey="logicGap"
                stroke={logicGapColor}
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        {/* Chart 3: Entropy Rate */}
        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-terminal-text uppercase">ENTROPY</h4>
            <span className="text-xs font-mono text-[#9932CC]">
              {currentEntropyRate.toFixed(1)}%/hr
            </span>
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1A1A1A" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => formatTimestamp(value, timeRange)}
                tick={{ fill: '#666666', fontSize: 10 }}
                axisLine={{ stroke: '#1A1A1A' }}
                tickLine={{ stroke: '#1A1A1A' }}
              />
              <YAxis
                domain={[-10, 0]}
                tick={{ fill: '#666666', fontSize: 10 }}
                axisLine={{ stroke: '#1A1A1A' }}
                tickLine={{ stroke: '#1A1A1A' }}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="entropyRate"
                stroke="#9932CC"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
