import type { ExportJob, ExportDatasetKind } from '../../types/exports';

/**
 * ExportJobTable Props
 */
export interface ExportJobTableProps {
  /** Array of export jobs to display */
  jobs: ExportJob[];
  /** Callback when a completed job is clicked */
  onJobClick?: (kind: ExportDatasetKind) => void;
}

/**
 * Format timestamp to relative time or date
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);

  if (diffHours < 1) {
    const diffMins = Math.floor(diffMs / (1000 * 60));
    return `${diffMins}m ago`;
  }
  if (diffHours < 24) {
    return `${Math.floor(diffHours)}h ago`;
  }
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

/**
 * Get status badge color
 */
function getStatusColor(status: ExportJob['status']): string {
  switch (status) {
    case 'completed':
      return '#00FF41'; // green
    case 'running':
      return '#00D4FF'; // cyan
    case 'queued':
      return '#FF9500'; // amber
    case 'failed':
      return '#FF3B3B'; // red
  }
}

/**
 * Shorten job ID for display
 */
function shortenJobId(id: string): string {
  if (id.length <= 16) return id;
  return `${id.substring(0, 8)}...${id.substring(id.length - 4)}`;
}

/**
 * ExportJobTable Component
 * 
 * Displays export jobs in a table format with status badges and metadata.
 */
export function ExportJobTable({ jobs, onJobClick }: ExportJobTableProps) {
  const handleRowClick = (job: ExportJob) => {
    if (job.status === 'completed' && onJobClick) {
      onJobClick(job.kind);
    }
  };

  if (jobs.length === 0) {
    return (
      <div className="bg-[#111111] rounded-lg border border-[#1A1A1A] p-4">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-4">
          Export Jobs
        </h3>
        <p className="text-sm text-terminal-muted text-center py-8">
          No export jobs yet. Create one to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-[#111111] rounded-lg border border-[#1A1A1A] p-4">
      <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-4">
        Export Jobs
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#1A1A1A]">
              <th className="text-left py-2 text-terminal-muted font-semibold text-xs uppercase">
                ID
              </th>
              <th className="text-left py-2 text-terminal-muted font-semibold text-xs uppercase">
                Kind
              </th>
              <th className="text-left py-2 text-terminal-muted font-semibold text-xs uppercase">
                Status
              </th>
              <th className="text-left py-2 text-terminal-muted font-semibold text-xs uppercase">
                Created
              </th>
              <th className="text-left py-2 text-terminal-muted font-semibold text-xs uppercase">
                Rows
              </th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => {
              const statusColor = getStatusColor(job.status);
              const isCompleted = job.status === 'completed';
              const isClickable = isCompleted && onJobClick;

              return (
                <tr
                  key={job.id}
                  onClick={() => handleRowClick(job)}
                  className={`
                    border-b border-[#1A1A1A] transition-colors
                    ${isClickable ? 'cursor-pointer hover:bg-terminal-panel/50' : ''}
                  `}
                >
                  <td className="py-2 text-terminal-text font-mono text-xs">
                    {shortenJobId(job.id)}
                  </td>
                  <td className="py-2 text-terminal-text capitalize">
                    {job.kind.replace('_', ' ')}
                  </td>
                  <td className="py-2">
                    <span
                      className="px-2 py-0.5 rounded text-xs font-semibold uppercase"
                      style={{
                        backgroundColor: `${statusColor}20`,
                        color: statusColor,
                        border: `1px solid ${statusColor}`,
                      }}
                    >
                      {job.status}
                    </span>
                  </td>
                  <td className="py-2 text-terminal-muted text-xs">
                    {formatTimestamp(job.createdAt)}
                  </td>
                  <td className="py-2 text-terminal-text text-xs">
                    {job.rowCount ? job.rowCount.toLocaleString() : '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
