/**
 * ExportConsolePage — Stub
 *
 * TODO: Implement export console UI from combined HTML prototype.
 * Should allow batch export of agent data, RLMF episodes, and market snapshots.
 */
export function ExportConsolePage() {
  return (
    <div className="h-full flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="text-4xl mb-4">📦</div>
        <h1 className="text-lg font-bold text-terminal-text uppercase tracking-wider mb-2">
          Export Console
        </h1>
        <p className="text-sm text-terminal-text-secondary mb-4">
          Batch export agent data, RLMF episodes, and market snapshots.
        </p>
        <span className="inline-block px-3 py-1.5 text-xs font-mono text-terminal-text-muted border border-terminal-border rounded-lg bg-terminal-card">
          COMING SOON
        </span>
      </div>
    </div>
  );
}
