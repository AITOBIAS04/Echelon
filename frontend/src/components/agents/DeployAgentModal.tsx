/**
 * Deploy Agent Modal
 *
 * Staged deployment modal — agent-to-theatre assignment.
 *
 * BACKEND TRUTH (Cycle 019):
 *   POST /api/v1/agent-deployments — real endpoint, creates deployment record
 *   GET  /api/v1/agents            — real endpoint, returns agent roster
 *   GET  /api/v1/theatres          — NO list endpoint exists (only GET /{id})
 *
 * The theatre list will return empty until a list endpoint is added.
 * DeploymentGuardError surfaces as 422 with structured detail.
 *
 * STATES:
 *   1. Normal — agents loaded, theatres loaded (or empty), form active
 *   2. Empty  — no agents OR no theatres available (form disabled, explanation shown)
 *   3. Guard failure — deployment rejected by backend guard
 *   4. Success — deployment created, auto-close after 1.2s
 */

import { useState, useEffect, useMemo } from 'react';
import { X, Rocket, ChevronDown, Loader2, CheckCircle2, AlertCircle, ShieldAlert, Info } from 'lucide-react';
import { clsx } from 'clsx';
import { useCreateDeployment } from '../../hooks/useAgentDeployments';
import { useAgentRoster } from '../../hooks/useAgents';
import { apiClient } from '../../api/client';
import type { StrategyProfile } from '../../types/agentDeployment';

interface DeployAgentModalProps {
  open: boolean;
  onClose: () => void;
  preselectedAgentId?: string;
  preselectedTheatreId?: string;
}

const STRATEGIES: { id: StrategyProfile; label: string; description: string }[] = [
  { id: 'AGGRESSIVE', label: 'Aggressive', description: 'High risk, high reward' },
  { id: 'BALANCED', label: 'Balanced', description: 'Default strategy' },
  { id: 'DEFENSIVE', label: 'Defensive', description: 'Capital preservation' },
];

interface TheatreOption {
  id: string;
  construct_id: string;
  state: string;
}

