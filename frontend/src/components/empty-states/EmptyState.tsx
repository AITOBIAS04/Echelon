/**
 * EmptyState — Shared empty state component system for Echelon.
 *
 * 6 state types, one anatomy, adapted by copy and tone across 13+ surfaces.
 *
 * Types:
 *   ZERO_STATE      — nothing created yet (onboarding)
 *   ALL_CLEAR       — system active, nothing needs intervention (success)
 *   QUIET_MONITORING — watching, low activity (subdued awareness)
 *   SPARSE_DATA     — some activity, not enough for analytics (patience)
 *   NO_RESULTS      — filters returned nothing (compact inline)
 *   NOT_YET_GENERATED — upstream dependency hasn't run (explanatory)
 *
 * Design ref: echelon_empty_states_v1.html (Alexander)
 */

import { type ReactNode } from 'react';
import { clsx } from 'clsx';

// ── Types ───────────────────────────────────────────────────────────────

export type EmptyStateType =
  | 'ZERO_STATE'
  | 'ALL_CLEAR'
  | 'QUIET_MONITORING'
  | 'SPARSE_DATA'
  | 'NO_RESULTS'
  | 'NOT_YET_GENERATED';

export interface EmptyStateAction {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

export interface EmptyStateProps {
  type: EmptyStateType;

  /** Page's own icon — reuse nav icon, not novelty art */
  icon?: ReactNode;

  /** Short declarative title. 2-5 words. Describes state, not page. */
  title?: string;

  /** One sentence explaining what produces content here. */
  description?: string;

  /** Primary + optional secondary action */
  actions?: EmptyStateAction[];

  /**
   * Context slot — varies by type:
   * - ALL_CLEAR: status text + timestamp
   * - QUIET_MONITORING: skeleton content behind overlay
   * - SPARSE_DATA: chart placeholder content
   * - NOT_YET_GENERATED: trigger explanation text
   */
  context?: ReactNode;

  /** Additional className on the wrapper */
  className?: string;

  /** For ALL_CLEAR: the "last checked" or "since" timestamp */
  timestamp?: string;

  /** For ALL_CLEAR: list of recently resolved items */
  recentItems?: Array<{ label: string; time?: string }>;

  /** For NO_RESULTS: the active filter description */
  filterDescription?: string;

  /** For NO_RESULTS: clear filters handler */
  onClearFilters?: () => void;

  /** For NOT_YET_GENERATED: what triggers generation */
  triggerText?: string;
}

// ── Main Component ──────────────────────────────────────────────────────

export function EmptyState(props: EmptyStateProps) {
  switch (props.type) {
    case 'ZERO_STATE':
      return <ZeroState {...props} />;
    case 'ALL_CLEAR':
      return <AllClear {...props} />;
    case 'QUIET_MONITORING':
      return <QuietMonitoring {...props} />;
    case 'SPARSE_DATA':
      return <SparseData {...props} />;
    case 'NO_RESULTS':
      return <NoResults {...props} />;
    case 'NOT_YET_GENERATED':
      return <NotYetGenerated {...props} />;
    default:
      return null;
  }
}

// ── Shared Button ───────────────────────────────────────────────────────

function ActionButton({ label, onClick, variant = 'primary' }: EmptyStateAction) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'inline-flex items-center justify-center gap-1.5 h-9 px-4 rounded-lg',
        'font-sans text-[13px] font-semibold whitespace-nowrap',
        'transition-all duration-150 ease-out active:scale-[0.97]',
        variant === 'primary' && [
          'border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] text-[var(--e-text-inverse)]',
          'hover:bg-[var(--e-purple-400)]',
        ],
        variant === 'secondary' && [
          'border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)]',
          'hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
        ],
      )}
    >
      {label}
    </button>
  );
}

// ── 1. ZERO STATE — centered icon + title + desc + CTA ──────────────────

