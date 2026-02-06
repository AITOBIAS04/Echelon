import { useState } from 'react';
import { Clock, AlertTriangle, ChevronRight, X } from 'lucide-react';
import { clsx } from 'clsx';
import type { Market } from '../../types/marketplace';
import { useDemoEnabled, useDemoOutcome } from '../../demo/hooks';
import { DemoBetModal } from '../../demo/DemoBetModal';
import { demoActions } from '../../demo/actions';

interface MarketCardProps {
  market: Market;
  onClick?: (market: Market) => void;
  onBet?: (market: Market, outcome: 'YES' | 'NO') => void;
}

/**
 * Get category badge styles
 */
function getCategoryStyles(category: string): { bg: string; text: string; border: string } {
  const styles: Record<string, { bg: string; text: string; border: string }> = {
    robotics: {
      bg: 'rgba(96, 165, 250, 0.1)',
      text: '#60A5FA',
      border: 'rgba(96, 165, 250, 0.2)',
    },
    logistics: {
      bg: 'rgba(74, 222, 128, 0.1)',
      text: '#4ADE80',
      border: 'rgba(74, 222, 128, 0.2)',
    },
    defi: {
      bg: 'rgba(139, 92, 246, 0.1)',
      text: '#8B5CF6',
      border: 'rgba(139, 92, 246, 0.2)',
    },
    physics: {
      bg: 'rgba(250, 204, 21, 0.1)',
      text: '#FACC15',
      border: 'rgba(250, 204, 21, 0.2)',
    },
    soceng: {
      bg: 'rgba(59, 130, 246, 0.1)',
      text: '#3B82F6',
      border: 'rgba(59, 130, 246, 0.2)',
    },
  };

  return styles[category] || styles.robotics;
}

/**
 * Get stability gauge color
 */
function getStabilityColor(stability: number): { color: string; class: string } {
  if (stability >= 70) {
    return { color: '#4ADE80', class: 'stable' };
  } else if (stability >= 50) {
    return { color: '#FACC15', class: 'warning' };
  }
  return { color: '#FB7185', class: 'critical' };
}

/**
 * Get gap warning styles
 */
function getGapStyles(gap: number): { color: string; class: string } {
  if (gap >= 40) {
    return { color: '#FB7185', class: 'danger' };
  } else if (gap >= 25) {
    return { color: '#FACC15', class: 'warning' };
  }
  return { color: '#64748B', class: '' };
}

/**
 * Format time remaining
 */
function formatTimeRemaining(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h ${minutes % 60}m`;
  }
  const days = Math.floor(hours / 24);
  return `${days}d ${hours % 24}h`;
}

/**
 * Format currency
 */
function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toFixed(0)}`;
}

/**
 * MarketCard Component
 *
 * Displays a single market card with:
 * - Category badge and stability gauge
 * - Market title
 * - YES/NO outcome betting UI
 * - Metrics: liquidity, fork time, logic gap
 * - 3D flip to bet form on outcome selection
 */
