/**
 * ScenarioRunDetail — Run status, checkpoint results, and derived theatres display.
 *
 * Subscribes to WebSocket events for live updates:
 * - SCENARIO_RUN_STATUS: run progress
 * - CHECKPOINT_RESOLVED: new checkpoint result
 */

import { useEffect, useState, useCallback } from 'react';
import { Activity, GitBranch, ExternalLink, Loader2 } from 'lucide-react';
import { BranchMap } from './BranchMap';
import { apiClient } from '../../api/client';

interface EpisodeNode {
  checkpoint_id: string;
  sequence_num: number;
  trigger: string;
  market_question: string;
  selected_branch: string;
  outcome_type: string;
  reward: number;
  spawned_theatre_id: string | null;
}

interface DerivedTheatre {
  id: string;
  construct_id: string;
  state: string;
  spawned_from_checkpoint_id: string;
  certificate_id: string | null;
  created_at: string;
}

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
}

export function ScenarioRunDetail({ packId, runId, totalCheckpoints }: ScenarioRunDetailProps) {
  const [status, setStatus] = useState<RunStatusData | null>(null);
  const [nodes, setNodes] = useState<EpisodeNode[]>([]);
  const [theatres, setTheatres] = useState<DerivedTheatre[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [treeRes, theatreRes] = await Promise.all([
        apiClient.get(`/api/v1/scenario-packs/${packId}/runs/${runId}/tree`),
        apiClient.get(`/api/v1/scenario-packs/${packId}/derived-theatres`),
      ]);
      setNodes(treeRes.data.nodes ?? treeRes.data);
      setTheatres(theatreRes.data.theatres ?? theatreRes.data);
    } catch {
      // Endpoints may 404 if run not complete yet
    } finally {
      setLoading(false);
    }
  }, [packId, runId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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
          setStatus(msg.data);
          if (msg.data.status === 'COMPLETED') {
            fetchData();
          }
        }
        if (msg.type === 'CHECKPOINT_RESOLVED' && msg.data?.run_id === runId) {
          fetchData();
        }
      };
    } catch {
      // WS may not be available in test/dev
    }

    return () => {
      ws?.close();
    };
  }, [packId, runId, fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="scenario-run-detail">
      {/* Run status bar */}
      <div className="flex items-center gap-3 p-3 bg-terminal-surface border border-terminal-border rounded-lg">
        <Activity className="w-4 h-4 text-terminal-text-muted" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-terminal-text">
              Run {runId.slice(0, 8)}
            </span>
            <span
              className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                status?.status === 'COMPLETED'
                  ? 'bg-status-success/15 text-status-success'
                  : status?.status === 'RUNNING'
                    ? 'bg-status-warning/15 text-status-warning'
                    : 'bg-terminal-panel text-terminal-text-muted'
              }`}
              data-testid="run-status-badge"
            >
              {status?.status ?? 'PENDING'}
            </span>
          </div>
          {status && (
            <div className="text-[10px] text-terminal-text-muted mt-0.5">
              Checkpoint {status.current_checkpoint_seq} of {totalCheckpoints} — Reward: {status.total_reward}
            </div>
          )}
        </div>
      </div>

      {/* Branch map */}
      {nodes.length > 0 && (
        <div className="p-3 bg-terminal-surface border border-terminal-border rounded-lg">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch className="w-3.5 h-3.5 text-terminal-text-muted" />
            <span className="text-xs font-semibold text-terminal-text">Episode Tree</span>
          </div>
          <BranchMap nodes={nodes} />
        </div>
      )}

      {/* Derived theatres */}
      {theatres.length > 0 && (
        <div className="p-3 bg-terminal-surface border border-terminal-border rounded-lg">
          <div className="text-xs font-semibold text-terminal-text mb-2">
            Derived Theatres ({theatres.length})
          </div>
          <div className="space-y-1.5">
            {theatres.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between text-[10px] p-2 rounded bg-terminal-panel"
              >
                <div>
                  <span className="font-mono text-terminal-text">{t.construct_id}</span>
                  <span className="ml-2 text-terminal-text-muted">{t.state}</span>
                </div>
                <a
                  href={`/theatres/${t.id}`}
                  className="flex items-center gap-1 text-terminal-text-muted hover:text-terminal-text"
                >
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
