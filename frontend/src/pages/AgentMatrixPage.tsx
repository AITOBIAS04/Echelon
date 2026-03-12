import { useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { AlertTriangle, CheckCircle, Grid3X3 } from 'lucide-react';
import { useAgentMatrix } from '../hooks/useAgentMatrix';
import { MatrixKPICards } from '../components/matrix/MatrixKPICards';
import { MatrixTable } from '../components/matrix/MatrixTable';
import { MatrixSidebar } from '../components/matrix/MatrixSidebar';
import { EmptyState } from '../components/empty-states/EmptyState';

export function AgentMatrixPage() {
  const navigate = useNavigate();
  const { rows, kpis, pageState, alertSummary, strategyDistribution, isLoading, error } =
    useAgentMatrix();

  // ── Loading skeleton ──────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          <div>
            <div className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
              Fleet
            </div>
            <h1 className="text-[28px] font-bold tracking-[-0.02em] text-[var(--e-text-primary)]">
              Deployments
            </h1>
          </div>
          <div className="flex flex-wrap gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-[76px] flex-1 min-w-[140px] animate-pulse rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)]"
              />
            ))}
          </div>
          <div className="h-64 animate-pulse rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)]" />
        </div>
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────────────────
  if (error) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-lg border border-[oklch(0.545_0.185_25_/_0.2)] bg-[var(--e-red-50)] p-6 text-center">
            <p className="text-[14px] font-medium text-[var(--status-danger)]">
              Failed to load deployment data
            </p>
            <p className="mt-1 text-[12px] text-[var(--e-text-muted)]">
              Check your connection and try refreshing.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── Empty state ───────────────────────────────────────────────────
  if (pageState === 'EMPTY') {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          <div>
            <div className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
              Fleet
            </div>
            <h1 className="text-[28px] font-bold tracking-[-0.02em] text-[var(--e-text-primary)]">
              Deployments
            </h1>
            <p className="mt-1 max-w-2xl text-[15px] leading-6 text-[var(--e-text-secondary)]">
              Cross-theatre deployment view — every active agent-to-theatre assignment in one grid.
            </p>
          </div>
          <EmptyState
            type="ZERO_STATE"
            icon={<Grid3X3 className="h-6 w-6" />}
            title="No agents deployed yet"
            description="Deploy an agent from Fleet or a Theatre detail page. The matrix will visualize cross-theatre positions here."
            actions={[
              { label: 'Go to Fleet', onClick: () => navigate('/fleet'), variant: 'primary' },
            ]}
          />
        </div>
      </div>
    );
  }

  // ── Nominal / Alert states ────────────────────────────────────────
  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-5">
        {/* Header */}
        <div>
          <div className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
            Operations
          </div>
          <h1 className="text-[28px] font-bold tracking-[-0.02em] text-[var(--e-text-primary)]">
            Agent Matrix
          </h1>
          <p className="mt-1 max-w-2xl text-[15px] leading-6 text-[var(--e-text-secondary)]">
            Cross-theatre deployment view — every active agent-to-theatre assignment in one grid.
          </p>
        </div>

        {/* Attention strip */}
        {pageState === 'NOMINAL' ? (
          <div className="flex items-center gap-3 rounded-md border border-[oklch(0.545_0.170_152_/_0.18)] bg-[oklch(0.545_0.170_152_/_0.06)] px-5 py-3 text-[13px]">
            <CheckCircle className="h-4 w-4 text-[var(--e-green-600)]" />
            <span className="font-semibold text-[var(--e-green-700)]">
              All deployments operating normally
            </span>
          </div>
        ) : (
          <div
            className={clsx(
              'flex items-center gap-3 rounded-md border px-5 py-3 text-[13px]',
              'border-[oklch(0.545_0.185_25_/_0.18)] bg-[oklch(0.545_0.185_25_/_0.06)]',
            )}
          >
            <AlertTriangle className="h-4 w-4 text-[var(--status-danger)]" />
            <span className="font-semibold text-[var(--status-danger)]">{alertSummary}</span>
          </div>
        )}

        {/* KPI cards */}
        <MatrixKPICards kpis={kpis} />

        {/* Main content: table + sidebar */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_280px]">
          <MatrixTable rows={rows} />
          <MatrixSidebar rows={rows} strategyDistribution={strategyDistribution} />
        </div>
      </div>
    </div>
  );
}