export function MarketCard({ market, onClick, onBet }: MarketCardProps) {
  const demoEnabled = useDemoEnabled();
  const marketId = market.id;

  // Demo mode hooks for live ticks
  const yesSnap = useDemoOutcome(marketId, 'YES', {
    price: market.yesPrice,
    stability: market.stability,
    volume: market.volume24h,
  });

  const noSnap = useDemoOutcome(marketId, 'NO', {
    price: market.noPrice,
    stability: market.stability,
    volume: market.volume24h,
  });

  const [betAmount, setBetAmount] = useState<number>(10);
  const [selectedOutcome, setSelectedOutcome] = useState<'YES' | 'NO' | null>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [demoBetOpen, setDemoBetOpen] = useState(false);
  const [demoBetSide, setDemoBetSide] = useState<'YES' | 'NO'>('YES');

  // Use demo prices when enabled, otherwise use market data
  const displayYesPrice = demoEnabled ? yesSnap.price : market.yesPrice;
  const displayNoPrice = demoEnabled ? noSnap.price : market.noPrice;
  const displayStability = demoEnabled ? yesSnap.stability : market.stability;
  const displayYesProb = displayYesPrice * 100;
  const displayNoProb = displayNoPrice * 100;

  const categoryStyles = getCategoryStyles(market.category);
  const stabilityColor = getStabilityColor(displayStability);
  const gapStyles = getGapStyles(market.gap);
  const stabilityPercent = Math.max(0, Math.min(100, displayStability));

  const isFlipped = selectedOutcome !== null;

  const handleBet = (outcome: 'YES' | 'NO') => {
    if (demoEnabled) {
      setDemoBetSide(outcome);
      setDemoBetOpen(true);
      return;
    }

    if (onBet) {
      onBet(market, outcome);
    }
    setSelectedOutcome(outcome);
    setBetAmount(10);
  };

  const handleCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedOutcome(null);
  };

  const selectedPrice = selectedOutcome === 'YES' ? displayYesPrice : displayNoPrice;
  const potentialPayout = selectedOutcome ? betAmount / selectedPrice : 0;

  return (
    <div
      className="card-flip-container"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={clsx('card-flip-inner', isFlipped && 'flipped')}>

        {/* ══════════════ FRONT FACE ══════════════ */}
        <div
          className={clsx(
            'card-flip-front bg-terminal-panel border border-terminal-border rounded-xl p-4 transition-colors cursor-pointer',
            'hover:border-terminal-border-light hover:bg-terminal-card',
            'active:scale-[0.99]'
          )}
          onClick={() => onClick?.(market)}
        >
          {/* Header: Category + Stability */}
          <div className="flex items-center justify-between mb-3">
            <span
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider"
              style={{
                backgroundColor: categoryStyles.bg,
                color: categoryStyles.text,
                border: `1px solid ${categoryStyles.border}`,
              }}
            >
              {market.categoryIcon} {market.categoryName}
            </span>

            <div className="flex items-center gap-2">
              <span className="text-[10px] text-terminal-text-muted uppercase tracking-wider">
                {demoEnabled
                  ? displayStability >= 70 ? 'Stable' : displayStability >= 50 ? 'Degraded' : 'Critical'
                  : market.stabilityStatus}
              </span>
              <div className="w-10 h-1.5 bg-terminal-bg rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${stabilityPercent}%`,
                    backgroundColor: stabilityColor.color,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Title */}
          <h3 className="text-sm font-semibold text-terminal-text mb-4 line-clamp-2 leading-snug">
            {market.title}
          </h3>

          {/* Betting UI - Outcomes */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleBet('YES');
              }}
              className="flex-1 flex flex-col justify-between p-3 rounded-lg border transition-all hover:border-status-success/50 bg-terminal-bg border-terminal-border"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-terminal-text-muted uppercase">YES</span>
                <span className="text-[10px] font-mono text-terminal-secondary">
                  {displayYesProb.toFixed(0)}%
                </span>
              </div>
              <div className="text-lg font-bold font-mono text-status-success">
                ${displayYesPrice.toFixed(2)}
              </div>
            </button>

            <button
              onClick={(e) => {
                e.stopPropagation();
                handleBet('NO');
              }}
              className="flex-1 flex flex-col justify-between p-3 rounded-lg border transition-all hover:border-status-danger/50 bg-terminal-bg border-terminal-border"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-terminal-text-muted uppercase">NO</span>
                <span className="text-[10px] font-mono text-terminal-secondary">
                  {displayNoProb.toFixed(0)}%
                </span>
              </div>
              <div className="text-lg font-bold font-mono text-status-danger">
                ${displayNoPrice.toFixed(2)}
              </div>
            </button>
          </div>

          {/* Footer Metrics */}
          <div className="grid grid-cols-3 gap-2 pt-3 border-t border-terminal-border">
            <div className="flex flex-col">
              <span className="text-[10px] text-terminal-text-muted uppercase tracking-wider">Liquidity</span>
              <span className="text-xs font-mono font-medium text-terminal-secondary">
                {formatCurrency(market.liquidity)}
              </span>
            </div>

            <div className="flex flex-col">
              <span className="text-[10px] text-terminal-text-muted uppercase tracking-wider">Fork In</span>
              <span className="text-xs font-mono font-medium text-terminal-secondary flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatTimeRemaining(market.nextForkEtaSec)}
              </span>
            </div>

            <div className="flex flex-col">
              <span className="text-[10px] text-terminal-text-muted uppercase tracking-wider">Gap</span>
              <span
                className={clsx(
                  'text-xs font-mono font-medium flex items-center gap-1',
                  gapStyles.class === 'danger' && 'text-status-danger',
                  gapStyles.class === 'warning' && 'text-status-warning',
                  !gapStyles.class && 'text-terminal-secondary'
                )}
              >
                <AlertTriangle className="w-3 h-3" />
                {market.gap.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Hover Arrow */}
          <div
            className={clsx(
              'absolute top-4 right-4 transition-all duration-200',
              isHovered && !isFlipped ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'
            )}
          >
            <ChevronRight className="w-5 h-5 text-status-info" />
          </div>
        </div>

        {/* ══════════════ BACK FACE (Bet Form) ══════════════ */}
        <div
          className="card-flip-back bg-terminal-panel border border-terminal-border rounded-xl p-4 flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Back header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span
                className={clsx(
                  'px-3 py-1 rounded-lg text-xs font-bold uppercase border',
                  selectedOutcome === 'YES'
                    ? 'bg-status-success/15 border-status-success/40 text-status-success'
                    : 'bg-status-danger/15 border-status-danger/40 text-status-danger'
                )}
              >
                {selectedOutcome}
              </span>
              <span className="text-xs text-terminal-text-muted">on</span>
            </div>
            <button
              onClick={handleCancel}
              className="p-1.5 rounded-lg hover:bg-terminal-card text-terminal-text-muted hover:text-terminal-text transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Market title */}
          <h3 className="text-sm font-semibold text-terminal-text mb-4 line-clamp-2 leading-snug">
            {market.title}
          </h3>

          {/* Bet amount */}
          <div className="flex-1 flex flex-col justify-center">
            <div className="p-3 bg-terminal-bg rounded-lg border border-terminal-border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] text-terminal-text-muted uppercase tracking-wider">Bet Amount</span>
                <span className="text-sm font-mono font-bold text-terminal-text">${betAmount.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="1"
                max="100"
                value={betAmount}
                onChange={(e) => setBetAmount(Number(e.target.value))}
                onClick={(e) => e.stopPropagation()}
                className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, ${selectedOutcome === 'YES' ? '#4ADE80' : '#FB7185'} 0%, ${selectedOutcome === 'YES' ? '#4ADE80' : '#FB7185'} ${betAmount}%, rgba(255,255,255,0.1) ${betAmount}%, rgba(255,255,255,0.1) 100%)`,
                }}
              />
              <div className="flex justify-between mt-1.5">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setBetAmount(Math.max(1, betAmount - 10));
                  }}
                  className="text-[10px] text-terminal-text-muted hover:text-terminal-text transition-colors"
                >
                  −10
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setBetAmount(Math.min(100, betAmount + 10));
                  }}
                  className="text-[10px] text-terminal-text-muted hover:text-terminal-text transition-colors"
                >
                  +10
                </button>
              </div>
            </div>
          </div>

          {/* Payout + actions */}
          <div className="mt-3 pt-3 border-t border-terminal-border">
            <div className="text-center mb-3">
              <span className="text-xs text-terminal-text-muted">Potential payout: </span>
              <span className="text-sm font-mono font-bold text-echelon-green">
                ${potentialPayout.toFixed(2)}
              </span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleCancel}
                className="flex-1 py-2 rounded-lg border border-terminal-border text-xs font-semibold text-terminal-text-secondary hover:bg-terminal-card transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  // In a real app this would submit the bet
                  setSelectedOutcome(null);
                }}
                className={clsx(
                  'flex-1 py-2 rounded-lg border text-xs font-bold transition-colors',
                  selectedOutcome === 'YES'
                    ? 'bg-status-success/15 border-status-success/40 text-status-success hover:bg-status-success/25'
                    : 'bg-status-danger/15 border-status-danger/40 text-status-danger hover:bg-status-danger/25'
                )}
              >
                Confirm {selectedOutcome}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Demo Bet Modal */}
      {demoEnabled && (
        <DemoBetModal
          open={demoBetOpen}
          title={market.title}
          side={demoBetSide}
          onClose={() => setDemoBetOpen(false)}
          onConfirm={(stake) => {
            demoActions.placeBet({
              marketId: market.id,
              marketTitle: market.title,
              outcomeId: demoBetSide,
              stake,
            });
            setDemoBetOpen(false);
          }}
        />
      )}
    </div>
  );
}
