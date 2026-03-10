import { useCallback, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity,
  ChevronRight,
  GitBranch,
  Loader2,
  PlayCircle,
  RotateCcw,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';
import { BranchMap } from './BranchMap';
import { useDerivedTheatres, useRunReplay, useRunTree } from '../../hooks/useScenarioPacks';
import type { DerivedTheatreResponse } from '../../types/scenarioPack';

interface RunStatusData {
  run_id: string;
  status: string;
  current_checkpoint_seq: number;
  total_checkpoints: number;
  total_reward: number;
}

interface ScenarioRunDetailProps {
  packId: string;
  runId: string;
  totalCheckpoints: number;
  runMode?: string;
}

function statusClasses(status: string): string {
  switch (status) {
    case 'COMPLETED':
      return 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.10)] text-[var(--e-green-600)]';
    case 'RUNNING':
      return 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.12)] text-[var(--e-orange-600)]';
    case 'FAILED':
      return 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]';
    default:
      return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]';
  }
}

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

export function ScenarioRunDetail({
  packId,
  runId,
  totalCheckpoints,
  runMode,
}: ScenarioRunDetailProps) {
  const [wsStatus, setWsStatus] = useState<RunStatusData | null>(null);
  const [selectedForkId, setSelectedForkId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const isReplay = runMode === 'REPLAY';

  const { data: treeData, isLoading: treeLoading } = useRunTree(packId, runId);
  const { data: replay } = useRunReplay(packId, runId);
  const { data: theatresData } = useDerivedTheatres(packId);

  const nodes = treeData?.nodes ?? [];
  const theatres: DerivedTheatreResponse[] = theatresData ?? [];
  const treeStatus = treeData?.status ?? wsStatus?.status ?? 'PENDING';

  const invalidateRunData = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['run-tree', packId, runId] });
    queryClient.invalidateQueries({ queryKey: ['run-replay', packId, runId] });
    queryClient.invalidateQueries({ queryKey: ['derived-theatres', packId] });
  }, [packId, queryClient, runId]);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        ws?.send(JSON.stringify({ action: 'subscribe', channel: `scenario_pack:${packId}` }));
      };
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'SCENARIO_RUN_STATUS' && message.data?.run_id === runId) {
          setWsStatus(message.data);
          if (message.data.status === 'COMPLETED') {
            invalidateRunData();
          }
        }
        if (message.type === 'CHECKPOINT_RESOLVED' && message.data?.run_id === runId) {
          invalidateRunData();
        }
        if (message.type === 'THEATRE_SPAWNED' && message.data?.pack_id === packId) {
          queryClient.invalidateQueries({ queryKey: ['derived-theatres', packId] });
        }
      };
    } catch {
      // WS may not be available locally.
    }

    return () => {
      ws?.close();
    };
  }, [invalidateRunData, packId, queryClient, runId]);

  if (treeLoading) {
    return (
      <section className="rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-12 shadow-[var(--e-shadow-xs)]">
        <div className="flex items-center justify-center text-[14px] text-[var(--e-text-muted)]">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading run detail…
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-5" data-testid="scenario-run-detail">
      <div className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-[var(--e-purple-500)]" />
            <h2 className="text-[14px] font-semibold text-[var(--e-text-primary)]">Run Status</h2>
            {isReplay ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
                <RotateCcw className="h-3 w-3" />
                Replay
              </span>
            ) : null}
          </div>
          <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
            {runId.slice(0, 12)}
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3 px-5 py-5 md:grid-cols-4">
          <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
              Status
            </div>
            <span
              className={clsx(
                'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
                statusClasses(treeStatus),
              )}
            >
              {treeStatus}
            </span>
          </div>
          <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
              Mode
            </div>
            <div className="font-mono text-[13px] font-semibold text-[var(--e-text-primary)]">
              {runMode ?? '—'}
            </div>
          </div>
          <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
              Checkpoints
            </div>
            <div className="font-mono text-[13px] font-semibold text-[var(--e-text-primary)]">
              {wsStatus?.current_checkpoint_seq ?? nodes.length} / {totalCheckpoints}
            </div>
          </div>
          <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
              Reward
            </div>
            <div className="font-mono text-[13px] font-semibold text-[var(--e-text-primary)]">
              {treeData?.total_reward ?? wsStatus?.total_reward ?? '---'}
            </div>
            {treeData?.episode_duration_sec != null ? (
              <div className="mt-1 font-mono text-[10px] text-[var(--e-text-muted)]">
                {treeData.episode_duration_sec.toFixed(1)}s
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
        <div className="flex items-center justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-[var(--e-purple-500)]" />
            <h2 className="text-[14px] font-semibold text-[var(--e-text-primary)]">Episode Tree</h2>
          </div>
          <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{nodes.length} resolved</span>
        </div>
        <div className="px-5 py-5">
          {nodes.length > 0 ? (
            <BranchMap nodes={nodes} />
          ) : (
            <div className="rounded-md border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center">
              <div className="text-[13px] font-medium text-[var(--e-text-primary)]">
                {treeStatus === 'RUNNING' ? 'Awaiting checkpoint resolutions…' : 'No checkpoint data available'}
              </div>
              <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-muted)]">
                {treeStatus === 'RUNNING'
                  ? 'Tree updates will appear as checkpoints resolve.'
                  : 'No episode tree has been persisted for this run yet.'}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
          <div className="flex items-center gap-2">
            <PlayCircle className="h-4 w-4 text-[var(--e-purple-500)]" />
            <h2 className="text-[14px] font-semibold text-[var(--e-text-primary)]">
              {isReplay ? 'Replay Trace' : 'Fork Replay'}
            </h2>
          </div>
          {isReplay ? (
            <span className="text-[12px] text-[var(--e-text-muted)]">exact recorded-path replay</span>
          ) : null}
        </div>

        <div className="px-5 py-5">
          {replay ? (
            <div className="space-y-4">
              <div className="text-[15px] font-semibold leading-6 text-[var(--e-text-primary)]">
                {replay.forkQuestion}
              </div>

              <div className="flex flex-wrap gap-2">
                {replay.options.map((option) => (
                  <button
                    key={option.label}
                    type="button"
                    onClick={() => setSelectedForkId(option.label)}
                    className={clsx(
                      'rounded-full border px-3 py-1 text-[11px] font-semibold transition',
                      selectedForkId === option.label
                        ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                        : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
                    )}
                  >
                    {option.label}
                  </button>
                ))}
              </div>

              {replay.chosenOption ? (
                <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  <span className="font-semibold text-[var(--e-text-primary)]">Settled:</span>{' '}
                  <span className="font-mono text-[var(--e-green-600)]">{replay.chosenOption}</span>
                  {replay.outcomeLabel ? ` — ${replay.outcomeLabel}` : ''}
                </div>
              ) : null}

              {replay.notes ? (
                <div className="font-mono text-[11px] leading-5 text-[var(--e-text-muted)]">{replay.notes}</div>
              ) : null}

              {replay.disclosureEvents.length > 0 ? (
                <div className="rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
                  <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Disclosure Events
                  </div>
                  <div className="space-y-2 px-4 py-4">
                    {replay.disclosureEvents.map((event, index) => (
                      <div key={`${event.tMs}-${index}`} className="flex flex-wrap items-center gap-3 text-[12px]">
                        <span className="font-mono text-[var(--e-text-muted)]">{event.tMs}ms</span>
                        <span className="rounded-full border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                          {event.type}
                        </span>
                        <span className="text-[var(--e-text-primary)]">{event.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="rounded-md border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center">
              <div className="text-[13px] font-medium text-[var(--e-text-primary)]">
                {treeStatus === 'COMPLETED' ? 'No replay data for this run' : 'Replay available after run completes'}
              </div>
              <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-muted)]">
                Replay output is generated only once the run has persisted replay state.
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-[var(--e-purple-500)]" />
            <h2 className="text-[14px] font-semibold text-[var(--e-text-primary)]">Derived Theatres</h2>
          </div>
          <span className="text-[11px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
            pack-scoped
          </span>
        </div>

        <div className="space-y-3 px-5 py-5">
          {theatres.length > 0 ? (
            theatres.map((theatre) => (
              <div
                key={theatre.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]"
              >
                <div className="min-w-0">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <span className="font-mono text-[12px] text-[var(--e-text-primary)]">{theatre.construct_id}</span>
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
            <div className="rounded-md border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center">
              <div className="text-[13px] font-medium text-[var(--e-text-primary)]">No derived theatres spawned</div>
              <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-muted)]">
                Pack-scoped theatre outputs will appear here when checkpoint resolutions emit them.
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default ScenarioRunDetail;
