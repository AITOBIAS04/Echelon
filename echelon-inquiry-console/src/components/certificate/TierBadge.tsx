interface TierBadgeProps {
  tier: 'UNVERIFIED' | 'BACKTESTED' | 'PROVEN';
  size?: 'sm' | 'md' | 'lg';
}

const TIER_STYLES: Record<string, string> = {
  UNVERIFIED: 'bg-amber-100 text-amber-800 border-amber-300',
  BACKTESTED: 'bg-blue-100 text-blue-800 border-blue-300',
  PROVEN: 'bg-emerald-100 text-emerald-800 border-emerald-300',
};

const SIZE_STYLES: Record<string, string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-4 py-1.5 text-base',
};

export function TierBadge({ tier, size = 'md' }: TierBadgeProps) {
  return (
    <span
      className={`inline-block rounded border font-semibold uppercase tracking-wider ${TIER_STYLES[tier]} ${SIZE_STYLES[size]}`}
    >
      {tier}
    </span>
  );
}