function ZeroState({ icon, title, description, actions, className }: EmptyStateProps) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center text-center',
        'min-h-[280px] rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-12 shadow-[var(--e-shadow-xs)]',
        className,
      )}
    >
      {icon && (
        <div
          className={clsx(
            'w-14 h-14 flex items-center justify-center',
            'rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)] mb-5',
          )}
        >
          {icon}
        </div>
      )}
      {title && (
        <h3 className="mb-2 text-[17px] font-bold text-[var(--e-text-primary)]">{title}</h3>
      )}
      {description && (
        <p className="mb-6 max-w-[400px] text-sm leading-relaxed text-[var(--e-text-secondary)]">
          {description}
        </p>
      )}
      {actions && actions.length > 0 && (
        <div className="flex gap-3 justify-center">
          {actions.map((action) => (
            <ActionButton key={action.label} {...action} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── 2. ALL CLEAR — green status strip + recent resolved ─────────────────

function AllClear({
  description,
  timestamp,
  recentItems,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={clsx(
        'min-h-[160px] rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-5 shadow-[var(--e-shadow-xs)]',
        className,
      )}
    >
      {/* Status strip */}
      <div
        className={clsx(
          'flex items-center gap-3 px-4 py-3 rounded-lg mb-5',
          'bg-status-success/[0.06] border border-status-success/[0.15]',
        )}
      >
        <span
          className={clsx(
            'w-2.5 h-2.5 rounded-full bg-status-success flex-shrink-0',
            'shadow-[0_0_0_3px_rgba(74,222,128,0.15)]',
          )}
        />
        <span className="text-sm font-semibold text-status-success">All Clear</span>
        {timestamp && (
          <span className="ml-auto font-mono text-[11px] font-medium text-[var(--e-text-muted)]">
            {timestamp}
          </span>
        )}
      </div>

      {/* Message */}
      {description && (
        <p className="mb-4 text-[13px] leading-5 text-[var(--e-text-secondary)]">
          {description}
        </p>
      )}

      {/* Recently resolved */}
      {recentItems && recentItems.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--e-text-muted)]">
            Recently Resolved
          </div>
          {recentItems.map((item) => (
            <div
              key={item.label}
              className="flex items-center gap-2 py-1 text-xs text-[var(--e-text-muted)]"
            >
              <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[var(--e-border-secondary)]" />
              <span>{item.label}</span>
              {item.time && (
                <span className="ml-auto font-mono text-[10px]">{item.time}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── 3. QUIET MONITORING — skeleton + overlay badge ──────────────────────

function QuietMonitoring({ description, context, className }: EmptyStateProps) {
  return (
    <div
      className={clsx(
        'relative min-h-[280px] overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]',
        className,
      )}
    >
      {/* Skeleton layer at 0.25 opacity */}
      {context && (
        <div className="opacity-25 absolute inset-0">{context}</div>
      )}

      {/* Overlay badge + message */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-[280px] p-6">
        <div
          className={clsx(
            'inline-flex items-center gap-1.5 px-4 py-2 rounded-lg mb-3',
            'bg-status-info/[0.08] border border-status-info/[0.18]',
            'text-xs font-semibold text-status-info',
          )}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-status-info animate-pulse-slow" />
          Monitoring
        </div>
        {description && (
          <p className="max-w-[320px] text-center text-[13px] leading-5 text-[var(--e-text-secondary)]">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}

// ── 4. SPARSE DATA — chart shells + note ────────────────────────────────

function SparseData({ description, context, className }: EmptyStateProps) {
  return (
    <div
      className={clsx(
        'min-h-[200px] rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-5 shadow-[var(--e-shadow-xs)]',
        className,
      )}
    >
      {/* Chart placeholders */}
      {context ? (
        <div className="mb-5">{context}</div>
      ) : (
        <SparseDataDefaultCharts />
      )}

      {/* Explanatory note */}
      {description && (
        <div
          className={clsx(
            'flex items-start gap-3 p-3 rounded',
            'border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)]',
          )}
        >
          <svg
            className="mt-0.5 h-4 w-4 flex-shrink-0 text-[var(--e-text-muted)]"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <circle cx="8" cy="8" r="6" />
            <path d="M8 5.5v3M8 10.5v.01" />
          </svg>
          <span className="text-xs leading-[18px] text-[var(--e-text-muted)]">
            {description}
          </span>
        </div>
      )}
    </div>
  );
}

/** Default chart shells when no custom context is provided */
function SparseDataDefaultCharts() {
  return (
    <div className="grid grid-cols-2 gap-4 mb-5">
      {['Volume', 'Activity'].map((label) => (
        <div
          key={label}
          className={clsx(
            'min-h-[100px] rounded border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] p-4',
            'flex flex-col',
          )}
        >
          <div className="mb-3 text-[10px] font-bold uppercase tracking-wider text-[var(--e-text-muted)]">
            {label}
          </div>
          <div className="flex-1 flex items-end gap-1 pt-2">
            {[0.2, 0.35, 0.15, 0.5, 0.25, 0.1, 0.4].map((h, i) => (
              <div
                key={i}
                className="min-h-[4px] w-full rounded-t bg-[var(--e-border-secondary)]"
                style={{ height: `${h * 60}px` }}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── 5. NO RESULTS — compact inline ──────────────────────────────────────

function NoResults({
  filterDescription,
  onClearFilters,
  description,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={clsx(
        'flex items-center justify-center gap-4 px-4 py-6',
        'min-h-[80px] rounded border border-[var(--e-border-primary)] bg-[var(--e-bg-card)]',
        className,
      )}
    >
      <p className="text-[13px] text-[var(--e-text-muted)]">
        {filterDescription ? (
          <>
            No results for{' '}
            <strong className="font-semibold text-[var(--e-text-secondary)]">
              {filterDescription}
            </strong>
          </>
        ) : (
          description ?? 'No results match your current filters.'
        )}
      </p>
      {onClearFilters && (
        <button
          onClick={onClearFilters}
          className={clsx(
            'inline-flex items-center gap-1 px-3 py-1',
            'text-xs font-semibold rounded',
            'border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)]',
            'hover:border-[var(--e-purple-200)] hover:bg-[var(--e-purple-50)] hover:text-[var(--e-purple-700)]',
            'transition-colors duration-150',
          )}
        >
          Clear Filters
        </button>
      )}
    </div>
  );
}

// ── 6. NOT YET GENERATED — dependency explanation ───────────────────────

function NotYetGenerated({
  icon,
  title,
  description,
  triggerText,
  actions,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center text-center',
        'min-h-[240px] rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-10 shadow-[var(--e-shadow-xs)]',
        className,
      )}
    >
      {icon && (
        <div
          className={clsx(
            'w-12 h-12 flex items-center justify-center',
            'rounded-xl border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)] mb-4',
          )}
        >
          {icon}
        </div>
      )}
      {title && (
        <h3 className="mb-2 text-base font-bold text-[var(--e-text-primary)]">{title}</h3>
      )}
      {description && (
        <p className="mb-2 max-w-[380px] text-[13px] leading-5 text-[var(--e-text-secondary)]">
          {description}
        </p>
      )}
      {triggerText && (
        <p className="mb-5 text-xs italic text-[var(--e-text-muted)]">{triggerText}</p>
      )}
      {actions && actions.length > 0 && (
        <div className="flex gap-3">
          {actions.map((action) => (
            <ActionButton key={action.label} {...action} />
          ))}
        </div>
      )}
    </div>
  );
}
