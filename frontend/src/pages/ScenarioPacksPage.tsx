/**
 * ScenarioPacksPage — Scenario Packs browser (Alpamayo Studio).
 *
 * Wired to GET /api/v1/scenario-pack-templates for real catalog data.
 * Shows template cards with family badge, checkpoint count, fork range,
 * and RUNNABLE vs CATALOG_ONLY status.
 *
 * PRODUCT DISTINCTION:
 *   - Theatre Templates = live market contracts (Create Theatre flow)
 *   - Scenario Packs = branching RL / telemetry environments (THIS PAGE)
 *   - Alpamayo = recommendation + scenario-construction intelligence
 *   - RLMF Exports = downstream data products
 *
 * DESIGN REF: output/design_reference/echelon_scenario_packs_v1.html
 */

import { useEffect, useState } from 'react';
import { Boxes, GitBranch, BarChart3, Play, Loader2 } from 'lucide-react';
import { EmptyState } from '../components/empty-states/EmptyState';
import {
  scenarioPackApi,
  type ScenarioPackTemplateSummary,
} from '../api/scenarioPacks';

const FAMILY_LABELS: Record<string, string> = {
  NAV_UNC: 'Navigation',
  SOC_NAV: 'Social',
  MAN_FORCE: 'Manual Force',
  MARL_C3: 'Multi-Agent',
  '3D_INERT': '3D Inertial',
  LONG_HZN: 'Long Horizon',
  PUZ_LOGIC: 'Puzzle',
  ADV_AIR: 'Adversarial',
  PREC_MAN: 'Precision',
};

export function ScenarioPacksPage() {
  const [templates, setTemplates] = useState<ScenarioPackTemplateSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [familyFilter, setFamilyFilter] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    scenarioPackApi
      .listTemplates({
        family: familyFilter ?? undefined,
        limit: 50,
      })
      .then((res) => {
        if (!cancelled) {
          setTemplates(res.templates);
          setTotal(res.total);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || 'Failed to load templates');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [familyFilter]);

  // Get unique families for filter tabs
  const families = Object.keys(FAMILY_LABELS);

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

      {/* Stats bar */}
      <div className="flex gap-4 p-3 bg-terminal-surface border border-terminal-border rounded-lg flex-wrap">
        {[
          { label: 'Templates', value: loading ? '...' : String(total) },
          {
            label: 'Runnable',
            value: loading
              ? '...'
              : String(templates.filter((t) => t.template_status === 'RUNNABLE').length),
          },
          {
            label: 'Catalog Only',
            value: loading
              ? '...'
              : String(templates.filter((t) => t.template_status === 'CATALOG_ONLY').length),
          },
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

      {/* Family filter tabs */}
      <div className="flex items-center gap-1 flex-wrap">
        <button
          onClick={() => setFamilyFilter(null)}
          className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
            familyFilter === null
              ? 'bg-terminal-surface text-terminal-text shadow-sm border border-terminal-border'
              : 'text-terminal-text-muted hover:text-terminal-text'
          }`}
        >
          All
        </button>
        {families.map((f) => (
          <button
            key={f}
            onClick={() => setFamilyFilter(f)}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              familyFilter === f
                ? 'bg-terminal-surface text-terminal-text shadow-sm border border-terminal-border'
                : 'text-terminal-text-muted hover:text-terminal-text'
            }`}
          >
            {FAMILY_LABELS[f] || f}
          </button>
        ))}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 text-terminal-text-muted animate-spin" />
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="p-4 bg-status-failure/10 border border-status-failure/30 rounded-lg text-xs text-status-failure">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && templates.length === 0 && (
        <EmptyState
          type="ZERO_STATE"
          icon={<Boxes className="w-7 h-7" />}
          title="No scenario packs yet"
          description="Scenario packs are branching environments for agent training and RLMF telemetry. Seed the template catalog to get started."
          actions={[]}
        />
      )}

      {/* Template grid */}
      {!loading && !error && templates.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {templates.map((t) => (
            <div
              key={t.id}
              className="bg-terminal-surface border border-terminal-border rounded-lg p-4 hover:border-terminal-text/20 transition-colors"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="text-sm font-semibold text-terminal-text">{t.name}</div>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                    t.template_status === 'RUNNABLE'
                      ? 'bg-status-success/15 text-status-success'
                      : 'bg-terminal-panel text-terminal-text-muted'
                  }`}
                >
                  {t.template_status}
                </span>
              </div>

              {/* Family badge */}
              <div className="text-[10px] font-mono text-terminal-text-muted mb-2">
                {FAMILY_LABELS[t.family] || t.family} ({t.family})
              </div>

              {/* Description */}
              {t.description && (
                <div className="text-[11px] text-terminal-text-secondary mb-3 line-clamp-2">
                  {t.description}
                </div>
              )}

              {/* Stats row */}
              <div className="flex items-center gap-3 text-[10px] text-terminal-text-muted">
                <span className="flex items-center gap-1">
                  <GitBranch className="w-3 h-3" />
                  {t.checkpoint_count} checkpoints
                </span>
                <span>
                  {t.fork_points_min}–{t.fork_points_max} forks
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
