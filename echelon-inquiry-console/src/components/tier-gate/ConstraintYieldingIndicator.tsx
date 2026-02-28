interface ConstraintYieldingIndicatorProps {
  declaredReview: string;
  effectiveReview: string;
  tier: 'UNVERIFIED' | 'BACKTESTED' | 'PROVEN';
}

export function ConstraintYieldingIndicator({
  declaredReview,
  effectiveReview,
  tier,
}: ConstraintYieldingIndicatorProps) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
      <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-amber-800">
        Constraint Yielding
      </h4>
      <p className="text-sm text-amber-700">
        This construct declared{' '}
        <span className="font-mono font-semibold">review: {declaredReview}</span>{' '}
        but the{' '}
        <span className="font-semibold">{tier}</span> tier overrides this to{' '}
        <span className="font-mono font-semibold">review: {effectiveReview}</span>.
      </p>
      <p className="mt-2 text-xs text-amber-600">
        Constraint yielding allows constructs to declare reduced review
        requirements, but the verification tier enforces a minimum review level.
        Higher tiers unlock the ability to yield constraints.
      </p>
    </div>
  );
}
