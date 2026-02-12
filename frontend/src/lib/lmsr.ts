/**
 * LMSR (Logarithmic Market Scoring Rule) — shared math
 *
 * Used by ImpactCostPanel and DepthChartPanel (Impact Curve).
 * All values are demo/mock — no backend required.
 */

// ── Parameters ──────────────────────────────────────────────────────────
export const LIQUIDITY_B = 142.5;
export const NUM_OUTCOMES = 2;
export const WORST_CASE_LOSS = LIQUIDITY_B * Math.log(NUM_OUTCOMES);

// ── Cost function ───────────────────────────────────────────────────────

/**
 * Binary LMSR cost to move probability from `pFrom` to `pTo`.
 *
 * Uses a simplified log-odds approach scaled for demo realism.
 */
export function lmsrCost(
  pFrom: number,
  pTo: number,
  b: number = LIQUIDITY_B,
): number {
  const qFrom = Math.log(pFrom / (1 - pFrom));
  const qTo = Math.log(pTo / (1 - pTo));
  return Math.abs(b * (qTo - qFrom)) * 0.42; // Scaled for demo realism
}

// ── Curve generator ─────────────────────────────────────────────────────

export interface CurvePoint {
  targetProb: number;
  cost: number;
}

/**
 * Generate an array of `{ targetProb, cost }` points for charting the
 * cost-to-move curve centred on `currentProb`.
 */
export function lmsrCostCurve(
  currentProb: number,
  steps: number = 50,
  maxDelta: number = 0.40,
  b: number = LIQUIDITY_B,
): CurvePoint[] {
  const points: CurvePoint[] = [];
  const pMin = Math.max(0.02, currentProb - maxDelta);
  const pMax = Math.min(0.98, currentProb + maxDelta);

  for (let i = 0; i <= steps; i++) {
    const targetProb = pMin + (i / steps) * (pMax - pMin);
    const cost = lmsrCost(currentProb, targetProb, b);
    points.push({ targetProb, cost });
  }
  return points;
}
