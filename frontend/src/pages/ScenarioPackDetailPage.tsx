import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  GitBranch,
  Loader2,
  Play,
  Sparkles,
  XCircle,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';
import {
  useBranchProbabilities,
  useCommitPack,
  useCreatePack,
  useDerivedTheatres,
  usePackDetail,
  useStartRun,
  useTemplateDetail,
} from '../hooks/useScenarioPacks';
import { BranchMap } from '../components/scenario/BranchMap';
import { ScenarioRunDetail } from '../components/scenario/ScenarioRunDetail';
import type { DerivedTheatreResponse } from '../types/scenarioPack';

type RunMode = 'TRAINING' | 'EVALUATION' | 'CALIBRATION' | 'REPLAY';

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

const RUN_MODES: Array<{ id: RunMode; label: string; description: string }> = [
  { id: 'TRAINING', label: 'Training', description: 'Varying seeds across fresh runs' },
  { id: 'EVALUATION', label: 'Evaluation', description: 'Pinned evaluation seed set' },
  { id: 'CALIBRATION', label: 'Calibration', description: 'Canonical calibration seeds' },
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
  { id: 'pack_default', label: 'Pack default' },
  { id: 'maximize_delivery_rate', label: 'Maximise delivery rate' },
  { id: 'minimize_detection', label: 'Minimise detection' },
  { id: 'balanced_risk_reward', label: 'Balanced risk / reward' },
];

function theatreStateClasses(state: string): string {
  switch (state) {
    case 'RUNNING':
      return 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.12)] text-[var(--e-orange-600)]';
    case 'SETTLED':
      return 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.10)] text-[var(--e-green-600)]';
    default:
      return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]';
  }
}

