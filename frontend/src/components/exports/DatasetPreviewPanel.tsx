import type { DatasetPreview } from '../../types/exports';

/**
 * DatasetPreviewPanel Props
 */
export interface DatasetPreviewPanelProps {
  /** Dataset preview to display */
  preview: DatasetPreview | undefined;
}

/**
 * Truncate long values for display
 */
function truncateValue(value: any, maxLength: number = 50): string {
  if (value === null || value === undefined) {
    return '-';
  }
  
  const str = typeof value === 'object' ? JSON.stringify(value) : String(value);
  
  if (str.length <= maxLength) {
    return str;
  }
  
  return `${str.substring(0, maxLength)}...`;
}

/**
 * Format field type for display
 */
function formatFieldType(type: string): string {
  return type.toUpperCase();
}

/**
 * DatasetPreviewPanel Component
 * 
 * Displays dataset schema and sample rows in a preview format.
 */
export function DatasetPreviewPanel({ preview }: DatasetPreviewPanelProps) {
  if (!preview) {
    return (
      <div className="bg-[#111111] rounded-lg border border-[#1A1A1A] p-4 h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-terminal-muted mb-2">
            No dataset preview selected
          </p>
          <p className="text-xs text-terminal-muted">
            Click a completed export job to view its dataset preview
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#111111] rounded-lg border border-[#1A1A1A] p-4 h-full flex flex-col">
      <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-4">
        Dataset Preview
      </h3>

      {/* Schema Version */}
      <div className="mb-4 pb-4 border-b border-[#1A1A1A]">
        <div className="flex items-center gap-2">
          <span className="text-xs text-terminal-muted uppercase">Schema:</span>
          <span className="text-xs font-mono text-terminal-text">{preview.schemaVersion}</span>
        </div>
      </div>

      {/* Schema Fields */}
      <div className="mb-4 pb-4 border-b border-[#1A1A1A]">
        <h4 className="text-xs font-semibold text-terminal-muted uppercase mb-2">
          Schema Fields
        </h4>
        <div className="space-y-2 max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          {preview.fields.map((field) => (
            <div key={field.name} className="bg-terminal-panel rounded p-2 border border-[#1A1A1A]">
              <div className="flex items-start justify-between gap-2 mb-1">
                <span className="text-xs font-mono font-semibold text-terminal-text">
                  {field.name}
                </span>
                <span
                  className="px-1.5 py-0.5 rounded text-[10px] font-semibold"
                  style={{
                    backgroundColor: '#333',
                    color: '#999',
                  }}
                >
                  {formatFieldType(field.type)}
                </span>
              </div>
              <p className="text-xs text-terminal-muted">{field.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Sample Rows */}
      <div className="flex-1 min-h-0 flex flex-col">
        <h4 className="text-xs font-semibold text-terminal-muted uppercase mb-2">
          Sample Rows ({preview.sampleRows.length})
        </h4>
        <div className="flex-1 overflow-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-[#111111]">
              <tr className="border-b border-[#1A1A1A]">
                {preview.fields.map((field) => (
                  <th
                    key={field.name}
                    className="text-left py-2 px-2 text-terminal-muted font-semibold uppercase"
                  >
                    {field.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.sampleRows.map((row, index) => (
                <tr
                  key={index}
                  className="border-b border-[#1A1A1A] hover:bg-terminal-panel/50 transition-colors"
                >
                  {preview.fields.map((field) => (
                    <td
                      key={field.name}
                      className="py-2 px-2 text-terminal-text font-mono"
                      title={typeof row[field.name] === 'object' ? JSON.stringify(row[field.name]) : String(row[field.name])}
                    >
                      {truncateValue(row[field.name], 30)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Hint */}
      <div className="mt-4 pt-4 border-t border-[#1A1A1A]">
        <p className="text-xs text-terminal-muted italic">
          💡 Replay available from fork rows
        </p>
      </div>
    </div>
  );
}
