/**
 * Scenario Pack Detail Page
 *
 * Aligned to: echelon_scenario_pack_detail_v2.html
 *
 * Two-column layout: content left, sticky launch panel + metadata right.
 * Launch flow composes create + commit + run into a single user action.
 * RUNNABLE vs CATALOG_ONLY distinction preserved throughout.
 *
 * Run modes: TRAINING | EVALUATION | CALIBRATION | REPLAY
 * REPLAY = exact recorded-path replay (NOT "deterministic re-execution")
 *
 * Derived theatres surfaced at pack level via useDerivedTheatres(packId).
 * Branch probabilities remain template-level only in this pass.
 */

import { useState, useEffect, useMemo, useRef } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Loader2,
  Play,
  BarChart2,
  BookOpen,
  Download,
  Zap,
  GitBranch,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import {
  useTemplateDetail,
  useCreatePack,
  useCommitPack,
  useStartRun,
  usePackDetail,
  useBranchProbabilities,
  useDerivedTheatres,
} from '../hooks/useScenarioPacks';
import { ScenarioRunDetail } from '../components/scenario/ScenarioRunDetail';
import { BranchMap } from '../components/scenario/BranchMap';
import type { DerivedTheatreResponse } from '../types/scenarioPack';

type RunMode = 'TRAINING' | 'EVALUATION' | 'CALIBRATION' | 'REPLAY';

const RUN_MODES: { id: RunMode; label: string; description: string }[] = [
  { id: 'TRAINING', label: 'Training', description: 'Random seed per run' },
  { id: 'EVALUATION', label: 'Evaluation', description: 'Controlled stochasticity' },
  { id: 'CALIBRATION', label: 'Calibration', description: 'Canonical seed set' },
  { id: 'REPLAY', label: 'Replay', description: 'Exact recorded-path replay' },
];

const AGENT_ASSIGNMENTS = [
  { id: 'auto_assign', label: 'Auto-assign from fleet' },
  { id: 'courier-class', label: 'Courier-class agents' },
  { id: 'analyst-class', label: 'Analyst-class agents' },
  { id: 'manual', label: 'Manual selection' },
];

const SIMULATION_SCALES = [
  { id: 'single_1x', label: 'Single run (1x)' },
  { id: 'small_batch_10x', label: 'Small batch (10x)' },
  { id: 'full_sweep_100x', label: 'Full sweep (100x)' },
];

const OBJECTIVE_PROFILES = [
  { id: 'pack_default', label: 'Default (pack-defined)' },
  { id: 'maximize_delivery_rate', label: 'Maximise delivery rate' },
  { id: 'minimize_detection', label: 'Minimise detection' },
  { id: 'balanced_risk_reward', label: 'Balanced risk/reward' },
];

/** Family to human label mapping */
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

/** Derived theatre state badge */
function theatreStateClasses(state: string): string {
  switch (state) {
    case 'RUNNING':
      return 'bg-status-warning/15 text-status-warning';
    case 'SETTLED':
      return 'bg-status-success/15 text-status-success';
    default:
      return 'bg-terminal-panel text-terminal-text-muted';
  }
}