export function DeployAgentModal({
  open,
  onClose,
  preselectedAgentId,
  preselectedTheatreId,
}: DeployAgentModalProps) {
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [selectedTheatreId, setSelectedTheatreId] = useState<string>('');
  const [strategy, setStrategy] = useState<StrategyProfile>('BALANCED');
  const [theatres, setTheatres] = useState<TheatreOption[]>([]);
  const [theatresLoading, setTheatresLoading] = useState(false);
  const [theatresError, setTheatresError] = useState(false);
  const [agentDropdownOpen, setAgentDropdownOpen] = useState(false);
  const [theatreDropdownOpen, setTheatreDropdownOpen] = useState(false);

  const { agents, isLoading: agentsLoading } = useAgentRoster();
  const createDeployment = useCreateDeployment();

  // Derive selected agent/theatre display names
  const selectedAgent = useMemo(
    () => agents.find((a) => a.id === selectedAgentId),
    [agents, selectedAgentId],
  );
  const selectedTheatre = useMemo(
    () => theatres.find((t) => t.id === selectedTheatreId),
    [theatres, selectedTheatreId],
  );

  // Load theatres from /api/v1/theatres
  // NOTE: No GET /api/v1/theatres list endpoint exists yet — will 404 gracefully
  useEffect(() => {
    if (!open) return;
    setTheatresLoading(true);
    setTheatresError(false);
    apiClient
      .get('/api/v1/theatres')
      .then((res) => {
        const items = (res.data?.theatres ?? res.data ?? []) as TheatreOption[];
        setTheatres(items);
      })
      .catch(() => {
        setTheatres([]);
        setTheatresError(true);
      })
      .finally(() => setTheatresLoading(false));
  }, [open]);

  // Reset state when modal opens
  useEffect(() => {
    if (open) {
      setSelectedAgentId(preselectedAgentId ?? '');
      setSelectedTheatreId(preselectedTheatreId ?? '');
      setStrategy('BALANCED');
      createDeployment.reset();
    }
  }, [open, preselectedAgentId, preselectedTheatreId]);

  // Lock body scroll
  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  if (!open) return null;

  const hasAgents = !agentsLoading && agents.length > 0;
  const hasTheatres = !theatresLoading && theatres.length > 0;
  // Theatre-context deployment: when theatre_id is preselected, deployment is viable
  // even without a theatre list endpoint
  const hasTheatreContext = !!preselectedTheatreId;
  const canDeploy = selectedAgentId && selectedTheatreId && !createDeployment.isPending;

  // Extract guard error detail from API response
  const guardError = createDeployment.isError
    ? parseGuardError(createDeployment.error)
    : null;

  const handleDeploy = () => {
    if (!canDeploy) return;
    createDeployment.mutate(
      {
        agent_id: selectedAgentId,
        theatre_id: selectedTheatreId,
        strategy_profile: strategy,
      },
      { onSuccess: () => setTimeout(onClose, 1200) },
    );
  };

  // Agent dropdown trigger text
  const agentTriggerText = agentsLoading
    ? 'Loading agents...'
    : selectedAgent
      ? (selectedAgent.name ?? selectedAgent.id)
      : agents.length === 0
        ? 'No agents available'
        : 'Select agent';

  // Theatre dropdown trigger text
  const theatreTriggerText = hasTheatreContext
    ? `Theatre: ${selectedTheatreId.slice(0, 12)}`
    : theatresLoading
      ? 'Loading theatres...'
      : selectedTheatre
        ? (selectedTheatre.construct_id ?? selectedTheatre.id)
        : theatres.length === 0
          ? 'No theatres available'
          : 'Select theatre';

  return (
    <>
      <div className="fixed inset-0 bg-terminal-bg/80 backdrop-blur-sm z-[300]" onClick={onClose} />
      <div
        className="fixed inset-0 z-[310] flex items-center justify-center p-4 pointer-events-none"
        onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      >
        <div
          className="bg-terminal-bg border border-terminal-border rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col pointer-events-auto shadow-2xl"
          onClick={(e) => e.stopPropagation()}
          data-testid="deploy-agent-modal"
        >
          {/* Header */}
          <div className="p-5 border-b border-terminal-border flex items-center justify-between bg-terminal-surface">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-echelon-cyan/10 rounded-full flex items-center justify-center border border-echelon-cyan/20">
                <Rocket className="w-5 h-5 text-echelon-cyan" />
              </div>
              <div>
                <h3 className="text-white font-sans font-bold tracking-tight text-lg">Deploy Agent</h3>
                <p className="text-terminal-text-muted text-xs">Assign agent to theatre with strategy</p>
              </div>
            </div>
            <button onClick={onClose} className="text-terminal-text-muted hover:text-white transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto flex-1 space-y-5">
            {/* Success state */}
            {createDeployment.isSuccess && (
              <div className="bg-status-success/10 border border-status-success/30 rounded-lg p-4 flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-status-success" />
                <div>
                  <div className="text-sm font-semibold text-status-success">Agent Deployed</div>
                  <div className="text-xs text-terminal-text-muted mt-0.5">
                    Deployment ID: <span className="font-mono">{createDeployment.data?.id}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Guard error state — deployment rejected by backend guard */}
            {guardError && (
              <div className="bg-status-failure/10 border border-status-failure/30 rounded-lg p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-status-failure shrink-0" />
                  <span className="text-xs font-semibold text-status-failure">Deployment Guard Failure</span>
                </div>
                <p className="text-xs text-status-failure/80 font-mono">{guardError}</p>
              </div>
            )}

            {/* Generic error state (non-guard) */}
            {createDeployment.isError && !guardError && (
              <div className="bg-status-failure/10 border border-status-failure/30 rounded-lg p-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-status-failure" />
                <span className="text-xs text-status-failure">
                  {(createDeployment.error as Error)?.message ?? 'Deployment failed'}
                </span>
              </div>
            )}

            {/* Unavailable state — no theatres loaded and no preselected theatre context */}
            {!theatresLoading && theatres.length === 0 && theatresError && !hasTheatreContext && (
              <div className="bg-terminal-surface border border-terminal-border rounded-lg p-4 flex items-start gap-3">
                <Info className="w-4 h-4 text-terminal-text-muted shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-semibold text-terminal-text">Theatre selection unavailable</div>
                  <div className="text-xs text-terminal-text-muted mt-1">
                    No theatre list endpoint exists (GET /api/v1/theatres). Deploy agents from a theatre detail page where the theatre context is already known.
                  </div>
                </div>
              </div>
            )}

            {/* Agent selection */}
            <div>
              <label className="text-xs font-sans text-terminal-text-muted uppercase tracking-wide block mb-2">
                Agent
              </label>
              <div className="relative">
                <button
                  onClick={() => hasAgents && setAgentDropdownOpen(!agentDropdownOpen)}
                  disabled={agentsLoading || !hasAgents}
                  className={clsx(
                    'w-full flex items-center justify-between border rounded-lg px-3 py-2.5 text-sm font-mono transition-all',
                    hasAgents
                      ? 'bg-terminal-bg border-terminal-border text-white hover:border-echelon-cyan/40'
                      : 'bg-terminal-bg border-terminal-border/50 text-terminal-text-muted cursor-not-allowed',
                  )}
                >
                  <span className={selectedAgent ? 'text-white' : 'text-terminal-text-muted'}>
                    {agentTriggerText}
                  </span>
                  {hasAgents && (
                    <ChevronDown className={clsx('w-4 h-4 text-terminal-text-muted transition', agentDropdownOpen && 'rotate-180')} />
                  )}
                  {agentsLoading && <Loader2 className="w-4 h-4 text-terminal-text-muted animate-spin" />}
                </button>
                {agentDropdownOpen && agents.length > 0 && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setAgentDropdownOpen(false)} />
                    <div className="absolute top-full left-0 mt-1 w-full bg-terminal-panel border border-terminal-border rounded-lg shadow-lg z-20 max-h-40 overflow-y-auto">
                      {agents.map((agent) => (
                        <button
                          key={agent.id}
                          onClick={() => { setSelectedAgentId(agent.id); setAgentDropdownOpen(false); }}
                          className={clsx(
                            'w-full text-left px-3 py-2.5 text-xs font-mono hover:bg-terminal-card transition flex items-center justify-between',
                            selectedAgentId === agent.id ? 'text-echelon-cyan' : 'text-terminal-text',
                          )}
                        >
                          <span>{agent.name ?? agent.id}</span>
                          <span className="text-terminal-text-muted text-[10px]">{agent.archetype}</span>
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Theatre selection */}
            <div>
              <label className="text-xs font-sans text-terminal-text-muted uppercase tracking-wide block mb-2">
                Theatre
              </label>
              <div className="relative">
                <button
                  onClick={() => !hasTheatreContext && hasTheatres && setTheatreDropdownOpen(!theatreDropdownOpen)}
                  disabled={hasTheatreContext || theatresLoading || !hasTheatres}
                  className={clsx(
                    'w-full flex items-center justify-between border rounded-lg px-3 py-2.5 text-sm font-mono transition-all',
                    hasTheatreContext
                      ? 'bg-terminal-bg border-echelon-cyan/30 text-echelon-cyan cursor-default'
                      : hasTheatres
                        ? 'bg-terminal-bg border-terminal-border text-white hover:border-echelon-cyan/40'
                        : 'bg-terminal-bg border-terminal-border/50 text-terminal-text-muted cursor-not-allowed',
                  )}
                >
                  <span className={clsx(
                    hasTheatreContext ? 'text-echelon-cyan' : selectedTheatre ? 'text-white' : 'text-terminal-text-muted',
                  )}>
                    {theatreTriggerText}
                  </span>
                  {!hasTheatreContext && hasTheatres && (
                    <ChevronDown className={clsx('w-4 h-4 text-terminal-text-muted transition', theatreDropdownOpen && 'rotate-180')} />
                  )}
                  {theatresLoading && !hasTheatreContext && <Loader2 className="w-4 h-4 text-terminal-text-muted animate-spin" />}
                </button>
                {theatreDropdownOpen && theatres.length > 0 && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setTheatreDropdownOpen(false)} />
                    <div className="absolute top-full left-0 mt-1 w-full bg-terminal-panel border border-terminal-border rounded-lg shadow-lg z-20 max-h-40 overflow-y-auto">
                      {theatres.map((t) => (
                        <button
                          key={t.id}
                          onClick={() => { setSelectedTheatreId(t.id); setTheatreDropdownOpen(false); }}
                          className={clsx(
                            'w-full text-left px-3 py-2.5 text-xs font-mono hover:bg-terminal-card transition flex items-center justify-between',
                            selectedTheatreId === t.id ? 'text-echelon-cyan' : 'text-terminal-text',
                          )}
                        >
                          <span>{t.construct_id ?? t.id}</span>
                          <span className="text-terminal-text-muted text-[10px]">{t.state}</span>
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Strategy */}
            <div>
              <label className="text-xs font-sans text-terminal-text-muted uppercase tracking-wide block mb-2">
                Strategy Profile
              </label>
              <div className="flex gap-2">
                {STRATEGIES.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setStrategy(s.id)}
                    className={clsx(
                      'flex-1 px-2 py-2.5 text-xs rounded-lg border transition-all text-left',
                      strategy === s.id
                        ? 'bg-echelon-cyan/10 border-echelon-cyan/30 text-echelon-cyan'
                        : 'bg-terminal-bg border-terminal-border text-terminal-text-muted hover:text-terminal-text hover:border-terminal-border',
                    )}
                  >
                    <div className="font-semibold">{s.label}</div>
                    <div className={clsx(
                      'text-[10px] mt-0.5',
                      strategy === s.id ? 'text-echelon-cyan/70' : 'text-terminal-text-muted',
                    )}>
                      {s.description}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-5 border-t border-terminal-border bg-terminal-surface flex gap-3 rounded-b-xl">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-white/5 text-terminal-text-muted rounded-lg font-bold hover:bg-white/10 transition-colors font-sans text-sm"
            >
              Cancel
            </button>
            <button
              onClick={handleDeploy}
              disabled={!canDeploy}
              className={clsx(
                'flex-1 px-4 py-3 rounded-lg font-bold flex items-center justify-center gap-2 font-sans text-sm transition-colors',
                canDeploy
                  ? 'bg-echelon-cyan/20 border border-echelon-cyan/40 text-echelon-cyan hover:bg-echelon-cyan/30'
                  : 'bg-echelon-cyan/10 border border-echelon-cyan/20 text-echelon-cyan/50 cursor-not-allowed',
              )}
            >
              {createDeployment.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Rocket className="w-4 h-4" />
              )}
              {createDeployment.isPending ? 'Deploying...' : 'Deploy'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

/**
 * Extract guard error detail from API error response.
 * DeploymentGuardError returns structured detail from the backend.
 */
function parseGuardError(error: unknown): string | null {
  if (!error) return null;
  const err = error as { response?: { data?: { detail?: string } }; message?: string };
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string' && detail.toLowerCase().includes('guard')) {
    return detail;
  }
  return null;
}

export default DeployAgentModal;
