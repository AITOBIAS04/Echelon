import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Info,
  Loader2,
  Rocket,
  ShieldAlert,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import { apiClient } from '../../api/client';
import { useCreateDeployment } from '../../hooks/useAgentDeployments';
import { useAgentRoster } from '../../hooks/useAgents';
import type { StrategyProfile } from '../../types/agentDeployment';

interface DeployAgentModalProps {
  open: boolean;
  onClose: () => void;
  preselectedAgentId?: string;
  preselectedTheatreId?: string;
}

interface TheatreOption {
  id: string;
  construct_id: string;
  state: string;
}

const STRATEGIES: Array<{
  id: StrategyProfile;
  label: string;
  description: string;
}> = [
  { id: 'AGGRESSIVE', label: 'Aggressive', description: 'High risk, high reward' },
  { id: 'BALANCED', label: 'Balanced', description: 'Default strategy' },
  { id: 'DEFENSIVE', label: 'Defensive', description: 'Capital preservation' },
];

function parseGuardError(error: unknown): string | null {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === 'string' && detail.toLowerCase().includes('guard') ? detail : null;
}

function ModalSelect({
  label,
  value,
  placeholder,
  options,
  open,
  onToggle,
  onSelect,
  disabled,
  locked,
  loading,
}: {
  label: string;
  value: string;
  placeholder: string;
  options: Array<{ value: string; label: string; sublabel?: string }>;
  open: boolean;
  onToggle: () => void;
  onSelect: (value: string) => void;
  disabled?: boolean;
  locked?: boolean;
  loading?: boolean;
}) {
  const selected = options.find((option) => option.value === value);

  return (
    <div>
      <label className="mb-2 block text-[11px] font-medium uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
        {label}
      </label>
      <div className="relative">
        <button
          type="button"
          onClick={onToggle}
          disabled={disabled || locked}
          className={clsx(
            'flex w-full items-center justify-between rounded-md border px-3 py-2.5 text-left text-[13px] transition',
            disabled
              ? 'cursor-not-allowed border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] text-[var(--e-text-disabled)] opacity-70'
              : locked
                ? 'cursor-default border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                : 'border-[var(--e-border-primary)] bg-[var(--e-bg-elevated)] text-[var(--e-text-primary)] hover:border-[var(--e-purple-200)]',
          )}
        >
          <span className={selected ? 'text-[var(--e-text-primary)]' : 'text-[var(--e-text-muted)]'}>
            {selected?.label ?? placeholder}
          </span>
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin text-[var(--e-text-muted)]" />
          ) : !locked && !disabled ? (
            <ChevronDown className={clsx('h-4 w-4 text-[var(--e-text-muted)] transition', open && 'rotate-180')} />
          ) : null}
        </button>

        {open && !disabled && !locked ? (
          <>
            <button
              type="button"
              aria-label={`Close ${label} dropdown`}
              onClick={onToggle}
              className="fixed inset-0 z-[319] cursor-default bg-transparent"
            />
            <div className="absolute top-full z-[320] mt-1 max-h-44 w-full overflow-y-auto rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] py-1 shadow-[var(--e-shadow-md)]">
              {options.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => onSelect(option.value)}
                  className={clsx(
                    'flex w-full items-center justify-between px-3 py-2 text-left text-[12px] transition hover:bg-[var(--e-bg-hover)]',
                    option.value === value ? 'text-[var(--e-purple-700)]' : 'text-[var(--e-text-primary)]',
                  )}
                >
                  <span>{option.label}</span>
                  {option.sublabel ? (
                    <span className="font-mono text-[10px] text-[var(--e-text-muted)]">{option.sublabel}</span>
                  ) : null}
                </button>
              ))}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

