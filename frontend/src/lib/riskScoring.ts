import type {
  PositionExposure,
  TimelineRiskState,
  PortfolioRiskSummary,
  TopRisk,
} from '../types/risk';

/**
 * Risk Scoring Library
 * ====================
 * 
 * Pure functions for computing risk scores and portfolio risk analysis.
 * All functions are deterministic and side-effect free.
 */

/**
 * Clamp a value to the range [0, 1]
 */
export function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}

/**
 * Clamp a value to the range [0, 100]
 */
export function clamp100(x: number): number {
  return Math.max(0, Math.min(100, x));
}

/**
 * Compute Burn at Collapse
 * 
 * Calculates the estimated loss if a timeline collapses to a specific outcome.
 * 
 * This is a simplified MVP implementation:
 * - If user holds YES and outcome is NO (timeline collapse), burnAtCollapse = notional
 * - If user holds NO and outcome is NO, burnAtCollapse = 0 (they benefit; show 0)
 * - If user holds NO and outcome is YES, burnAtCollapse = notional (simplified)
 * - If user holds YES and outcome is YES, burnAtCollapse = 0
 * 
 * Note: This is a placeholder implementation. In production, this would:
 * - Account for partial fills and average entry prices
 * - Consider market depth and slippage
 * - Factor in settlement mechanics and oracle resolution
 * - Handle edge cases like paradox extraction costs
 * 
 * @param pos - Position exposure
 * @param collapseOutcome - Expected outcome if timeline collapses ('YES' or 'NO')
 * @returns Estimated loss in base currency (0 if position benefits from collapse)
 */
export function computeBurnAtCollapse(
  pos: PositionExposure,
  collapseOutcome: 'NO' | 'YES'
): number {
  // If position direction matches collapse outcome, no loss
  if (pos.direction === collapseOutcome) {
    return 0;
  }
  
  // If position direction opposes collapse outcome, full notional is at risk
  return pos.notional;
}

/**
 * Compute Timeline Risk Score
 * 
 * Calculates a composite risk score (0-100) for a timeline based on its risk state.
 * 
 * Formula:
 * - Fragility = (100 - stability) weighted + entropyRate*10 + sabotageHeat24h*5
 * - Divergence = logicGap*0.6 + paradoxProximity*0.4
 * - Time Pressure = nextForkEtaSec ? clamp100((600 - nextForkEtaSec)/6) : 0
 * - Score = clamp100(0.45*fragility + 0.45*divergence + 0.10*timePressure)
 * 
 * @param state - Timeline risk state
 * @returns Object with score (0-100) and drivers (human-readable list)
 */
export function computeTimelineRiskScore(
  state: TimelineRiskState
): { score: number; drivers: string[] } {
  // Fragility component: combines stability, entropy, and sabotage
  const stabilityContribution = 100 - state.stability;
  const entropyContribution = Math.abs(state.entropyRate) * 10;
  const sabotageContribution = state.sabotageHeat24h * 5;
  const fragility = clamp100(
    stabilityContribution + entropyContribution + sabotageContribution
  );

  // Divergence component: combines logic gap and paradox proximity
  const divergence = clamp100(
    state.logicGap * 0.6 + state.paradoxProximity * 0.4
  );

  // Time pressure component: urgency based on next fork timing
  const timePressure = state.nextForkEtaSec
    ? clamp100((600 - state.nextForkEtaSec) / 6)
    : 0;

  // Composite score
  const score = clamp100(
    0.45 * fragility + 0.45 * divergence + 0.1 * timePressure
  );

  // Identify top contributors for drivers
  const drivers: string[] = [];
  const contributions: Array<{ label: string; value: number }> = [];

  // Fragility contributors
  if (state.stability < 50) {
    contributions.push({ label: 'Low stability', value: stabilityContribution });
  }
  if (Math.abs(state.entropyRate) > 2) {
    contributions.push({ label: 'High entropy rate', value: entropyContribution });
  }
  if (state.sabotageHeat24h > 0) {
    contributions.push({ label: 'Sabotage activity', value: sabotageContribution });
  }

  // Divergence contributors
  if (state.logicGap > 40) {
    contributions.push({ label: 'High logic gap', value: state.logicGap * 0.6 });
  }
  if (state.paradoxProximity > 60) {
    contributions.push({
      label: 'Paradox proximity',
      value: state.paradoxProximity * 0.4,
    });
  }

  // Time pressure contributor
  if (timePressure > 20) {
    contributions.push({ label: 'Upcoming fork', value: timePressure });
  }

  // Sort by value and take top 2
  contributions.sort((a, b) => b.value - a.value);
  drivers.push(...contributions.slice(0, 2).map((c) => c.label));

  // Fallback if no drivers identified
  if (drivers.length === 0) {
    drivers.push('Moderate risk factors');
  }

  return { score, drivers };
}

