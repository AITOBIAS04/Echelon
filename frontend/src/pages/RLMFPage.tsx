/**
 * RLMF Page — Export Viewer
 *
 * Shows RLMF export status per Theatre, export job list,
 * sample records, and download capability.
 * Uses real useExports hook — no demo/mock data.
 */

import { useExports } from '../hooks/useExports';
import type { ExportJob, ExportDatasetKind } from '../types/exports';

const KIND_LABELS: Record<ExportDatasetKind, string> = {
  rlmf: 'RLMF Training Data',
  human_judgement: 'Human Judgement',
  audit_trace: 'Audit Trace',
};

const STATUS_STYLES: Record<ExportJob['status'], string> = {
  queued: 'bg-zinc-500/20 text-zinc-400',
  running: 'bg-amber-500/20 text-amber-400',
  completed: 'bg-emerald-500/20 text-emerald-400',
  failed: 'bg-red-500/20 text-red-400',
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function ExportJobCard({ job }: { job: ExportJob }) {
  return (
    <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-terminal-text">
          {KIND_LABELS[job.kind]}
        </span>
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${STATUS_STYLES[job.status]}`}
        >
          {job.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[10px] text-terminal-text-muted">
        <div>
          <span className="uppercase tracking-wider">Created</span>
          <div className="font-mono text-terminal-text mt-0.5">
            {new Date(job.createdAt).toLocaleString()}
          </div>
        </div>
        {job.completedAt && (
          <div>
            <span className="uppercase tracking-wider">Completed</span>
            <div className="font-mono text-terminal-text mt-0.5">
              {new Date(job.completedAt).toLocaleString()}
            </div>
          </div>
        )}
        {job.rowCount !== undefined && (
          <div>
            <span className="uppercase tracking-wider">Rows</span>
            <div className="font-mono text-terminal-text mt-0.5">
              {job.rowCount.toLocaleString()}
            </div>
          </div>
        )}
        {job.byteSize !== undefined && (
          <div>
            <span className="uppercase tracking-wider">Size</span>
            <div className="font-mono text-terminal-text mt-0.5">
              {formatBytes(job.byteSize)}
            </div>
          </div>
        )}
      </div>

      {job.error && (
        <div className="mt-2 text-[10px] text-status-danger">{job.error}</div>
      )}

      <div className="mt-2 text-[10px] font-mono text-terminal-text-muted">
        Scope: {job.scope.scope} · Filter: {job.filter.kind}
        {job.filter.seedTier ? ` · Tier: ${job.filter.seedTier}` : ''}
      </div>
    </div>
  );
}

export function RLMFPage() {
  const { jobs, loading, error, previews, loadPreview } = useExports();

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
          RLMF Export Viewer
        </h2>
        <p className="text-xs text-terminal-text-muted mt-1">
          Export training data, human judgements, and audit traces from the prediction market pipeline.
        </p>
      </div>

      {/* Dataset Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {(['rlmf', 'human_judgement', 'audit_trace'] as ExportDatasetKind[]).map(
          (kind) => {
            const preview = previews[kind];
            const kindJobs = jobs.filter((j) => j.kind === kind);
            const completed = kindJobs.filter((j) => j.status === 'completed');

            return (
              <div
                key={kind}
                className="bg-terminal-panel border border-terminal-border rounded-xl p-4"
              >
                <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
                  {KIND_LABELS[kind]}
                </div>
                <div className="text-lg font-mono font-bold text-terminal-text">
                  {completed.length}
                </div>
                <div className="text-xs text-terminal-text-muted">
                  completed exports
                </div>
                {!preview && (
                  <button
                    onClick={() => loadPreview(kind)}
                    className="mt-3 w-full text-[10px] text-echelon-cyan hover:text-echelon-cyan/80 border border-echelon-cyan/20 hover:border-echelon-cyan/40 rounded py-1.5 transition-colors"
                  >
                    Preview Schema
                  </button>
                )}
                {preview && (
                  <div className="mt-3 text-[10px] text-terminal-text-muted">
                    Schema v{preview.schemaVersion} · {preview.fields.length} fields ·{' '}
                    {preview.sampleRows.length} samples
                  </div>
                )}
              </div>
            );
          },
        )}
      </div>

      {/* Export Jobs */}
      <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
        <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex items-center justify-between">
          <span className="text-xs font-semibold text-terminal-text uppercase tracking-wider">
            Export Jobs
          </span>
          <span className="text-[10px] text-terminal-text-muted font-mono">
            {jobs.length} total
          </span>
        </div>

        <div className="p-4">
          {loading ? (
            <div className="text-xs text-terminal-text-muted text-center py-4">
              Loading exports...
            </div>
          ) : error ? (
            <div className="text-xs text-status-danger text-center py-4">
              {error}
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-xs text-terminal-text-muted text-center py-8">
              No export jobs found. Use the API to create exports.
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <ExportJobCard key={job.id} job={job} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Schema Preview */}
      {Object.entries(previews).map(([kind, preview]) => {
        if (!preview) return null;
        return (
          <div
            key={kind}
            className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden"
          >
            <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
              <span className="text-xs font-semibold text-terminal-text uppercase tracking-wider">
                {KIND_LABELS[kind as ExportDatasetKind]} — Schema Preview
              </span>
            </div>
            <div className="p-4">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-terminal-border">
                      <th className="text-left px-3 py-2 text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold">
                        Field
                      </th>
                      <th className="text-left px-3 py-2 text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold">
                        Type
                      </th>
                      <th className="text-left px-3 py-2 text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold">
                        Description
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.fields.map((field) => (
                      <tr
                        key={field.name}
                        className="border-b border-terminal-border/50"
                      >
                        <td className="px-3 py-2 font-mono text-echelon-cyan">
                          {field.name}
                        </td>
                        <td className="px-3 py-2 font-mono text-terminal-text-muted">
                          {field.type}
                        </td>
                        <td className="px-3 py-2 text-terminal-text-secondary">
                          {field.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {preview.sampleRows.length > 0 && (
                <div className="mt-4">
                  <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
                    Sample Record
                  </div>
                  <pre className="bg-terminal-bg border border-terminal-border rounded-lg p-3 text-[10px] font-mono text-terminal-text overflow-x-auto">
                    {JSON.stringify(preview.sampleRows[0], null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