export function DeployAgentModal({
  open,
  onClose,
  preselectedAgentId,
  preselectedTheatreId,
}: DeployAgentModalProps) {
  const { agents, isLoading: agentsLoading } = useAgentRoster({ is_alive: true });
  const createDeployment = useCreateDeployment();

  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [selectedTheatreId, setSelectedTheatreId] = useState('');
  const [strategy, setStrategy] = useState<StrategyProfile>('BALANCED');
  const [theatres, setTheatres] = useState<TheatreOption[]>([]);
  const [theatresLoading, setTheatresLoading] = useState(false);
  const [theatresError, setTheatresError] = useState(false);
  const [agentDropdownOpen, setAgentDropdownOpen] = useState(false);
  const [theatreDropdownOpen, setTheatreDropdownOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    setSelectedAgentId(preselectedAgentId ?? '');
    setSelectedTheatreId(preselectedTheatreId ?? '');
    setStrategy('BALANCED');
    setAgentDropdownOpen(false);
    setTheatreDropdownOpen(false);
    createDeployment.reset();
  }, [createDeployment, open, preselectedAgentId, preselectedTheatreId]);

  useEffect(() => {
    if (!open) return;

    if (preselectedTheatreId) {
      setTheatres([]);
      setTheatresLoading(false);
      setTheatresError(false);
      return;
    }

    setTheatresLoading(true);
    setTheatresError(false);

    apiClient
      .get('/api/v1/theatres/')
      .then((response) => {
        const items = (response.data?.theatres ?? response.data ?? []) as TheatreOption[];
        setTheatres(items);
      })
      .catch(() => {
        setTheatres([]);
        setTheatresError(true);
      })
      .finally(() => setTheatresLoading(false));
  }, [open, preselectedTheatreId]);

  useEffect(() => {
    if (!open) return undefined;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId),
    [agents, selectedAgentId],
  );
  const selectedTheatre = useMemo(
    () => theatres.find((theatre) => theatre.id === selectedTheatreId),
    [selectedTheatreId, theatres],
  );

  const hasTheatreContext = Boolean(preselectedTheatreId);
  const canDeploy = Boolean(selectedAgentId && selectedTheatreId && !createDeployment.isPending);
  const guardError = createDeployment.isError ? parseGuardError(createDeployment.error) : null;

  const agentOptions = agents.map((agent) => ({
    value: agent.id,
    label: agent.name ?? agent.id,
    sublabel: agent.archetype,
  }));

  const theatreOptions = theatres.map((theatre) => ({
    value: theatre.id,
    label: theatre.construct_id ?? theatre.id,
    sublabel: theatre.state,
  }));

  const handleDeploy = () => {
    if (!canDeploy) return;

    createDeployment.mutate(
      {
        agent_id: selectedAgentId,
        theatre_id: selectedTheatreId,
        strategy_profile: strategy,
      },
      {
        onSuccess: () => {
          window.setTimeout(onClose, 1200);
        },
      },
    );
  };

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 z-[300] bg-[color:oklch(0.20_0.01_265_/_0.60)]" onClick={onClose} />
      <div className="fixed inset-0 z-[310] flex items-center justify-center p-4">
        <div className="w-full max-w-[560px] overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-md)]">
          <div className="flex items-center justify-between border-b border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)]">
                <Rocket className="h-5 w-5 text-[var(--e-purple-500)]" />
              </div>
              <div>
                <div className="text-[18px] font-bold tracking-[-0.01em] text-[var(--e-text-primary)]">
                  Deploy Agent
                </div>
                <div className="text-[12px] text-[var(--e-text-muted)]">
                  Assign agent to theatre with strategy
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
              aria-label="Close deploy agent modal"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex flex-col gap-5 p-6">
            {createDeployment.isSuccess ? (
              <div className="flex items-start gap-3 rounded-md border border-[color:oklch(0.545_0.170_152_/_0.30)] bg-[var(--e-green-50)] p-4">
                <CheckCircle2 className="mt-0.5 h-5 w-5 text-[var(--status-success)]" />
                <div>
                  <div className="text-[13px] font-semibold text-[var(--e-green-600)]">
                    Agent deployed
                  </div>
                  <div className="mt-1 text-[11px] text-[var(--e-text-muted)]">
                    Deployment ID <span className="font-mono">{createDeployment.data?.id}</span>
                  </div>
                </div>
              </div>
            ) : null}

            {guardError ? (
              <div className="flex items-start gap-3 rounded-md border border-[color:oklch(0.545_0.185_25_/_0.30)] bg-[var(--e-red-50)] p-4">
                <ShieldAlert className="mt-0.5 h-4 w-4 text-[var(--status-danger)]" />
                <div>
                  <div className="text-[12px] font-semibold text-[var(--e-red-600)]">
                    Deployment guard failure
                  </div>
                  <div className="mt-1 text-[11px] text-[var(--status-danger)]/80">{guardError}</div>
                </div>
              </div>
            ) : null}

            {createDeployment.isError && !guardError ? (
              <div className="flex items-start gap-3 rounded-md border border-[color:oklch(0.545_0.185_25_/_0.30)] bg-[var(--e-red-50)] p-4">
                <AlertCircle className="mt-0.5 h-4 w-4 text-[var(--status-danger)]" />
                <div className="text-[12px] text-[var(--e-red-600)]">
                  {(createDeployment.error as Error)?.message ?? 'Deployment failed'}
                </div>
              </div>
            ) : null}

            {!hasTheatreContext && theatresError && !theatresLoading ? (
              <div className="flex items-start gap-3 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] p-4">
                <Info className="mt-0.5 h-4 w-4 text-[var(--e-text-muted)]" />
                <div>
                  <div className="text-[12px] font-semibold text-[var(--e-text-primary)]">
                    Theatre selection unavailable
                  </div>
                  <div className="mt-1 text-[11px] leading-5 text-[var(--e-text-muted)]">
                    The theatre list API does not exist yet. Deploy from a theatre detail page where the theatre context is already known.
                  </div>
                </div>
              </div>
            ) : null}

            <ModalSelect
              label="Agent"
              value={selectedAgentId}
              placeholder={agentsLoading ? 'Loading agents…' : 'Select agent'}
              options={agentOptions}
              open={agentDropdownOpen}
              onToggle={() => setAgentDropdownOpen((state) => !state)}
              onSelect={(value) => {
                setSelectedAgentId(value);
                setAgentDropdownOpen(false);
              }}
              disabled={agentsLoading || agentOptions.length === 0}
              loading={agentsLoading}
            />

            <ModalSelect
              label="Theatre"
              value={selectedTheatreId}
              placeholder={
                hasTheatreContext
                  ? `Theatre: ${selectedTheatreId.slice(0, 12)}`
                  : theatresLoading
                    ? 'Loading theatres…'
                    : 'No list endpoint available'
              }
              options={theatreOptions}
              open={theatreDropdownOpen}
              onToggle={() => setTheatreDropdownOpen((state) => !state)}
              onSelect={(value) => {
                setSelectedTheatreId(value);
                setTheatreDropdownOpen(false);
              }}
              disabled={(!hasTheatreContext && theatreOptions.length === 0) || theatresLoading}
              locked={hasTheatreContext}
              loading={theatresLoading && !hasTheatreContext}
            />

            <div>
              <label className="mb-2 block text-[11px] font-medium uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                Strategy Profile
              </label>
              <div className="flex gap-2">
                {STRATEGIES.map((option) => {
                  const active = strategy === option.id;
                  return (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => setStrategy(option.id)}
                      className={clsx(
                        'flex-1 rounded-md border p-3 text-left transition',
                        active
                          ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)]'
                          : 'border-[var(--e-border-primary)] bg-[var(--e-bg-elevated)] hover:border-[var(--e-purple-200)]',
                      )}
                    >
                      <div
                        className={clsx(
                          'text-[12px] font-semibold',
                          active ? 'text-[var(--e-purple-700)]' : 'text-[var(--e-text-primary)]',
                        )}
                      >
                        {option.label}
                      </div>
                      <div
                        className={clsx(
                          'mt-1 text-[10px]',
                          active ? 'text-[var(--e-purple-400)]' : 'text-[var(--e-text-muted)]',
                        )}
                      >
                        {option.description}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {selectedAgent ? (
              <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-[12px] text-[var(--e-text-secondary)]">
                Deploying <span className="font-semibold text-[var(--e-text-primary)]">{selectedAgent.name}</span>
                {selectedTheatre ? (
                  <>
                    {' '}
                    into <span className="font-semibold text-[var(--e-text-primary)]">{selectedTheatre.construct_id}</span>
                  </>
                ) : hasTheatreContext ? (
                  <>
                    {' '}
                    into <span className="font-semibold text-[var(--e-text-primary)]">{selectedTheatreId.slice(0, 12)}</span>
                  </>
                ) : null}
                .
              </div>
            ) : null}
          </div>

          <div className="flex gap-3 border-t border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] p-5">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-md bg-[var(--e-bg-hover)] px-4 py-3 text-[13px] font-semibold text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-active)] hover:text-[var(--e-text-primary)]"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDeploy}
              disabled={!canDeploy}
              className={clsx(
                'flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-3 text-[13px] font-semibold transition',
                canDeploy
                  ? 'bg-[var(--e-purple-500)] text-[var(--e-text-inverse)] hover:bg-[var(--e-purple-600)]'
                  : 'cursor-not-allowed bg-[var(--e-purple-200)] text-[var(--e-text-disabled)]',
              )}
            >
              {createDeployment.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
              {createDeployment.isPending ? 'Deploying…' : 'Deploy'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default DeployAgentModal;
