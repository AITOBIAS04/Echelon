/**
 * CFPM / LMSR Impact & Cost Panel
 *
 * Replaces the traditional order book with a cost-function prediction market
 * (CFPM) panel powered by LMSR (Logarithmic Market Scoring Rule).
 * All values are demo/mock — no backend required.
 */

import { Activity, Zap, TrendingUp, ArrowRight } from 'lucide-react';
import { clsx } from 'clsx';

interface ImpactCostPanelProps {
  currentPrice: number;
}

// ── Demo LMSR parameters ────────────────────────────────────────────────
const LIQUIDITY_B = 142.5;
const NUM_OUTCOMES = 2;
const WORST_CASE_LOSS = LIQUIDITY_B * Math.log(NUM_OUTCOMES);

// LMSR cost function: C(q) = b * ln(sum(exp(q_i / b)))
// For binary market, cost to move probability from p1 to p2:
// cost = b * ln(exp(q_yes_new/b) + exp(q_no_new/b)) - b * ln(exp(q_yes_old/b) + exp(q_no_old/b))
function lmsrCost(pFrom: number, pTo: number, b: number): number {
  // Simplified binary LMSR cost approximation
  const qFrom = Math.log(pFrom / (1 - pFrom));
  const qTo = Math.log(pTo / (1 - pTo));
  return Math.abs(b * (qTo - qFrom)) * 0.42; // Scaled for demo realism
}

// Impact ladder entries
const IMPACT_LADDER = [
  { delta: 0.01, label: '+1%' },
  { delta: 0.05, label: '+5%' },
  { delta: 0.10, label: '+10%' },
  { delta: 0.25, label: '+25%' },
];

