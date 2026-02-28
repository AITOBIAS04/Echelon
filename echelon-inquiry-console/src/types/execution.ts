export interface Episode {
  episode_id: string;
  ground_truth_summary: string;
  expected_class: 'PASS' | 'FAIL';
  construct_output_class: 'PASS' | 'FAIL';
  criteria_scores: Record<string, number>;
  composite_score: number;
  ground_truth_hash: string;
  invocation_hash: string;
}

export interface MarketPhase {
  phase_number: number;
  label: string;
  detail: string;
  hash?: string;
  status: 'pending' | 'active' | 'complete';
}

export interface BundleFileEntry {
  path: string;
  hash?: string;
  status: 'committed' | 'building' | 'complete';
}
