import { clsx } from 'clsx';
import type { CounterSignal } from '../../types/investigation';

const SIGNAL_STYLES: Record<string, string> = {
  official_denial: 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]',
  regulatory_clearance: 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]',
  filing_contradiction: 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]',
  competing_analysis: 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]',
};

function SignalCard({ signal }: { signal: CounterSignal }) {
  return (
    <div
      className={clsx(
        'rounded-lg border bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]',
        signal.material
          ? 'border-[color:oklch(0.545_0.185_25_/_0.18)]'
          : 'border-[var(--e-border-primary)]',
      )}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{signal.counter_signal_id}</span>
          <span
            className={clsx(
              'rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
              SIGNAL_STYLES[signal.signal_class] ??
                'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
            )}
          >
            {signal.signal_class.replace(/_/g, ' ')}
          </span>
          {signal.material ? (
            <span className="rounded-full border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-red-600)]">
              Material
            </span>
          ) : null}
        </div>
        <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
          {new Date(signal.detected_at).toLocaleString()}
        </span>
      </div>

      {signal.resolution_impact ? (
        <div className="mb-2 text-[13px] leading-6 text-[var(--e-text-primary)]">{signal.resolution_impact}</div>
      ) : null}

      <div className="flex flex-wrap items-center gap-3 text-[12px] text-[var(--e-text-secondary)]">
        <span>Method {signal.detection_method}</span>
        {signal.evidence_ref ? (
          <span className="font-mono text-[var(--e-purple-700)]">{signal.evidence_ref}</span>
        ) : null}
      </div>
    </div>
  );
}

export function CounterSignalPanel({
  signals,
  summary,
}: {
  signals: CounterSignal[];
  summary: Record<string, number>;
}) {
  if (signals.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">
        No counter-signals detected.
      </div>
    );
  }

  const materialCount = signals.filter((signal) => signal.material).length;

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
        <div className="mb-2 flex flex-wrap items-center gap-4 text-[13px]">
          <div>
            <span className="text-[var(--e-text-muted)]">Total </span>
            <span className="font-mono text-[var(--e-text-primary)]">{signals.length}</span>
          </div>
          <div>
            <span className="text-[var(--e-text-muted)]">Material </span>
            <span className={clsx('font-mono', materialCount > 0 ? 'text-[var(--e-red-600)]' : 'text-[var(--e-text-primary)]')}>
              {materialCount}
            </span>
          </div>
        </div>
        {Object.keys(summary).length > 0 ? (
          <div className="flex flex-wrap gap-3 text-[11px] text-[var(--e-text-muted)]">
            {Object.entries(summary).map(([key, count]) => (
              <span key={key}>
                {key}: {count}
              </span>
            ))}
          </div>
        ) : null}
      </div>

      <div className="space-y-3">
        {signals.map((signal) => (
          <SignalCard key={signal.counter_signal_id} signal={signal} />
        ))}
      </div>
    </div>
  );
}

export default CounterSignalPanel;
