import { useState } from 'react';
import { Clock, AlertTriangle, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';
import type { Market } from '../../types/marketplace';

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
 * - RLMF training data indicator
 */
export function MarketCard({ market, onClick, onBet }: MarketCardProps) {
  const [betAmount, setBetAmount] = useState<number>(10);
  const [selectedOutcome, setSelectedOutcome] = useState<'YES' | 'NO' | null>(null);
  const [isHovered, setIsHovered] = useState(false);

  const categoryStyles = getCategoryStyles(market.category);
  const stabilityColor = getStabilityColor(market.stability);
  const gapStyles = getGapStyles(market.gap);
  const stabilityPercent = Math.max(0, Math.min(100, market.stability));

  const handleBet = (outcome: 'YES' | 'NO') => {
    if (onBet) {
      onBet(market, outcome);
    }
    setSelectedOutcome(outcome);
  };

  const potentialPayout = selectedOutcome
    ? betAmount * (selectedOutcome === 'YES' ? market.yesPrice : market.noPrice)
    : 0;

  return (
    <div
      className={clsx(
        'bg-terminal-panel border border-terminal-border rounded-xl p-4 transition-all cursor-pointer',
        'hover:border-terminal-border/70 hover:bg-terminal-card',
        'active:scale-[0.99]'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
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
          <span className="text-[10px] text-terminal-muted uppercase tracking-wider">
            {market.stabilityStatus}
          </span>
          <div className="w-10 h-1.5 bg-terminal-bg rounded-full overflow-hidden">
            <div
              className={clsx(
                'h-full rounded-full transition-all duration-300',
                `bg-[${stabilityColor.color}]`
              )}
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
          className={clsx(
            'flex-1 flex flex-col justify-between p-3 rounded-lg border transition-all',
            'hover:border-status-success/50',
            selectedOutcome === 'YES'
              ? 'bg-status-success/10 border-status-success'
              : 'bg-terminal-bg border-terminal-border'
          )}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-terminal-muted uppercase">YES</span>
            <span className="text-[10px] font-mono text-terminal-secondary">
              {market.yesProb}%
            </span>
          </div>
          <div className="text-lg font-bold font-mono text-status-success">
            ${market.yesPrice.toFixed(2)}
          </div>
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            handleBet('NO');
          }}
          className={clsx(
            'flex-1 flex flex-col justify-between p-3 rounded-lg border transition-all',
            'hover:border-status-danger/50',
            selectedOutcome === 'NO'
              ? 'bg-status-danger/10 border-status-danger'
              : 'bg-terminal-bg border-terminal-border'
          )}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-terminal-muted uppercase">NO</span>
            <span className="text-[10px] font-mono text-terminal-secondary">
              {market.noProb}%
            </span>
          </div>
          <div className="text-lg font-bold font-mono text-status-danger">
            ${market.noPrice.toFixed(2)}
          </div>
        </button>
      </div>

      {/* Bet Amount Slider (shown when outcome selected) */}
      {selectedOutcome && (
        <div className="mb-4 p-3 bg-terminal-bg rounded-lg border border-terminal-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-terminal-muted uppercase">Bet Amount</span>
            <span className="text-sm font-mono text-terminal-text">${betAmount.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="1"
            max="100"
            value={betAmount}
            onChange={(e) => setBetAmount(Number(e.target.value))}
            onClick={(e) => e.stopPropagation()}
            className="w-full h-1.5 bg-terminal-panel rounded-full appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${betAmount}%, #363A40 ${betAmount}%, #363A40 100%)`,
            }}
          />
          <div className="flex justify-between mt-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setBetAmount(Math.max(1, betAmount - 10));
              }}
              className="text-[10px] text-terminal-muted hover:text-terminal-text"
            >
              -10
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setBetAmount(Math.min(100, betAmount + 10));
              }}
              className="text-[10px] text-terminal-muted hover:text-terminal-text"
            >
              +10
            </button>
          </div>
          <div className="mt-2 text-center">
            <span className="text-xs text-terminal-muted">
              Potential payout: <span className="text-status-success font-mono font-bold">${potentialPayout.toFixed(2)}</span>
            </span>
          </div>
        </div>
      )}

      {/* Footer Metrics */}
      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-terminal-border">
        <div className="flex flex-col">
          <span className="text-[10px] text-terminal-muted uppercase tracking-wider">Liquidity</span>
          <span className="text-xs font-mono font-medium text-terminal-secondary">
            {formatCurrency(market.liquidity)}
          </span>
        </div>

        <div className="flex flex-col">
          <span className="text-[10px] text-terminal-muted uppercase tracking-wider">Fork In</span>
          <span className="text-xs font-mono font-medium text-terminal-secondary flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatTimeRemaining(market.nextForkEtaSec)}
          </span>
        </div>

        <div className="flex flex-col">
          <span className="text-[10px] text-terminal-muted uppercase tracking-wider">Gap</span>
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
          isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'
        )}
      >
        <ChevronRight className="w-5 h-5 text-status-info" />
      </div>
    </div>
  );
}
