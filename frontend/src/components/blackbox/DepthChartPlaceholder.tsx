// Depth Chart Placeholder Component
// TODO: Implement actual depth chart visualization

export function DepthChartPlaceholder() {
  return (
    <div className="rounded-2xl border border-terminal-border bg-terminal-bg flex flex-col min-h-0 h-full">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
        <span className="text-sm font-semibold text-terminal-text">DEPTH CHART</span>
        <span className="text-xs font-mono text-terminal-text-muted">LIMITED</span>
      </div>

      {/* Placeholder Content */}
      <div className="flex-1 min-h-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">📊</div>
          <p className="text-sm font-medium text-terminal-text mb-1">Coming soon</p>
          <p className="text-xs text-terminal-text-muted">Order book depth visualization</p>
        </div>
      </div>
    </div>
  );
}