/**
 * Compute Portfolio Risk
 * 
 * Aggregates risk analysis across all positions in a portfolio.
 * 
 * Process:
 * 1. Join positions with their timeline risk states by timelineId
 * 2. Weight each timeline by absolute notional value
 * 3. Compute weighted average risk index
 * 4. Calculate fragility and divergence indices
 * 5. Identify top 5 risks by weighted risk score
 * 6. Generate recommendations
 * 
 * @param positions - Array of position exposures
 * @param states - Array of timeline risk states
 * @returns Portfolio risk summary
 */
export function computePortfolioRisk(
  positions: PositionExposure[],
  states: TimelineRiskState[]
): PortfolioRiskSummary {
  const asOf = new Date().toISOString();

  // Create a map of timelineId -> risk state for efficient lookup
  const stateMap = new Map<string, TimelineRiskState>();
  states.forEach((state) => {
    stateMap.set(state.timelineId, state);
  });

  // Calculate total notional and net positions
  let totalNotional = 0;
  let netYesNotional = 0;
  let netNoNotional = 0;

  positions.forEach((pos) => {
    totalNotional += Math.abs(pos.notional);
    if (pos.direction === 'YES') {
      netYesNotional += pos.notional;
    } else {
      netNoNotional += pos.notional;
    }
  });

  // Compute risk scores for each timeline with positions
  const timelineScores: Array<{
    timelineId: string;
    label: string;
    riskScore: number;
    drivers: string[];
    notionalWeight: number;
    burnAtCollapse: number;
    state: TimelineRiskState;
  }> = [];

  positions.forEach((pos) => {
    const state = stateMap.get(pos.timelineId);
    if (!state) {
      // Skip positions without risk state data
      return;
    }

    const { score, drivers } = computeTimelineRiskScore(state);
    const notionalWeight = Math.abs(pos.notional) / totalNotional;
    const burnAtCollapse = computeBurnAtCollapse(pos, 'NO');

    timelineScores.push({
      timelineId: pos.timelineId,
      label: `Timeline ${pos.timelineId.substring(0, 8)}...`,
      riskScore: score,
      drivers,
      notionalWeight,
      burnAtCollapse,
      state,
    });
  });

  // Compute weighted average risk index
  const riskIndex = timelineScores.reduce((sum, ts) => {
    return sum + ts.riskScore * ts.notionalWeight;
  }, 0);

  // Compute fragility index (weighted average)
  const fragilityIndex = timelineScores.reduce((sum, ts) => {
    const fragility = clamp100(
      (100 - ts.state.stability) +
        Math.abs(ts.state.entropyRate) * 10 +
        ts.state.sabotageHeat24h * 5
    );
    return sum + fragility * ts.notionalWeight;
  }, 0);

  // Compute belief divergence index (weighted average)
  const beliefDivergenceIndex = timelineScores.reduce((sum, ts) => {
    const divergence = clamp100(
      ts.state.logicGap * 0.6 + ts.state.paradoxProximity * 0.4
    );
    return sum + divergence * ts.notionalWeight;
  }, 0);

  // Get top 5 risks by weighted risk score
  const topRisks: TopRisk[] = timelineScores
    .sort((a, b) => {
      // Sort by riskScore * notionalWeight (weighted risk)
      const aWeighted = a.riskScore * a.notionalWeight;
      const bWeighted = b.riskScore * b.notionalWeight;
      return bWeighted - aWeighted;
    })
    .slice(0, 5)
    .map((ts) => ({
      timelineId: ts.timelineId,
      label: ts.label,
      riskScore: ts.riskScore,
      drivers: ts.drivers,
      burnAtCollapse: ts.burnAtCollapse,
    }));

  // Generate recommendations
  const recommendations: string[] = [];

  if (riskIndex > 70) {
    recommendations.push('Consider reducing overall portfolio exposure');
  }

  if (beliefDivergenceIndex > 60) {
    recommendations.push('High belief divergence detected; monitor paradox proximity');
  }

  if (fragilityIndex > 60) {
    recommendations.push('Portfolio fragility elevated; review stability metrics');
  }

  const highBurnRisks = topRisks.filter((r) => r.burnAtCollapse > totalNotional * 0.1);
  if (highBurnRisks.length > 0) {
    recommendations.push(
      `Consider hedging positions in ${highBurnRisks.length} high-burn-risk timeline${highBurnRisks.length !== 1 ? 's' : ''}`
    );
  }

  if (topRisks.length > 0 && topRisks[0].riskScore > 80) {
    recommendations.push(
      `Monitor ${topRisks[0].label} closely; risk score exceeds 80`
    );
  }

  return {
    asOf,
    totalNotional,
    netYesNotional,
    netNoNotional,
    riskIndex: clamp100(riskIndex),
    fragilityIndex: clamp100(fragilityIndex),
    beliefDivergenceIndex: clamp100(beliefDivergenceIndex),
    topRisks,
    recommendations,
  };
}
