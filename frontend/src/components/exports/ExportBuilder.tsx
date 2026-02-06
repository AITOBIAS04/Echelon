import { useState } from 'react';
import type { ExportScope, ExportFilter, ExportDatasetKind } from '../../types/exports';

/**
 * ExportBuilder Props
 */
export interface ExportBuilderProps {
  /** Callback when export job is created */
  onCreateJob: (input: { scope: ExportScope; filter: ExportFilter }) => Promise<void>;
  /** Loading state */
  loading?: boolean;
}

/**
 * ExportBuilder Component
 * 
 * Form for creating new export jobs with dataset kind, scope, and filters.
 */
export function ExportBuilder({ onCreateJob, loading = false }: ExportBuilderProps) {
  const [kind, setKind] = useState<ExportDatasetKind>('rlmf');
  const [scope, setScope] = useState<'my' | 'workspace' | 'global'>('my');
  const [paradoxOnly, setParadoxOnly] = useState(false);
  const [oodOnly, setOodOnly] = useState(false);
  const [minForkCount, setMinForkCount] = useState<number | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      const filter: ExportFilter = {
        kind,
        ...(paradoxOnly && { paradoxOnly: true }),
        ...(oodOnly && { oodOnly: true }),
        ...(minForkCount !== undefined && minForkCount > 0 && { minForkCount }),
      };

      const exportScope: ExportScope = {
        scope,
      };

      await onCreateJob({ scope: exportScope, filter });
      
      // Reset form after successful creation
      setParadoxOnly(false);
      setOodOnly(false);
      setMinForkCount(undefined);
    } catch (error) {
      // Error handling is done by parent component
      console.error('Failed to create export job:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-terminal-panel rounded-lg border border-terminal-border p-4">
      <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-4">
        Create Export Job
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Dataset Kind */}
        <div>
          <label className="block text-xs text-terminal-text-muted mb-2 uppercase">
            Dataset Kind
          </label>
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as ExportDatasetKind)}
            className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
            disabled={isSubmitting || loading}
          >
            <option value="rlmf">RLMF</option>
            <option value="human_judgement">Human Judgement</option>
            <option value="audit_trace">Audit Trace</option>
          </select>
        </div>

        {/* Scope */}
        <div>
          <label className="block text-xs text-terminal-text-muted mb-2 uppercase">
            Scope
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as 'my' | 'workspace' | 'global')}
            className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
            disabled={isSubmitting || loading}
          >
            <option value="my">My</option>
            <option value="workspace">Workspace</option>
            <option value="global">Global</option>
          </select>
        </div>

        {/* Filters */}
        <div className="space-y-3">
          <label className="block text-xs text-terminal-text-muted mb-2 uppercase">
            Filters
          </label>

          {/* Paradox Only Toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={paradoxOnly}
              onChange={(e) => setParadoxOnly(e.target.checked)}
              disabled={isSubmitting || loading}
              className="w-4 h-4 rounded border-terminal-border bg-terminal-bg text-echelon-cyan focus:ring-echelon-cyan focus:ring-offset-0"
            />
            <span className="text-sm text-terminal-text">Paradox Only</span>
          </label>

          {/* OOD Only Toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={oodOnly}
              onChange={(e) => setOodOnly(e.target.checked)}
              disabled={isSubmitting || loading}
              className="w-4 h-4 rounded border-terminal-border bg-terminal-bg text-echelon-cyan focus:ring-echelon-cyan focus:ring-offset-0"
            />
            <span className="text-sm text-terminal-text">Out-of-Distribution Only</span>
          </label>

          {/* Min Fork Count */}
          <div>
            <label className="block text-xs text-terminal-text-muted mb-1">
              Min Fork Count (optional)
            </label>
            <input
              type="number"
              min="0"
              value={minForkCount || ''}
              onChange={(e) => {
                const value = e.target.value;
                setMinForkCount(value === '' ? undefined : parseInt(value, 10));
              }}
              placeholder="0"
              className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
              disabled={isSubmitting || loading}
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting || loading}
          className="w-full px-4 py-2 bg-echelon-cyan/20 border border-echelon-cyan rounded text-sm font-semibold text-echelon-cyan hover:bg-echelon-cyan/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting || loading ? 'Creating...' : 'CREATE EXPORT JOB'}
        </button>
      </form>
    </div>
  );
}