function SelectField({
  label,
  value,
  onChange,
  disabled,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  options: Array<{ id: string; label: string; description?: string }>;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </label>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        className="h-10 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-primary)] outline-none transition focus:border-[var(--e-border-focus)] disabled:cursor-not-allowed disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
      >
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.description ? `${option.label} — ${option.description}` : option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function MetadataCell({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className={clsx('text-[13px] font-medium text-[var(--e-text-primary)]', mono && 'font-mono tabular-nums')}>
        {value}
      </div>
    </div>
  );
}

function OutputCard({
  label,
  description,
  icon,
  value,
}: {
  label: string;
  description: string;
  icon: React.ReactNode;
  value?: string;
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
      <div className="mb-3 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]">
          {icon}
        </div>
        <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">{label}</div>
      </div>
      <div className="text-[13px] leading-5 text-[var(--e-text-secondary)]">{description}</div>
      {value ? (
        <div className="mt-3 font-mono text-[14px] font-semibold text-[var(--e-text-primary)]">{value}</div>
      ) : null}
    </div>
  );
}

export function ScenarioPackDetailPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const launchPanelRef = useRef<HTMLDivElement>(null);

  const { data: template, isLoading: templateLoading } = useTemplateDetail(templateId ?? null);
  const [packId, setPackId] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [packCommitted, setPackCommitted] = useState(false);
  const [runMode, setRunMode] = useState<RunMode>('TRAINING');
  const [agentAssignment, setAgentAssignment] = useState('auto_assign');
  const [simulationScale, setSimulationScale] = useState('single_1x');
  const [objectiveProfile, setObjectiveProfile] = useState('pack_default');
  const [launchStep, setLaunchStep] = useState<'idle' | 'creating' | 'committing' | 'starting' | 'done' | 'error'>('idle');
  const [launchError, setLaunchError] = useState<string | null>(null);

  const createPack = useCreatePack();
  const commitPack = useCommitPack();
  const startRun = useStartRun();
  const { data: packDetail } = usePackDetail(packId);
  const { data: branchProbabilities } = useBranchProbabilities(templateId ?? null);
  const { data: derivedTheatresData } = useDerivedTheatres(packId);
  const derivedTheatres: DerivedTheatreResponse[] = derivedTheatresData ?? [];

  useEffect(() => {
    if (searchParams.get('launch') === 'true' && launchPanelRef.current && !templateLoading) {
      launchPanelRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams, templateLoading]);

  const canSpawnTheatreCount = useMemo(
    () => template?.checkpoints?.filter((checkpoint) => checkpoint.can_spawn_theatre).length ?? 0,
    [template],
  );

  const useTags = useMemo(
    () =>
      RUN_MODES.map((mode) => ({
        ...mode,
        active: runMode === mode.id,
      })),
    [runMode],
  );

  if (templateLoading) {
    return (
      <div className="p-6">
        <div className="mx-auto flex max-w-6xl items-center justify-center rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-16 shadow-[var(--e-shadow-xs)]">
          <Loader2 className="mr-2 h-5 w-5 animate-spin text-[var(--e-text-muted)]" />
          <span className="text-[14px] text-[var(--e-text-muted)]">Loading scenario pack…</span>
        </div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-6xl rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-16 text-center text-[14px] text-[var(--e-text-muted)] shadow-[var(--e-shadow-xs)]">
          Scenario pack template not found.
        </div>
      </div>
    );
  }

  const isRunnable = template.template_status === 'RUNNABLE';
  const isLaunching = !['idle', 'done', 'error'].includes(launchStep);

  const handleLaunch = async () => {
    if (!isRunnable) return;
    setLaunchError(null);

    try {
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
        setPackId(newPack.id);
      }

      if (!packCommitted) {
        setLaunchStep('committing');
        await commitPack.mutateAsync(currentPackId);
        setPackCommitted(true);
      }

      if (!runId) {
        setLaunchStep('starting');
        const run = await startRun.mutateAsync(currentPackId);
        setRunId(run.id);
      }

      setLaunchStep('done');
    } catch (error) {
      setLaunchStep('error');
      setLaunchError(error instanceof Error ? error.message : 'Launch failed');
    }
  };

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <Link
          to="/scenario-packs"
          className="inline-flex items-center gap-2 text-[12px] font-medium text-[var(--e-text-muted)] no-underline transition hover:text-[var(--e-text-primary)]"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Scenario Packs
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-4xl">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
                {FAMILY_LABELS[template.family] ?? template.family}
              </span>
              <span
                className={clsx(
                  'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.04em]',
                  isRunnable
                    ? 'bg-[var(--e-green-50)] text-[var(--e-green-600)]'
                    : 'bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
                )}
              >
                <span
                  className={clsx(
                    'h-2 w-2 rounded-full',
                    isRunnable ? 'bg-[var(--e-green-600)]' : 'bg-[var(--e-text-disabled)]',
                  )}
                />
                {template.template_status}
              </span>
            </div>
            <h1 className="text-[36px] font-bold tracking-[-0.03em] text-[var(--e-text-primary)]">
              {template.name}
            </h1>
            <p className="mt-3 max-w-3xl text-[15px] leading-7 text-[var(--e-text-secondary)]">
              {template.description}
            </p>
          </div>
        </div>

        {!isRunnable ? (
          <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-5 py-4 shadow-[var(--e-shadow-xs)]">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]">
                <BookOpen className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[14px] font-semibold text-[var(--e-text-primary)]">
                  Catalog-only template
                </div>
                <div className="mt-1 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  This pack can be inspected and compared, but cannot be instantiated as a runnable scenario.
                </div>
              </div>
            </div>
          </div>
        ) : null}

        <div className="flex flex-wrap gap-2">
          {useTags.map((tag) => (
            <span
              key={tag.id}
              className={clsx(
                'inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.04em]',
                tag.active
                  ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                  : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-muted)]',
              )}
            >
              {tag.label}
            </span>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-6">
            <section
              id="branch-map"
              className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]"
            >
              <div className="flex items-center justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
                <div className="flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-[var(--e-purple-500)]" />
                  <h2 className="text-[14px] font-semibold text-[var(--e-text-primary)]">Branch Map</h2>
                </div>
                <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
                  {template.checkpoint_count} checkpoints
                </span>
              </div>
              <div className="px-5 py-5">
                {template.checkpoints?.length ? (
                  <BranchMap
                    nodes={template.checkpoints.map((checkpoint) => ({
                      checkpoint_id: checkpoint.id,
                      sequence_num: checkpoint.sequence_num,
                      trigger: checkpoint.trigger,
                      market_question: checkpoint.market_question,
                      selected_branch: null,
                      outcome_type: null,
                      reward: null,
                      spawned_theatre_id: null,
                    }))}
                  />
                ) : (
                  <div className="rounded-md border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-6 text-center text-[13px] text-[var(--e-text-muted)]">
                    No checkpoint data available for this template.
                  </div>
                )}
              </div>
              <div className="flex flex-wrap gap-4 border-t border-[var(--e-border-secondary)] px-5 py-3 text-[11px] text-[var(--e-text-muted)]">
                {[
                  { label: 'Start', color: 'bg-[var(--e-purple-500)]' },
                  { label: 'Checkpoint', color: 'bg-[var(--e-orange-500)]' },
                  { label: 'Success', color: 'bg-[var(--e-green-600)]' },
                  { label: 'Failure', color: 'bg-[var(--e-red-600)]' },
                ].map((legend) => (
                  <div key={legend.label} className="flex items-center gap-2">
                    <span className={clsx('h-2.5 w-2.5 rounded-full', legend.color)} />
                    {legend.label}
                  </div>
                ))}
              </div>
            </section>

            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-[16px] font-semibold text-[var(--e-text-primary)]">Expected Outputs</h2>
                <span className="text-[12px] text-[var(--e-text-muted)]">Only data-backed outputs shown</span>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <OutputCard
                  label="Checkpoints"
                  description="Resolution points that determine episode flow."
                  icon={<GitBranch className="h-4 w-4" />}
                  value={String(template.checkpoint_count)}
                />
                <OutputCard
                  label="Branches"
                  description={`Fork range ${template.fork_points_min}–${template.fork_points_max} based on template fork points.`}
                  icon={<ChevronRight className="h-4 w-4" />}
                  value={`${template.fork_points_max} max`}
                />
                <OutputCard
                  label="Replay"
                  description="Fork replay with disclosure events and final settlement once a run completes."
                  icon={<Play className="h-4 w-4" />}
                />
                {canSpawnTheatreCount > 0 ? (
                  <OutputCard
                    label="Derived Theatres"
                    description={`${canSpawnTheatreCount} checkpoint${canSpawnTheatreCount === 1 ? '' : 's'} can emit pack-scoped theatre outputs at runtime.`}
                    icon={<Zap className="h-4 w-4" />}
                  />
                ) : null}
              </div>
            </section>

            <section className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
              <div className="flex items-center justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-[var(--e-purple-500)]" />
                  <h2 className="text-[14px] font-semibold text-[var(--e-text-primary)]">Derived Theatres</h2>
                </div>
                <span className="text-[11px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                  pack-scoped
                </span>
              </div>
              <div className="space-y-3 px-5 py-5">
                {derivedTheatres.length > 0 ? (
                  derivedTheatres.map((theatre) => (
                    <div
                      key={theatre.id}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]"
                    >
                      <div className="min-w-0">
                        <div className="mb-1 flex flex-wrap items-center gap-2">
                          <span className="font-mono text-[12px] text-[var(--e-text-primary)]">
                            {theatre.construct_id}
                          </span>
                          <span
                            className={clsx(
                              'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
                              theatreStateClasses(theatre.state),
                            )}
                          >
                            {theatre.state}
                          </span>
                        </div>
                        <div className="text-[12px] leading-5 text-[var(--e-text-secondary)]">
                          {theatre.spawned_from_checkpoint_id ? (
                            <>
                              Spawned from checkpoint{' '}
                              <span className="font-mono text-[var(--e-text-primary)]">
                                {theatre.spawned_from_checkpoint_id.slice(0, 8)}
                              </span>
                            </>
                          ) : (
                            'Spawn checkpoint provenance unavailable'
                          )}
                          {theatre.certificate_id ? (
                            <>
                              {' '}
                              · certificate{' '}
                              <span className="font-mono text-[var(--e-text-primary)]">
                                {theatre.certificate_id.slice(0, 8)}
                              </span>
                            </>
                          ) : null}
                        </div>
                      </div>
                      <Link
                        to={`/theatre/${theatre.id}`}
                        className="inline-flex items-center gap-1 text-[12px] font-semibold text-[var(--e-purple-700)] no-underline transition hover:text-[var(--e-purple-500)]"
                      >
                        View Theatre
                        <ChevronRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  ))
                ) : (
                  <div className="rounded-md border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-6 text-center">
                    <div className="text-[13px] font-medium text-[var(--e-text-primary)]">
                      {packId ? 'No derived theatres spawned' : 'No active pack'}
                    </div>
                    <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-muted)]">
                      {packId
                        ? 'Theatres appear here when runtime checkpoint resolutions spawn them.'
                        : 'Launch a run to see pack-scoped theatre outputs from runtime checkpoints.'}
                    </div>
                  </div>
                )}
              </div>
              <div className="border-t border-[var(--e-border-secondary)] px-5 py-3 text-[12px] leading-5 text-[var(--e-text-muted)]">
                Derived theatres are pack-scoped outputs from checkpoint resolution rules, not a manual follow-up create flow.
              </div>
            </section>

            {template.checkpoints?.length ? (
              <section className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
                <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
                  <h2 className="text-[14px] font-semibold text-[var(--e-text-primary)]">Checkpoints</h2>
                </div>
                <div className="space-y-2 px-5 py-5">
                  {template.checkpoints.map((checkpoint) => (
                    <div
                      key={checkpoint.id}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]"
                    >
                      <div className="min-w-0">
                        <div className="mb-1 flex items-center gap-2">
                          <span className="font-mono text-[11px] text-[var(--e-text-muted)]">#{checkpoint.sequence_num}</span>
                          <span className="text-[13px] font-medium text-[var(--e-text-primary)]">
                            {checkpoint.trigger}
                          </span>
                        </div>
                        <div className="text-[12px] text-[var(--e-text-secondary)]">
                          {checkpoint.market_question}
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] font-medium text-[var(--e-text-muted)]">
                        <span>{checkpoint.branch_count} branches</span>
                        {checkpoint.can_spawn_theatre ? (
                          <span className="rounded-full bg-[var(--e-green-50)] px-2 py-0.5 text-[var(--e-green-600)]">
                            spawns theatre
                          </span>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            {branchProbabilities?.probabilities && Object.keys(branchProbabilities.probabilities).length > 0 ? (
              <section className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
                <div className="flex items-center justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
                  <h2 className="text-[14px] font-semibold text-[var(--e-text-primary)]">Branch Probabilities</h2>
                  <span className="text-[11px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                    template-level
                  </span>
                </div>
                <div className="space-y-5 px-5 py-5">
                  {Object.entries(branchProbabilities.probabilities).map(([checkpointId, probabilities]) => {
                    if (!probabilities) return null;
                    return (
                      <div key={checkpointId}>
                        <div className="mb-2 font-mono text-[11px] text-[var(--e-text-muted)]">{checkpointId}</div>
                        <div className="space-y-2">
                          {Object.entries(probabilities).map(([branchId, probability]) => (
                            <div key={branchId} className="flex items-center gap-3">
                              <div className="w-28 truncate text-[11px] text-[var(--e-text-secondary)]">
                                {branchId}
                              </div>
                              <div className="h-5 flex-1 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
                                <div
                                  className="h-full rounded-full bg-[var(--e-purple-500)]/25"
                                  style={{ width: `${Math.max(probability * 100, 2)}%` }}
                                />
                              </div>
                              <div className="w-14 text-right font-mono text-[11px] font-semibold tabular-nums text-[var(--e-purple-700)]">
                                {(probability * 100).toFixed(1)}%
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            ) : null}

            {packId && runId ? (
              <ScenarioRunDetail
                packId={packId}
                runId={runId}
                totalCheckpoints={template.checkpoint_count}
                runMode={runMode}
              />
            ) : null}
          </div>

          <aside className="space-y-4 xl:sticky xl:top-20">
            <section
              ref={launchPanelRef}
              className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]"
            >
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
                <h2 className="text-[15px] font-semibold text-[var(--e-text-primary)]">Launch Configuration</h2>
              </div>
              <div className="space-y-4 px-5 py-5">
                <SelectField
                  label="Run Mode"
                  value={runMode}
                  onChange={(value) => setRunMode(value as RunMode)}
                  options={RUN_MODES}
                  disabled={!isRunnable || isLaunching || launchStep === 'done'}
                />
                <SelectField
                  label="Agent Assignment"
                  value={agentAssignment}
                  onChange={setAgentAssignment}
                  options={AGENT_ASSIGNMENTS}
                  disabled={!isRunnable || isLaunching || launchStep === 'done'}
                />
                <SelectField
                  label="Simulation Scale"
                  value={simulationScale}
                  onChange={setSimulationScale}
                  options={SIMULATION_SCALES}
                  disabled={!isRunnable || isLaunching || launchStep === 'done'}
                />
                <SelectField
                  label="Objective Profile"
                  value={objectiveProfile}
                  onChange={setObjectiveProfile}
                  options={OBJECTIVE_PROFILES}
                  disabled={!isRunnable || isLaunching || launchStep === 'done'}
                />

                {isRunnable ? (
                  <>
                    <button
                      type="button"
                      onClick={handleLaunch}
                      disabled={isLaunching || launchStep === 'done'}
                      className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[var(--e-purple-500)] px-4 text-[14px] font-semibold text-[var(--e-text-inverse)] transition hover:bg-[var(--e-purple-600)] disabled:cursor-not-allowed disabled:bg-[var(--e-purple-200)] disabled:text-[var(--e-text-disabled)]"
                    >
                      {isLaunching ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : launchStep === 'done' ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      {launchStep === 'creating'
                        ? 'Creating pack…'
                        : launchStep === 'committing'
                          ? 'Committing…'
                          : launchStep === 'starting'
                            ? 'Starting run…'
                            : launchStep === 'done'
                              ? 'Run Started'
                              : 'Launch Run'}
                    </button>
                    {launchError ? (
                      <div className="flex items-start gap-2 rounded-md border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-3 py-3 text-[12px] text-[var(--e-red-600)]">
                        <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
                        {launchError}
                      </div>
                    ) : null}
                    <div className="text-[12px] leading-5 text-[var(--e-text-muted)]">
                      Launch composes create → commit → run. Retries resume from the failed step rather than creating duplicate packs.
                    </div>
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      disabled
                      className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[var(--e-bg-sunken)] px-4 text-[14px] font-semibold text-[var(--e-text-disabled)]"
                    >
                      Catalog Only
                    </button>
                    <div className="text-[12px] leading-5 text-[var(--e-text-muted)]">
                      This template can be browsed and compared, but cannot be instantiated as a runnable pack.
                    </div>
                  </>
                )}
              </div>
            </section>

            <section className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
                <h2 className="text-[15px] font-semibold text-[var(--e-text-primary)]">Pack Metadata</h2>
              </div>
              <div className="grid grid-cols-2 gap-3 px-5 py-5">
                <MetadataCell label="Family" value={FAMILY_LABELS[template.family] ?? template.family} />
                <MetadataCell label="Status" value={template.template_status} />
                <MetadataCell label="Checkpoints" value={String(template.checkpoint_count)} mono />
                <MetadataCell label="Branch Depth" value={`${template.fork_points_min}–${template.fork_points_max}`} mono />
                <MetadataCell label="Episode Length" value={template.episode_length_sec ? `${template.episode_length_sec}s` : '—'} mono />
                <MetadataCell label="Seeded" value={template.is_seeded ? 'Yes' : 'No'} />
                <MetadataCell label="Agent Type" value={packDetail?.agent_assignment ?? '—'} />
                <MetadataCell
                  label="Objective"
                  value={
                    packDetail?.objective_profile ??
                    (template.objective_vector?.length
                      ? `${template.objective_vector.length} components`
                      : '—')
                  }
                />
              </div>
              {packDetail ? (
                <div className="border-t border-[var(--e-border-secondary)] px-5 py-3 text-[12px] leading-5 text-[var(--e-text-muted)]">
                  Pack {packDetail.id.slice(0, 12)} is currently <span className="font-semibold text-[var(--e-text-primary)]">{packDetail.state}</span>.
                </div>
              ) : null}
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default ScenarioPackDetailPage;
