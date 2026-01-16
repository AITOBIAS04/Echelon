import { useNavigate } from 'react-router-dom';
import { RefreshCw, AlertTriangle, TrendingUp, Activity, ArrowRight } from 'lucide-react';
import { usePortfolioRisk } from '../../hooks/usePortfolioRisk';
import { ReplayDrawer } from '../replay/ReplayDrawer';
import { useState } from 'react';
import type { ReplayPointer } from '../../types/replay';

/**
 * PortfolioRiskPanel Component
 * 
 * Displays comprehensive portfolio risk analysis including risk indices,
 * exposure summary, top risks, and recommendations.
 */
export function PortfolioRiskPanel() {
  const navigate = useNavigate();
  const { summary, loading, error, refresh } = usePortfolioRisk();
  const [replayOpen, setReplayOpen] = useState(false);
  const [replayPointer, setReplayPointer] = useState<ReplayPointer | null>(null);

  const handleOpenTimeline = (timelineId: string) => {
    navigate(`/timeline/${timelineId}`);
  };

  const handleReplay = (timelineId: string) => {
    // Mock pointer - in production, would fetch actual latest fork ID
    const pointer: ReplayPointer = {
      timelineId,
      forkId: 'latest',
    };
    setReplayPointer(pointer);
    setReplayOpen(true);
  };

  const handleCloseReplay = () => {
    setReplayOpen(false);
    setReplayPointer(null);
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-terminal-muted animate-pulse">Loading portfolio risk...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <AlertTriangle className="w-12 h-12 text-red-500 mb-4 opacity-50" />
        <p className="text-lg font-semibold text-terminal-text mb-2">Error loading risk data</p>
        <p className="text-sm text-terminal-muted mb-4">{error}</p>
        <button
          onClick={refresh}
          className="px-4 py-2 bg-terminal-panel border border-terminal-border rounded hover:border-echelon-cyan transition text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-terminal-muted">No portfolio data available</div>
      </div>
    );
  }

  const formatCurrency = (value: number): string => {
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatTimestamp = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getRiskColor = (score: number): string => {
    if (score >= 70) return '#FF3B3B'; // red
    if (score >= 50) return '#FF9500'; // amber
    return '#00FF41'; // green
  };

  const getRiskLabel = (score: number): string => {
    if (score >= 70) return 'HIGH';
    if (score >= 50) return 'MODERATE';
    return 'LOW';
  };

  return (
    <div className="h-full flex flex-col gap-4 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-terminal-text uppercase tracking-wide">
            Portfolio Risk
          </h2>
          <p className="text-xs text-terminal-muted mt-1">
            Updated: {formatTimestamp(summary.asOf)}
          </p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-2 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition"
        >
          <RefreshCw className="w-3 h-3" />
          Refresh
        </button>
      </div>

      {/* KPI Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Risk Index */}
        <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-terminal-muted uppercase tracking-wide">Risk Index</span>
            <Activity className="w-4 h-4" style={{ color: getRiskColor(summary.riskIndex) }} />
          </div>
          <div className="flex items-baseline gap-2">
            <span
              className="text-3xl font-mono font-bold"
              style={{ color: getRiskColor(summary.riskIndex) }}
            >
              {summary.riskIndex.toFixed(1)}
            </span>
            <span className="text-xs text-terminal-muted">/ 100</span>
          </div>
          <div className="mt-2">
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded"
              style={{
                backgroundColor: `${getRiskColor(summary.riskIndex)}20`,
                color: getRiskColor(summary.riskIndex),
              }}
            >
              {getRiskLabel(summary.riskIndex)}
            </span>
          </div>
        </div>

        {/* Fragility Index */}
        <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-terminal-muted uppercase tracking-wide">Fragility Index</span>
            <TrendingUp className="w-4 h-4 text-amber-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span
              className="text-3xl font-mono font-bold"
              style={{ color: getRiskColor(summary.fragilityIndex) }}
            >
              {summary.fragilityIndex.toFixed(1)}
            </span>
            <span className="text-xs text-terminal-muted">/ 100</span>
          </div>
          <div className="mt-2">
            <span className="text-xs text-terminal-muted">
              Stability + Entropy + Sabotage
            </span>
          </div>
        </div>

        {/* Belief Divergence Index */}
        <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-terminal-muted uppercase tracking-wide">Belief Divergence</span>
            <AlertTriangle className="w-4 h-4 text-purple-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span
              className="text-3xl font-mono font-bold"
              style={{ color: getRiskColor(summary.beliefDivergenceIndex) }}
            >
              {summary.beliefDivergenceIndex.toFixed(1)}
            </span>
            <span className="text-xs text-terminal-muted">/ 100</span>
          </div>
          <div className="mt-2">
            <span className="text-xs text-terminal-muted">
              Logic Gap + Paradox Proximity
            </span>
          </div>
        </div>
      </div>

      {/* Exposure Summary */}
      <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-3">
          Exposure Summary
        </h3>
        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-terminal-muted">Total Notional</span>
              <span className="text-sm font-mono font-semibold text-terminal-text">
                {formatCurrency(summary.totalNotional)}
              </span>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-terminal-muted">Net YES Notional</span>
              <span
                className={`text-sm font-mono font-semibold ${
                  summary.netYesNotional >= 0 ? 'text-green-500' : 'text-red-500'
                }`}
              >
                {formatCurrency(summary.netYesNotional)}
              </span>
            </div>
            <div className="w-full h-2 bg-[#1A1A1A] rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500/50 transition-all"
                style={{
                  width: `${Math.min(100, Math.abs(summary.netYesNotional) / summary.totalNotional * 100)}%`,
                }}
              />
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-terminal-muted">Net NO Notional</span>
              <span
                className={`text-sm font-mono font-semibold ${
                  summary.netNoNotional >= 0 ? 'text-red-500' : 'text-green-500'
                }`}
              >
                {formatCurrency(summary.netNoNotional)}
              </span>
            </div>
            <div className="w-full h-2 bg-[#1A1A1A] rounded-full overflow-hidden">
              <div
                className="h-full bg-red-500/50 transition-all"
                style={{
                  width: `${Math.min(100, Math.abs(summary.netNoNotional) / summary.totalNotional * 100)}%`,
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Top Risks Table */}
      <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-3">
          Top Risks
        </h3>
        {summary.topRisks.length === 0 ? (
          <div className="text-center py-8 text-terminal-muted text-sm">
            No risks identified
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#1A1A1A]">
                  <th className="text-left p-2 text-terminal-muted uppercase text-xs">Timeline</th>
                  <th className="text-left p-2 text-terminal-muted uppercase text-xs">Risk Score</th>
                  <th className="text-left p-2 text-terminal-muted uppercase text-xs">Drivers</th>
                  <th className="text-left p-2 text-terminal-muted uppercase text-xs">Burn at Collapse</th>
                  <th className="text-right p-2 text-terminal-muted uppercase text-xs">Actions</th>
                </tr>
              </thead>
              <tbody>
                {summary.topRisks.map((risk) => (
                  <tr
                    key={risk.timelineId}
                    className="border-b border-[#1A1A1A]/50 hover:bg-[#1A1A1A]/30 transition"
                  >
                    <td className="p-2">
                      <span className="font-mono text-terminal-text text-xs">
                        {risk.timelineId}
                      </span>
                    </td>
                    <td className="p-2">
                      <span
                        className="font-mono font-semibold"
                        style={{ color: getRiskColor(risk.riskScore) }}
                      >
                        {risk.riskScore.toFixed(1)}
                      </span>
                    </td>
                    <td className="p-2">
                      <span className="text-terminal-muted text-xs">
                        {risk.drivers.join(', ')}
                      </span>
                    </td>
                    <td className="p-2">
                      <span className="font-mono text-red-400 text-xs">
                        {formatCurrency(risk.burnAtCollapse)}
                      </span>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenTimeline(risk.timelineId)}
                          className="px-2 py-1 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition"
                        >
                          OPEN
                        </button>
                        <button
                          onClick={() => handleReplay(risk.timelineId)}
                          className="px-2 py-1 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition"
                        >
                          REPLAY
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recommendations */}
      {summary.recommendations.length > 0 && (
        <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-3">
            Recommendations
          </h3>
          <ul className="space-y-2">
            {summary.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-terminal-text">
                <ArrowRight className="w-4 h-4 text-echelon-cyan mt-0.5 flex-shrink-0" />
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Replay Drawer */}
      <ReplayDrawer
        open={replayOpen}
        onClose={handleCloseReplay}
        pointer={replayPointer}
      />
    </div>
  );
}