export function ScenarioPackDetailPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const { data: template, isLoading: templateLoading } = useTemplateDetail(templateId ?? null);
  const launchPanelRef = useRef<HTMLDivElement>(null);

  const [packId, setPackId] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [packCommitted, setPackCommitted] = useState(false);
  const [runMode, setRunMode] = useState<RunMode>('TRAINING');
  const [agentAssignment, setAgentAssignment] = useState('auto_assign');
  const [simulationScale, setSimulationScale] = useState('single_1x');
  const [objectiveProfile, setObjectiveProfile] = useState('pack_default');
  const [launchStep, setLaunchStep] = useState<'idle' | 'creating' | 'committing' | 'starting' | 'done' | 'error'>(
    'idle',
  );
  const [launchError, setLaunchError] = useState<string | null>(null);

  // Consume ?launch=true from catalog page shortcut
  useEffect(() => {
    if (searchParams.get('launch') === 'true' && launchPanelRef.current) {
      launchPanelRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams, templateLoading]);

  const createPack = useCreatePack();
  const commitPack = useCommitPack();
  const startRun = useStartRun();
  usePackDetail(packId);
  const { data: branchProbs } = useBranchProbabilities(templateId ?? null);
  const { data: derivedTheatresData } = useDerivedTheatres(packId);
  const derivedTheatres: DerivedTheatreResponse[] = derivedTheatresData ?? [];

  // Determine which checkpoints can spawn theatres
  const canSpawnTheatreCount = useMemo(
    () => template?.checkpoints?.filter((cp) => cp.can_spawn_theatre).length ?? 0,
    [template],
  );

  if (templateLoading) {
    return (
      <div className="max-w-5xl mx-auto p-6 flex items-center justify-center h-64">
        <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
      </div>
    );
  }

  if (!template) {
    return (
      <div className="max-w-5xl mx-auto p-6">
        <div className="text-terminal-text-muted text-sm">Template not found.</div>
      </div>
    );
  }

  const isRunnable = template.template_status === 'RUNNABLE';

  /** Composed launch: create -> commit -> run. Idempotent — resumes from where it failed. */
  const handleLaunch = async () => {
    if (!isRunnable) return;
    setLaunchError(null);

    try {
      // Step 1: Create pack (skip if already created from a previous attempt)
      let currentPackId = packId;
      if (!currentPackId) {
        setLaunchStep('creating');
        const newPack = await createPack.mutateAsync({
          template_id: template.id,
          run_mode: runMode,
          agent_assignment: agentAssignment,
          simulation_scale: simulationScale,
          objective_profile: objectiveProfile,
        });
        currentPackId = newPack.id;
        setPackId(currentPackId);
      }

      // Step 2: Commit (skip if already committed from a previous attempt)
      if (!packCommitted) {
        setLaunchStep('committing');
        await commitPack.mutateAsync(currentPackId);
        setPackCommitted(true);
      }

      // Step 3: Start run (skip if already started)
      if (!runId) {
        setLaunchStep('starting');
        const run = await startRun.mutateAsync(currentPackId);
        setRunId(run.id);
      }

      setLaunchStep('done');
    } catch (err) {
      setLaunchStep('error');
      setLaunchError(err instanceof Error ? err.message : 'Launch failed');
    }
  };

  const isLaunching = launchStep !== 'idle' && launchStep !== 'done' && launchStep !== 'error';

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Back link */}
      <Link
        to="/scenario-packs"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-terminal-text-secondary hover:text-terminal-text transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Scenario Packs
      </Link>

      {/* Detail header */}
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-terminal-text leading-8 mb-2">
            {template.name}
          </h1>
          <p className="text-[15px] text-terminal-text-secondary leading-6 mb-3 max-w-[640px]">
            {template.description}
          </p>
          <div className="flex gap-2 flex-wrap">
            <span className="text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded bg-purple-500/10 text-purple-500">
              {FAMILY_LABELS[template.family] ?? template.family}
            </span>
            <span
              className={`flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded ${
                isRunnable
                  ? 'bg-status-success/15 text-status-success'
                  : 'bg-terminal-panel text-terminal-text-muted'
              }`}
            >
              <span
                className={`w-[5px] h-[5px] rounded-full ${
                  isRunnable ? 'bg-status-success' : 'bg-terminal-text-muted/40'
                }`}
              />
              {template.template_status}
            </span>
          </div>
        </div>
        <div className="flex gap-3 shrink-0">
          <button className="flex items-center gap-1.5 h-9 px-4 rounded-lg text-[13px] font-semibold text-terminal-text-secondary border border-terminal-border bg-terminal-surface hover:bg-terminal-panel transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
          {isRunnable && (
            <button
              onClick={handleLaunch}
              disabled={isLaunching || launchStep === 'done'}
              className="flex items-center gap-1.5 h-9 px-4 rounded-lg text-[13px] font-semibold text-white bg-purple-500 hover:bg-purple-400 transition-colors disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              Launch Run
            </button>
          )}
        </div>
      </div>

      {/* Use tags */}
      <div className="flex flex-wrap gap-2">
        {RUN_MODES.map((mode) => (
          <span
            key={mode.id}
            className={`text-[11px] font-semibold px-2.5 py-1 rounded-md border transition-colors ${
              runMode === mode.id
                ? 'border-purple-300/40 bg-purple-500/10 text-purple-500'
                : 'border-terminal-border text-terminal-text-secondary bg-terminal-surface'
            }`}
          >
            {mode.label}
          </span>
        ))}
      </div>

      {/* CATALOG_ONLY notice */}
      {!isRunnable && (
        <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border flex items-start gap-3 opacity-90">
          <BookOpen className="w-4 h-4 text-terminal-text-muted mt-0.5 shrink-0" />
          <div>
            <div className="text-xs font-semibold text-terminal-text">Catalog-Only Template</div>
            <p className="text-xs text-terminal-text-muted mt-1">
              This template is available for reference and study but cannot be instantiated as a
              runnable scenario pack. Inspect checkpoints and branch probabilities below.
            </p>
          </div>
        </div>
      )}

      {/* Two-column grid: content left, launch panel + metadata right */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 items-start">
        {/* Left column */}
        <div className="space-y-5">
          {/* Branch Map */}
          <div
            id="branch-map"
            className="bg-terminal-surface border border-terminal-border rounded-lg overflow-hidden"
          >
            <div className="px-5 py-4 border-b border-terminal-border/50 flex items-center justify-between">
              <span className="text-[13px] font-semibold uppercase tracking-wide text-terminal-text-muted">
                Branch Map
              </span>
            </div>
            <div className="p-6 min-h-[200px]">
              {template.checkpoints?.length > 0 ? (
                <BranchMap
                  nodes={template.checkpoints.map((cp) => ({
                    checkpoint_id: cp.id,
                    sequence_num: cp.sequence_num,
                    trigger: cp.trigger,
                    market_question: cp.market_question,
                    selected_branch: null,
                    outcome_type: null,
                    reward: null,
                    spawned_theatre_id: null,
                  }))}
                />
              ) : (
                <div className="py-6 text-center text-[13px] text-terminal-text-muted">
                  No checkpoint data available for this template.
                </div>
              )}
            </div>
            {/* Legend */}
            <div className="flex gap-4 px-5 py-3 border-t border-terminal-border/50">
              {[
                { label: 'Start', color: 'bg-purple-500' },
                { label: 'Checkpoint', color: 'bg-orange-500' },
                { label: 'Success', color: 'bg-status-success' },
                { label: 'Failure', color: 'bg-status-failure' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-1.5 text-[11px] font-medium text-terminal-text-secondary">
                  <div className={`w-2 h-2 rounded-full ${item.color}`} />
                  {item.label}
                </div>
              ))}
            </div>
          </div>

          {/* Expected Outputs — only honestly inferable outputs */}
          <div className="bg-terminal-surface border border-terminal-border rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-terminal-border/50">
              <span className="text-[13px] font-semibold uppercase tracking-wide text-terminal-text-muted">
                Expected Outputs
              </span>
            </div>
            <div className="p-5">
              <div className="grid grid-cols-2 gap-3">
                {/* Checkpoints — always known */}
                <div className="bg-terminal-panel border border-terminal-border/50 rounded-md p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-5 h-5 rounded flex items-center justify-center bg-orange-500/10 text-orange-500">
                      <GitBranch className="w-3 h-3" />
                    </div>
                    <span className="text-xs font-semibold text-terminal-text">Checkpoints</span>
                  </div>
                  <div className="text-xs text-terminal-text-muted">
                    {template.checkpoint_count} resolution points with branching decisions
                  </div>
                  <div className="font-mono text-sm font-bold text-terminal-text mt-1">
                    {template.checkpoint_count}
                  </div>
                </div>

                {/* Branches — derivable from fork_points */}
                <div className="bg-terminal-panel border border-terminal-border/50 rounded-md p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-5 h-5 rounded flex items-center justify-center bg-purple-500/10 text-purple-500">
                      <GitBranch className="w-3 h-3" />
                    </div>
                    <span className="text-xs font-semibold text-terminal-text">Branches</span>
                  </div>
                  <div className="text-xs text-terminal-text-muted">
                    Fork points with {template.fork_points_min}–{template.fork_points_max} depth range
                  </div>
                  <div className="font-mono text-sm font-bold text-terminal-text mt-1">
                    {template.fork_points_max} max
                  </div>
                </div>

                {/* Replay — always available for completed runs */}
                <div className="bg-terminal-panel border border-terminal-border/50 rounded-md p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-5 h-5 rounded flex items-center justify-center bg-purple-500/10 text-purple-600">
                      <Play className="w-3 h-3" />
                    </div>
                    <span className="text-xs font-semibold text-terminal-text">Replay</span>
                  </div>
                  <div className="text-xs text-terminal-text-muted">
                    Fork replay output with disclosure events and settlement
                  </div>
                </div>

                {/* Theatre output — only if checkpoints can spawn */}
                {canSpawnTheatreCount > 0 && (
                  <div className="bg-terminal-panel border border-terminal-border/50 rounded-md p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-5 h-5 rounded flex items-center justify-center bg-orange-500/10 text-orange-500">
                        <Zap className="w-3 h-3" />
                      </div>
                      <span className="text-xs font-semibold text-terminal-text">Theatre</span>
                    </div>
                    <div className="text-xs text-terminal-text-muted">
                      {canSpawnTheatreCount} checkpoint{canSpawnTheatreCount !== 1 ? 's' : ''} can
                      spawn derived theatres at runtime
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Derived Theatres — pack-scoped (B5). Always visible; honest empty state when no pack launched yet. */}
          <div className="bg-terminal-surface border border-terminal-border rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-terminal-border/50 flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-terminal-text-muted" />
              <span className="text-[13px] font-semibold uppercase tracking-wide text-terminal-text-muted">
                Derived Theatres
              </span>
              <span className="text-[11px] text-terminal-text-muted font-medium ml-auto">
                pack-scoped
              </span>
            </div>
            <div className="p-4">
              {derivedTheatres.length > 0 ? (
                <div className="space-y-2">
                  {derivedTheatres.map((t) => (
                    <div
                      key={t.id}
                      className="flex items-center justify-between p-3 rounded bg-terminal-panel border border-terminal-border/50"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-mono text-[11px] text-terminal-text">
                          {t.construct_id}
                        </span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold uppercase ${theatreStateClasses(t.state)}`}
                        >
                          {t.state}
                        </span>
                        {t.spawned_from_checkpoint_id && (
                          <span className="text-[10px] text-terminal-text-muted">
                            from <span className="font-mono">{t.spawned_from_checkpoint_id.slice(0, 8)}</span>
                          </span>
                        )}
                        {t.certificate_id && (
                          <span className="text-[10px] text-terminal-text-muted">
                            cert <span className="font-mono">{t.certificate_id.slice(0, 8)}</span>
                          </span>
                        )}
                      </div>
                      <Link
                        to={`/theatre/${t.id}`}
                        className="text-[11px] font-semibold text-purple-500 hover:underline transition-colors shrink-0 ml-3"
                      >
                        View Theatre
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center">
                  <div className="text-[13px] text-terminal-text-muted mb-1">
                    {packId ? 'No derived theatres spawned' : 'No active pack'}
                  </div>
                  <div className="text-[10px] text-terminal-text-muted/60">
                    {packId
                      ? 'Theatres are spawned at runtime when checkpoints with can_spawn_theatre=true resolve.'
                      : 'Launch a run to see derived theatres spawned from checkpoint resolutions.'}
                  </div>
                </div>
              )}
            </div>
            <div className="px-5 py-3 border-t border-terminal-border/50 text-[11px] text-terminal-text-muted">
              Derived theatres are pack-scoped runtime outputs, not manually created via the Create Theatre flow.
            </div>
          </div>

          {/* Checkpoints detail */}
          {template.checkpoints?.length > 0 && (
            <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
              <div className="px-5 py-4 border-b border-terminal-border/50">
                <span className="text-[13px] font-semibold uppercase tracking-wide text-terminal-text-muted">
                  Checkpoints
                </span>
              </div>
              <div className="p-4 space-y-1.5">
                {template.checkpoints.map((cp) => (
                  <div
                    key={cp.id}
                    className="flex items-center justify-between text-xs p-2 bg-terminal-panel rounded"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-terminal-text-muted">#{cp.sequence_num}</span>
                      <span className="text-terminal-text">{cp.trigger}</span>
                    </div>
                    <div className="flex items-center gap-3 text-terminal-text-muted">
                      <span>{cp.branch_count} branches</span>
                      {cp.can_spawn_theatre && (
                        <span className="text-status-success">spawns theatre</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Branch probabilities — template-level */}
          {branchProbs?.probabilities && Object.keys(branchProbs.probabilities).length > 0 && (
            <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
              <div className="px-5 py-4 border-b border-terminal-border/50 flex items-center gap-2">
                <BarChart2 className="w-3.5 h-3.5 text-terminal-text-muted" />
                <span className="text-[13px] font-semibold uppercase tracking-wide text-terminal-text-muted">
                  Branch Probabilities
                </span>
                <span className="text-[10px] text-terminal-text-muted/60 ml-auto">template-level</span>
              </div>
              <div className="p-4 space-y-4">
                {Object.entries(branchProbs.probabilities).map(([checkpointId, probs]) => {
                  if (!probs) return null;
                  return (
                    <div key={checkpointId}>
                      <div className="text-[10px] font-mono text-terminal-text-muted mb-1.5">
                        {checkpointId}
                      </div>
                      <div className="space-y-1">
                        {Object.entries(probs).map(([branch, prob]) => (
                          <div key={branch} className="flex items-center gap-2">
                            <div className="w-24 text-[10px] text-terminal-text-muted truncate">{branch}</div>
                            <div className="flex-1 h-4 bg-terminal-panel rounded overflow-hidden">
                              <div
                                className="h-full bg-purple-500/30 rounded"
                                style={{ width: `${Math.max(prob * 100, 2)}%` }}
                              />
                            </div>
                            <div className="w-12 text-right text-[10px] font-mono tabular-nums text-purple-500">
                              {(prob * 100).toFixed(1)}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Run detail (after launch) */}
          {packId && runId && (
            <ScenarioRunDetail
              packId={packId}
              runId={runId}
              totalCheckpoints={template.checkpoint_count}
              runMode={runMode}
            />
          )}
        </div>

        {/* Right column: Launch panel + metadata */}
        <div className="lg:sticky lg:top-6 space-y-4">
          {/* Launch Configuration */}
          <div ref={launchPanelRef} className="bg-terminal-surface border border-terminal-border rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-terminal-border/50">
              <div className="text-[15px] font-semibold text-terminal-text">Launch Configuration</div>
            </div>
            <div className="p-5 space-y-4">
              {/* Run Mode */}
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wide text-terminal-text-muted block mb-1">
                  Run Mode
                </label>
                <select
                  value={runMode}
                  onChange={(e) => setRunMode(e.target.value as RunMode)}
                  disabled={!isRunnable || isLaunching || launchStep === 'done'}
                  className="w-full h-9 px-3 bg-terminal-surface border border-terminal-border rounded-md text-[13px] text-terminal-text disabled:opacity-40"
                >
                  {RUN_MODES.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label} — {m.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Agent Assignment */}
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wide text-terminal-text-muted block mb-1">
                  Agent Assignment
                </label>
                <select
                  value={agentAssignment}
                  onChange={(e) => setAgentAssignment(e.target.value)}
                  disabled={!isRunnable || isLaunching || launchStep === 'done'}
                  className="w-full h-9 px-3 bg-terminal-surface border border-terminal-border rounded-md text-[13px] text-terminal-text disabled:opacity-40"
                >
                  {AGENT_ASSIGNMENTS.map((a) => (
                    <option key={a.id} value={a.id}>{a.label}</option>
                  ))}
                </select>
              </div>

              {/* Simulation Scale */}
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wide text-terminal-text-muted block mb-1">
                  Simulation Scale
                </label>
                <select
                  value={simulationScale}
                  onChange={(e) => setSimulationScale(e.target.value)}
                  disabled={!isRunnable || isLaunching || launchStep === 'done'}
                  className="w-full h-9 px-3 bg-terminal-surface border border-terminal-border rounded-md text-[13px] text-terminal-text disabled:opacity-40"
                >
                  {SIMULATION_SCALES.map((s) => (
                    <option key={s.id} value={s.id}>{s.label}</option>
                  ))}
                </select>
              </div>

              {/* Objective Profile */}
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wide text-terminal-text-muted block mb-1">
                  Objective Profile
                </label>
                <select
                  value={objectiveProfile}
                  onChange={(e) => setObjectiveProfile(e.target.value)}
                  disabled={!isRunnable || isLaunching || launchStep === 'done'}
                  className="w-full h-9 px-3 bg-terminal-surface border border-terminal-border rounded-md text-[13px] text-terminal-text disabled:opacity-40"
                >
                  {OBJECTIVE_PROFILES.map((o) => (
                    <option key={o.id} value={o.id}>{o.label}</option>
                  ))}
                </select>
              </div>

              {/* Launch button */}
              {isRunnable ? (
                <>
                  <button
                    onClick={handleLaunch}
                    disabled={isLaunching || launchStep === 'done'}
                    className="w-full h-11 flex items-center justify-center gap-2 rounded-lg text-sm font-semibold text-white bg-purple-500 hover:bg-purple-400 transition-colors disabled:opacity-50"
                  >
                    {isLaunching ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : launchStep === 'done' ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <Play className="w-[18px] h-[18px]" />
                    )}
                    {launchStep === 'creating'
                      ? 'Creating pack...'
                      : launchStep === 'committing'
                        ? 'Committing...'
                        : launchStep === 'starting'
                          ? 'Starting run...'
                          : launchStep === 'done'
                            ? 'Run Started'
                            : 'Launch Run'}
                  </button>
                  {launchStep === 'error' && launchError && (
                    <div className="flex items-center gap-2 text-xs text-status-failure">
                      <XCircle className="w-3 h-3 shrink-0" />
                      {launchError}
                    </div>
                  )}
                  <div className="text-[11px] text-terminal-text-muted text-center leading-4">
                    Runs execute in the simulation environment. No live market impact.
                  </div>
                </>
              ) : (
                <>
                  <button
                    disabled
                    className="w-full h-11 flex items-center justify-center gap-2 rounded-lg text-sm font-semibold text-terminal-text-muted bg-terminal-panel cursor-not-allowed opacity-40"
                  >
                    Catalog Only
                  </button>
                  <div className="text-[11px] text-terminal-text-muted text-center leading-4">
                    This template is catalog-only and cannot be launched as a runnable pack.
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Pack Metadata — 8-field grid per reference */}
          <div className="bg-terminal-surface border border-terminal-border rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-terminal-border/50">
              <div className="text-[15px] font-semibold text-terminal-text">Pack Metadata</div>
            </div>
            <div className="p-5">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Family', value: FAMILY_LABELS[template.family] ?? template.family },
                  { label: 'Status', value: template.template_status },
                  { label: 'Checkpoints', value: String(template.checkpoint_count), mono: true },
                  { label: 'Branch Depth', value: `${template.fork_points_min}–${template.fork_points_max}`, mono: true },
                  { label: 'Episode Length', value: template.episode_length_sec ? `${template.episode_length_sec}s` : '—', mono: true },
                  { label: 'Seeded', value: template.is_seeded ? 'Yes' : 'No' },
                  { label: 'Agent Type', value: '—' },
                  { label: 'Objective', value: template.objective_vector?.length ? `${template.objective_vector.length} components` : '—' },
                ].map((item) => (
                  <div key={item.label} className="py-2">
                    <div className="text-[11px] font-semibold uppercase tracking-wide text-terminal-text-muted mb-0.5">
                      {item.label}
                    </div>
                    <div className={`text-sm font-medium text-terminal-text ${item.mono ? 'font-mono tabular-nums' : ''}`}>
                      {item.value}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
