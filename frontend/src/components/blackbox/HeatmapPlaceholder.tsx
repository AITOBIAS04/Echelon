// Heatmap Placeholder Component
// TODO: Implement actual market heatmap visualization

export function HeatmapPlaceholder() {
  return (
    <div className="rounded-2xl border border-[#26292E] bg-slate-950 flex flex-col min-h-0 h-full">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#26292E]">
        <span className="text-sm font-semibold text-[#F1F5F9]">HEATMAP</span>
        <span className="text-xs font-mono text-[#64748B]">LIMITED</span>
      </div>

      {/* Placeholder Content */}
      <div className="flex-1 min-h-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">🔥</div>
          <p className="text-sm font-medium text-[#F1F5F9] mb-1">Coming soon</p>
          <p className="text-xs text-[#64748B]">Market overview heatmap</p>
        </div>
      </div>
    </div>
  );
}
