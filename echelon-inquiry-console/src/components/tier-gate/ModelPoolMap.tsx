interface ModelPoolMapProps {
  currentTier: 'UNVERIFIED' | 'BACKTESTED' | 'PROVEN';
}

interface TierCard {
  tier: 'UNVERIFIED' | 'BACKTESTED' | 'PROVEN';
  requirement: string;
  modelPool: string;
  routing: string;
  constraintYielding: string;
  expiry: string;
}

const TIER_CARDS: TierCard[] = [
  {
    tier: 'UNVERIFIED',
    requirement: 'Initial certificate issued',
    modelPool: 'Sandbox models only',
    routing: 'Manual review required',
    constraintYielding: 'No yielding permitted',
    expiry: '90 days',
  },
  {
    tier: 'BACKTESTED',
    requirement: '50 replay episodes passed',
    modelPool: 'Standard model pool',
    routing: 'Automated with spot checks',
    constraintYielding: 'Partial yielding (review: light)',
    expiry: '6 months',
  },
  {
    tier: 'PROVEN',
    requirement: '3 months live + telemetry',
    modelPool: 'Full model pool + priority',
    routing: 'Fully automated',
    constraintYielding: 'Full yielding available',
    expiry: '12 months',
  },
];

const TIER_RING: Record<string, string> = {
  UNVERIFIED: 'ring-2 ring-amber-400 shadow-amber-100 shadow-lg',
  BACKTESTED: 'ring-2 ring-blue-400 shadow-blue-100 shadow-lg',
  PROVEN: 'ring-2 ring-emerald-400 shadow-emerald-100 shadow-lg',
};

const TIER_ACCENT: Record<string, string> = {
  UNVERIFIED: 'text-amber-700',
  BACKTESTED: 'text-blue-700',
  PROVEN: 'text-emerald-700',
};

export function ModelPoolMap({ currentTier }: ModelPoolMapProps) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {TIER_CARDS.map((card) => {
        const isCurrent = card.tier === currentTier;
        return (
          <div
            key={card.tier}
            className={`rounded-lg border border-echelon-border bg-white p-5 transition-shadow ${
              isCurrent ? TIER_RING[card.tier] : 'opacity-70'
            }`}
          >
            <h4
              className={`mb-3 text-sm font-bold uppercase tracking-wider ${
                isCurrent ? TIER_ACCENT[card.tier] : 'text-slate-400'
              }`}
            >
              {card.tier}
              {isCurrent && (
                <span className="ml-2 text-xs font-normal normal-case text-slate-500">
                  (current)
                </span>
              )}
            </h4>
            <dl className="space-y-2 text-xs">
              <div>
                <dt className="uppercase tracking-wider text-slate-400">
                  Requirement
                </dt>
                <dd className="mt-0.5 text-slate-700">{card.requirement}</dd>
              </div>
              <div>
                <dt className="uppercase tracking-wider text-slate-400">
                  Model Pool
                </dt>
                <dd className="mt-0.5 text-slate-700">{card.modelPool}</dd>
              </div>
              <div>
                <dt className="uppercase tracking-wider text-slate-400">
                  Routing
                </dt>
                <dd className="mt-0.5 text-slate-700">{card.routing}</dd>
              </div>
              <div>
                <dt className="uppercase tracking-wider text-slate-400">
                  Constraint Yielding
                </dt>
                <dd className="mt-0.5 text-slate-700">
                  {card.constraintYielding}
                </dd>
              </div>
              <div>
                <dt className="uppercase tracking-wider text-slate-400">
                  Expiry
                </dt>
                <dd className="mt-0.5 text-slate-700">{card.expiry}</dd>
              </div>
            </dl>
          </div>
        );
      })}
    </div>
  );
}
