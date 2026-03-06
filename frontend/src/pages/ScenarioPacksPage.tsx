/**
 * ScenarioPacksPage — Scenario Packs browser (Alpamayo Studio).
 *
 * Branching scenario environments for RLMF and agent learning.
 * Separate product surface from Theatre Templates / Create Theatre.
 *
 * PRODUCT DISTINCTION:
 *   - Theatre Templates = live market contracts (Create Theatre flow)
 *   - Scenario Packs = branching RL / telemetry environments (THIS PAGE)
 *   - Alpamayo = recommendation + scenario-construction intelligence
 *   - RLMF Exports = downstream data products
 *
 * VOCABULARY: Scenario Pack, Checkpoint, Branch, Outcome Path, Replay,
 *   Telemetry, Derived Theatre, Training Use.
 * NEVER: Theatre Template, Inquiry Class, Resolution Pattern.
 *
 * No backend endpoint exists yet. This page shows the catalog structure
 * with empty state. Feature-flagged for Cycle 017+.
 *
 * DESIGN REF: output/design_reference/echelon_scenario_packs_v1.html
 */

import { Boxes, GitBranch, BarChart3, Play } from 'lucide-react';
import { EmptyState } from '../components/empty-states/EmptyState';

export function ScenarioPacksPage() {
  // No backend — show the page chrome with empty catalog

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-5">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs text-terminal-text-muted mb-0.5">
            Alpamayo Studio
          </div>
          <h1 className="text-lg font-bold text-terminal-text">Scenario Packs</h1>
          <p className="text-xs text-terminal-text-secondary mt-1">
            Branching environments for RLMF telemetry and agent learning.
          </p>
        </div>
      </div>

      {/* Stats bar (skeleton) */}
      <div className="flex gap-4 p-3 bg-terminal-surface border border-terminal-border rounded-lg flex-wrap">
        {[
          { label: 'Total Packs', value: '—' },
          { label: 'Active Runs', value: '—' },
          { label: 'Total Branches', value: '—' },
          { label: 'Checkpoints', value: '—' },
        ].map((stat) => (
          <div
            key={stat.label}
            className="flex items-center gap-2 pr-4 border-r border-terminal-border/50 last:border-r-0 last:pr-0"
          >
            <span className="font-mono text-base font-bold text-terminal-text-muted">
              {stat.value}
            </span>
            <span className="text-[11px] text-terminal-text-muted leading-tight">
              {stat.label}
            </span>
          </div>
        ))}
      </div>

      {/* Filter bar (disabled skeleton) */}
      <div className="flex items-center justify-between">
        <div className="flex gap-0.5 bg-terminal-panel rounded-lg p-0.5 border border-terminal-border">
          {['All', 'Ready', 'Running', 'Draft'].map((tab, i) => (
            <span
              key={tab}
              className={`px-3 py-1 rounded-md text-xs font-medium ${
                i === 0
                  ? 'bg-terminal-surface text-terminal-text shadow-sm'
                  : 'text-terminal-text-muted'
              }`}
            >
              {tab}
            </span>
          ))}
        </div>
      </div>

      {/* Empty catalog */}
      <EmptyState
        type="ZERO_STATE"
        icon={<Boxes className="w-7 h-7" />}
        title="No scenario packs yet"
        description="Scenario packs are branching environments for agent training and RLMF telemetry. Each pack contains checkpoints, outcome branches, and replay data that agents use to learn from simulated market conditions."
        actions={[
          {
            label: 'Browse Starter Packs',
            onClick: () => {
              // Wire to scenario packs catalog when backend exists
            },
            variant: 'primary',
          },
        ]}
      />

      {/* Concept cards — what scenario packs contain */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2">
        <div className="bg-terminal-surface border border-terminal-border rounded-lg p-4">
          <GitBranch className="w-5 h-5 text-status-paradox mb-2" />
          <div className="text-xs font-semibold text-terminal-text mb-1">Branching Outcomes</div>
          <div className="text-[11px] text-terminal-text-muted leading-relaxed">
            Each pack defines forking outcome paths. Agents explore branches to learn how
            different market conditions resolve.
          </div>
        </div>
        <div className="bg-terminal-surface border border-terminal-border rounded-lg p-4">
          <BarChart3 className="w-5 h-5 text-status-info mb-2" />
          <div className="text-xs font-semibold text-terminal-text mb-1">RLMF Telemetry</div>
          <div className="text-[11px] text-terminal-text-muted leading-relaxed">
            Training data from scenario runs feeds into RLMF exports. Replay data captures
            agent decisions at each checkpoint.
          </div>
        </div>
        <div className="bg-terminal-surface border border-terminal-border rounded-lg p-4">
          <Play className="w-5 h-5 text-status-success mb-2" />
          <div className="text-xs font-semibold text-terminal-text mb-1">Derived Theatres</div>
          <div className="text-[11px] text-terminal-text-muted leading-relaxed">
            High-performing scenarios can be promoted to live theatre templates for
            real market deployment.
          </div>
        </div>
      </div>
    </div>
  );
}
