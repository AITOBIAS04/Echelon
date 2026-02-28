interface SourceBadgeProps {
  jurisdiction: string;
}

export function SourceBadge({ jurisdiction }: SourceBadgeProps) {
  return (
    <span className="inline-block rounded border border-echelon-border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-500">
      {jurisdiction}
    </span>
  );
}
