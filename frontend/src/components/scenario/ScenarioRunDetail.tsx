/**
 * ScenarioRunDetail — Run status, episode tree, replay, and derived theatres.
 *
 * Surfaces real runtime outputs from the pack lifecycle:
 *   GET /api/v1/scenario-packs/{packId}/runs/{runId}/tree   → episode tree
 *   GET /api/v1/scenario-packs/{packId}/runs/{runId}/replay → fork replay
 *   GET /api/v1/scenario-packs/{packId}/derived-theatres    → spawned theatres
 *
 * WebSocket events for live updates:
 *   SCENARIO_RUN_STATUS   → run progress
 *   CHECKPOINT_RESOLVED   → new checkpoint result
 *
 * Run modes (scenario_seed_manager.py):
 *   TRAINING | EVALUATION | CALIBRATION | REPLAY
 *
 * REPLAY runs are clearly labeled as replays, not fresh runs.
 * Derived theatres show provenance (spawned_from_checkpoint_id).
 */

import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Activity, GitBranch, Loader2, PlayCircle, Zap, RotateCcw } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { BranchMap } from './BranchMap';
import { useRunTree, useDerivedTheatres, useRunReplay } from '../../hooks/useScenarioPacks';
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

/** Status badge colour classes using semantic tokens */
function statusClasses(status: string): string {
  switch (status) {
    case 'COMPLETED':
      return 'bg-status-success/15 text-status-success';
    case 'RUNNING':
      return 'bg-status-warning/15 text-status-warning';
    case 'FAILED':
      return 'bg-status-failure/15 text-status-failure';
    default:
      return 'bg-terminal-panel text-terminal-text-muted';
  }
}

/** Derived theatre state badge classes using semantic tokens */
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

