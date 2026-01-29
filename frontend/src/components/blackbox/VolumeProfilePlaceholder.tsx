// Volume Profile Placeholder Component
// TODO: Implement actual volume profile visualization

export function VolumeProfilePlaceholder() {
  return (
    <div className="rounded-2xl border border-[#26292E] bg-[#0F1113] flex flex-col min-h-0 h-full">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#26292E]">
        <span className="text-sm font-semibold text-[#F1F5F9]">VOL PROFILE</span>
        <span className="text-xs font-mono text-[#64748B]">LIMITED</span>
      </div>

      {/* Placeholder Content */}
      <div className="flex-1 min-h-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">📈</div>
          <p className="text-sm font-medium text-[#F1F5F9] mb-1">Coming soon</p>
          <p className="text-xs text-[#64748B]">Volume by price level analysis</p>
        </div>
      </div>
    </div>
  );
}
