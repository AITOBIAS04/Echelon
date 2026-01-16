import { useState, useEffect } from 'react';
import { useExports } from '../../hooks/useExports';
import { ExportBuilder } from './ExportBuilder';
import { ExportJobTable } from './ExportJobTable';
import { DatasetPreviewPanel } from './DatasetPreviewPanel';
import { AlertCircle } from 'lucide-react';
import type { ExportDatasetKind } from '../../types/exports';

/**
 * ExportConsole Component
 * 
 * Main component for the Export Console, managing export jobs and dataset previews.
 * Layout: 2-column on desktop, 1-column on mobile.
 */
export function ExportConsole() {
  const { jobs, loading, error, refresh, createJob, previews, loadPreview } = useExports();
  const [selectedKind, setSelectedKind] = useState<ExportDatasetKind | undefined>(undefined);

  // Load preview when a kind is selected
  useEffect(() => {
    if (selectedKind && !previews[selectedKind]) {
      loadPreview(selectedKind).catch((err) => {
        console.error('Failed to load preview:', err);
      });
    }
  }, [selectedKind, previews, loadPreview]);

  const handleJobClick = (kind: ExportDatasetKind) => {
    setSelectedKind(kind);
  };

  const handleCreateJob = async (input: { scope: any; filter: any }) => {
    try {
      await createJob(input);
      // Refresh jobs list after creation
      await refresh();
    } catch (err) {
      // Error is handled by hook
      console.error('Failed to create export job:', err);
    }
  };

  return (
    <div className="h-full flex flex-col p-4 gap-4 bg-terminal-bg">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-terminal-text uppercase tracking-wide">
            EXPORT CONSOLE
          </h1>
          <p className="text-sm text-terminal-muted mt-1">
            Create and manage data exports for training and analysis
          </p>
        </div>
        <button
          onClick={() => refresh()}
          disabled={loading}
          className="px-3 py-1.5 text-xs bg-terminal-panel border border-terminal-border rounded hover:border-echelon-cyan transition disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-500">Error</p>
            <p className="text-xs text-terminal-muted">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-4">
        {/* Left Column: Builder + Jobs Table */}
        <div className="flex flex-col gap-4 min-h-0">
          <ExportBuilder onCreateJob={handleCreateJob} loading={loading} />
          <div className="flex-1 min-h-0 overflow-hidden">
            <ExportJobTable jobs={jobs} onJobClick={handleJobClick} />
          </div>
        </div>

        {/* Right Column: Preview Panel */}
        <div className="min-h-0">
          <DatasetPreviewPanel preview={selectedKind ? previews[selectedKind] : undefined} />
        </div>
      </div>
    </div>
  );
}