export function ScenarioRunDetail({ packId, runId, totalCheckpoints, runMode }: ScenarioRunDetailProps) {
  const [wsStatus, setWsStatus] = useState<RunStatusData | null>(null);
  const [selectedForkId, setSelectedForkId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const isReplay = runMode === 'REPLAY';

  // React Query hooks — single source of truth for data
  const { data: treeData, isLoading: treeLoading } = useRunTree(packId, runId);
  const { data: theatresData } = useDerivedTheatres(packId);
  const { data: replay } = useRunReplay(packId, runId);

  const nodes = treeData?.nodes ?? [];
  const theatres: DerivedTheatreResponse[] = theatresData ?? [];
  const treeStatus = treeData?.status ?? wsStatus?.status ?? 'PENDING';

  // Invalidate React Query cache on WS events
  const invalidateRunData = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['run-tree', packId, runId] });
    queryClient.invalidateQueries({ queryKey: ['run-replay', packId, runId] });
    queryClient.invalidateQueries({ queryKey: ['derived-theatres', packId] });
  }, [queryClient, packId, runId]);

  // WebSocket subscription for live updates
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
        const msg = JSON.parse(event.data);
        if (msg.type === 'SCENARIO_RUN_STATUS' && msg.data?.run_id === runId) {
          setWsStatus(msg.data);
          if (msg.data.status === 'COMPLETED') {
            invalidateRunData();
          }
        }
        if (msg.type === 'CHECKPOINT_RESOLVED' && msg.data?.run_id === runId) {
          invalidateRunData();
        }
        // B6: THEATRE_SPAWNED — invalidate derived theatres cache
        if (msg.type === 'THEATRE_SPAWNED' && msg.data?.pack_id === packId) {
          queryClient.invalidateQueries({ queryKey: ['derived-theatres', packId] });
        }
      };
    } catch {
      // WS may not be available in test/dev
    }

    return () => {
      ws?.close();
    };
  }, [packId, runId, invalidateRunData]);

  if (treeLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="scenario-run-detail">
      {/* ── Run Status Header ──────────────────────────────────────── */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-terminal-text-muted" />
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Run Status
          </h3>
          {isReplay && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-echelon-cyan/10 text-echelon-cyan border border-echelon-cyan/20">
              <RotateCcw className="w-2.5 h-2.5" />
              REPLAY
            </span>
          )}
          <span className="font-mono text-[11px] text-terminal-text-muted ml-auto">
            {runId.slice(0, 12)}
          </span>
        </div>
        <div className="p-4">
          <div className="flex items-center gap-3">
            <span
              className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${statusClasses(treeStatus)}`}
              data-testid="run-status-badge"
            >
              {treeStatus}
            </span>
            {runMode && (
              <span className="text-[10px] font-mono text-terminal-text-muted">
                {runMode}
              </span>
            )}
          </div>
          <div className="flex items-center gap-4 mt-2 text-[11px] text-terminal-text-muted">
            <span>
              Checkpoints:{' '}
              <span className="font-mono text-terminal-text tabular-nums">
                {wsStatus?.current_checkpoint_seq ?? nodes.length} / {totalCheckpoints}
              </span>
            </span>
            <span>
              Reward:{' '}
              <span className="font-mono text-terminal-text tabular-nums">
                {treeData?.total_reward ?? wsStatus?.total_reward ?? '---'}
              </span>
            </span>
            {treeData?.episode_duration_sec != null && (
              <span>
                Duration:{' '}
                <span className="font-mono text-terminal-text tabular-nums">
                  {treeData.episode_duration_sec.toFixed(1)}s
                </span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── Episode Tree ───────────────────────────────────────────── */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center gap-2">
          <GitBranch className="w-3.5 h-3.5 text-terminal-text-muted" />
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Episode Tree
          </h3>
          <span className="font-mono text-[11px] text-terminal-text-muted ml-auto">
            {nodes.length} resolved
          </span>
        </div>
        <div className="p-4">
          {nodes.length > 0 ? (
            <BranchMap nodes={nodes} />
          ) : (
            <div className="py-6 text-center">
              <div className="text-[13px] text-terminal-text-muted mb-1">
                {treeStatus === 'RUNNING' ? 'Awaiting checkpoint resolutions...' : 'No checkpoint data available'}
              </div>
              <div className="text-[10px] font-mono text-terminal-text-muted/40">
                GET /api/v1/scenario-packs/{'{packId}'}/runs/{'{runId}'}/tree
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Fork Replay ────────────────────────────────────────────── */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center gap-2">
          <PlayCircle className="w-3.5 h-3.5 text-terminal-text-muted" />
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            {isReplay ? 'Replay Trace' : 'Fork Replay'}
          </h3>
          {isReplay && (
            <span className="text-[10px] text-terminal-text-muted/60">
              exact recorded-path replay
            </span>
          )}
          <span className="font-mono text-[11px] text-terminal-text-muted ml-auto">
            replay output
          </span>
        </div>
        <div className="p-4">
          {replay ? (
            <>
              {/* Fork question */}
              <div className="text-[13px] text-terminal-text font-medium mb-3">
                {replay.forkQuestion}
              </div>

              {/* Option pills */}
              <div className="flex gap-1.5 mb-3 flex-wrap">
                {replay.options.map((opt) => (
                  <button
                    key={opt.label}
                    onClick={() => setSelectedForkId(opt.label)}
                    className={`px-2.5 py-1.5 rounded text-[10px] font-mono font-semibold border transition-colors ${
                      selectedForkId === opt.label
                        ? 'bg-echelon-cyan/10 border-echelon-cyan/30 text-echelon-cyan'
                        : 'bg-terminal-panel border-terminal-border text-terminal-text-muted hover:text-terminal-text'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* Settlement */}
              {replay.chosenOption && (
                <div className="flex items-center gap-2 text-[11px] mb-3">
                  <span className="text-terminal-text-muted font-semibold">Settled:</span>
                  <span className="font-mono text-status-success">{replay.chosenOption}</span>
                  {replay.outcomeLabel && (
                    <span className="text-terminal-text-muted">— {replay.outcomeLabel}</span>
                  )}
                </div>
              )}

              {/* Seed and mode from notes */}
              {replay.notes && (
                <div className="text-[10px] font-mono text-terminal-text-muted/60 mb-3">
                  {replay.notes}
                </div>
              )}

              {/* Disclosure events */}
              {replay.disclosureEvents.length > 0 && (
                <div className="border-t border-terminal-border/50 pt-3">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted mb-2">
                    Disclosure Events
                  </div>
                  <div className="space-y-1">
                    {replay.disclosureEvents.map((e, i) => (
                      <div key={i} className="flex items-center gap-3 text-[11px]">
                        <span className="font-mono text-terminal-text-muted tabular-nums min-w-[56px]">
                          {e.tMs}ms
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-terminal-panel text-terminal-text-muted border border-terminal-border/50">
                          {e.type}
                        </span>
                        <span className="text-terminal-text">{e.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="py-6 text-center">
              <div className="text-[13px] text-terminal-text-muted mb-1">
                {treeStatus === 'COMPLETED'
                  ? 'No replay data for this run'
                  : 'Replay available after run completes'}
              </div>
              <div className="text-[10px] font-mono text-terminal-text-muted/40">
                GET /api/v1/scenario-packs/{'{packId}'}/runs/{'{runId}'}/replay
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Derived Theatres ───────────────────────────────────────── */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-terminal-text-muted" />
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Derived Theatres
          </h3>
          <span className="font-mono text-[11px] text-terminal-text-muted">
            {theatres.length} spawned
          </span>
          <span className="font-mono text-[11px] text-terminal-text-muted/50 ml-auto">
            pack-scoped
          </span>
        </div>
        <div className="p-4">
          {theatres.length > 0 ? (
            <div className="space-y-2">
              {theatres.map((t) => (
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
                        from{' '}
                        <span className="font-mono">{t.spawned_from_checkpoint_id.slice(0, 8)}</span>
                      </span>
                    )}
                    {t.certificate_id && (
                      <span className="text-[10px] text-terminal-text-muted">
                        cert {t.certificate_id.slice(0, 8)}
                      </span>
                    )}
                  </div>
                  <Link
                    to={`/theatre/${t.id}`}
                    className="text-[11px] font-semibold text-echelon-cyan hover:underline transition-colors shrink-0 ml-3"
                  >
                    View Theatre
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-6 text-center">
              <div className="text-[13px] text-terminal-text-muted mb-1">
                No derived theatres spawned
              </div>
              <div className="text-[10px] text-terminal-text-muted/60">
                Theatres are spawned at runtime when checkpoints with can_spawn_theatre=true resolve.
              </div>
              <div className="text-[10px] font-mono text-terminal-text-muted/40 mt-1">
                GET /api/v1/scenario-packs/{'{packId}'}/derived-theatres
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