export function ImpactCostPanel({ currentPrice }: ImpactCostPanelProps) {
  // Current probability derived from price (in a PM, price ≈ probability)
  const currentProb = Math.min(Math.max(currentPrice / 100, 0.01), 0.99);
  const probPercent = (currentProb * 100).toFixed(1);

  return (
    <div className="terminal-panel rounded-2xl flex flex-col min-h-0 overflow-hidden">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="section-header">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-echelon-cyan" />
          <span className="section-header-title">CFPM MARKET ENGINE</span>
        </div>
        <span className="chip chip-info">LMSR</span>
      </div>

      {/* ── Body ───────────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4">

        {/* ── Instant Price ────────────────────────────────────── */}
        <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
          <div className="flex items-center justify-between mb-3">
            <span className="data-label">Instant Probability</span>
            <span className="chip chip-success text-[9px]">CFPM</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-mono font-bold tabular-nums text-echelon-cyan">
              {probPercent}%
            </span>
            <span className="text-sm font-mono tabular-nums text-terminal-text-muted">
              ≈ ${currentPrice.toFixed(2)}
            </span>
          </div>
          <div className="flex items-center gap-1.5 mt-2">
            <TrendingUp className="w-3 h-3 text-echelon-green" />
            <span className="text-[10px] text-echelon-green font-mono tabular-nums">+2.4% 24h</span>
          </div>
        </div>

        {/* ── Liquidity Parameters ─────────────────────────────── */}
        <div className="space-y-2">
          <span className="section-title-accented">Liquidity Parameters</span>

          <div className="grid grid-cols-2 gap-3">
            <div className="metric-block bg-terminal-card/50 rounded-lg p-3 border border-terminal-border/50">
              <span className="metric-label">Depth (b)</span>
              <span className="metric-value text-echelon-cyan">{LIQUIDITY_B.toFixed(1)}</span>
            </div>
            <div className="metric-block bg-terminal-card/50 rounded-lg p-3 border border-terminal-border/50">
              <span className="metric-label">Max Loss</span>
              <span className="metric-value text-echelon-amber">${WORST_CASE_LOSS.toFixed(2)}</span>
            </div>
          </div>

          <div className="bg-terminal-card/30 rounded-lg p-3 border border-terminal-border/30">
            <div className="flex items-center gap-2 mb-1">
              <span className="data-label">Worst-Case Loss Bound</span>
            </div>
            <div className="flex items-center gap-2">
              <code className="text-xs font-mono text-echelon-purple bg-echelon-purple/10 px-2 py-0.5 rounded border border-echelon-purple/20">
                b &middot; ln(n)
              </code>
              <span className="text-xs text-terminal-text-muted">=</span>
              <span className="text-xs font-mono tabular-nums text-terminal-text">
                {LIQUIDITY_B} &times; ln({NUM_OUTCOMES}) = ${WORST_CASE_LOSS.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* ── Cost Calculator ──────────────────────────────────── */}
        <div className="space-y-2">
          <span className="section-title-accented">Cost Calculator</span>

          <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
            <div className="flex items-center gap-2 text-sm text-terminal-text-secondary mb-3">
              <span className="text-terminal-text-muted">Move probability</span>
              <span className="font-mono tabular-nums text-echelon-cyan font-semibold">{probPercent}%</span>
              <ArrowRight className="w-3 h-3 text-terminal-text-muted" />
              <span className="font-mono tabular-nums text-echelon-green font-semibold">
                {(currentProb * 100 + 5).toFixed(1)}%
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <Zap className="w-4 h-4 text-echelon-amber" />
              <span className="text-xl font-mono font-bold tabular-nums text-terminal-text">
                ${lmsrCost(currentProb, Math.min(currentProb + 0.05, 0.99), LIQUIDITY_B).toFixed(2)}
              </span>
              <span className="text-xs text-terminal-text-muted">estimated cost</span>
            </div>
          </div>
        </div>

        {/* ── Impact Ladder ────────────────────────────────────── */}
        <div className="space-y-2">
          <span className="section-title-accented">Impact Ladder</span>

          <div className="space-y-1">
            {IMPACT_LADDER.map(({ delta, label }) => {
              const targetProb = Math.min(currentProb + delta, 0.99);
              const cost = lmsrCost(currentProb, targetProb, LIQUIDITY_B);
              const targetPct = (targetProb * 100).toFixed(1);
              // Relative cost bar width (max at 25% move)
              const maxCost = lmsrCost(currentProb, Math.min(currentProb + 0.25, 0.99), LIQUIDITY_B);
              const barWidth = Math.min((cost / maxCost) * 100, 100);

              return (
                <div
                  key={label}
                  className="relative flex items-center justify-between px-3 py-2 rounded-lg border border-terminal-border/30 bg-terminal-card/30 overflow-hidden group hover:border-terminal-border transition-colors"
                >
                  {/* Cost bar background */}
                  <div
                    className="absolute inset-y-0 left-0 bg-echelon-cyan/[0.06] transition-all duration-300"
                    style={{ width: `${barWidth}%` }}
                  />

                  <div className="relative flex items-center gap-3 z-10">
                    <span className={clsx(
                      'text-xs font-mono font-bold tabular-nums w-10',
                      delta <= 0.05 ? 'text-echelon-green' : delta <= 0.10 ? 'text-echelon-amber' : 'text-echelon-red'
                    )}>
                      {label}
                    </span>
                    <span className="text-[10px] text-terminal-text-muted">
                      → {targetPct}%
                    </span>
                  </div>

                  <span className="relative z-10 text-xs font-mono tabular-nums font-semibold text-terminal-text">
                    ${cost.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Market Info Footer ────────────────────────────────── */}
        <div className="border-t border-terminal-border/50 pt-3 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="data-label">Market Type</span>
            <span className="data-value text-echelon-cyan">LMSR Binary</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="data-label">Outcomes</span>
            <span className="data-value">{NUM_OUTCOMES}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="data-label">Subsidy Pool</span>
            <span className="data-value">${(LIQUIDITY_B * 2.5).toFixed(0)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="data-label">24h Volume</span>
            <span className="data-value text-echelon-green">$12,847</span>
          </div>
        </div>
      </div>
    </div>
  );
}
