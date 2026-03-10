// Scenario Pack Types — Aligned with backend/schemas/scenario_packs.py
// Template types live in api/scenarioPacks.ts (inline). These cover pack lifecycle.

export type PackState =
  | 'DRAFT'
  | 'COMMITTED'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED';

export type RunStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED';

export interface ScenarioPackCreate {
  template_id: string;
  run_mode?: string;
  agent_assignment?: string;
  simulation_scale?: string;
  objective_profile?: string;
  config_json?: Record<string, unknown>;
}

export interface ScenarioPackResponse {
  id: string;
  user_id: string;
  template_id: string;
  state: PackState;
  run_mode: string;
  agent_assignment: string;
  simulation_scale: string;
  objective_profile: string;
  commitment_hash: string | null;
  committed_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScenarioRunResponse {
  id: string;
  pack_id: string;
  agent_id: string | null;
  status: RunStatus;
  environment_seed: number | null;
  run_mode: string;
  current_checkpoint_seq: number;
  started_at: string | null;
  completed_at: string | null;
  episode_duration_sec: number | null;
  total_reward: number;
  created_at: string;
}

export interface EpisodeTreeNode {
  checkpoint_id: string;
  sequence_num: number;
  trigger: string;
  market_question: string;
  selected_branch: string | null;
  outcome_type: string | null;
  reward: number | null;
  spawned_theatre_id: string | null;
  children: EpisodeTreeNode[];
}

export interface EpisodeTreeResponse {
  run_id: string;
  pack_id: string;
  template_name: string;
  status: string;
  nodes: EpisodeTreeNode[];
  total_reward: number;
  episode_duration_sec: number | null;
}

export interface BranchProbabilitiesResponse {
  template_id: string;
  probabilities: Record<string, Record<string, number> | null>;
}

export interface DisclosureEvent {
  tMs: number;
  type: string;
  label: string;
}

export interface ForkOptionPricePath {
  tMs: number;
  price: number;
}

export interface ReplayForkOption {
  label: string;
  pricePath: ForkOptionPricePath[];
}

export interface ForkReplayResponse {
  timelineId: string;
  forkId: string;
  forkQuestion: string;
  options: ReplayForkOption[];
  openedAt: string;
  settledAt: string | null;
  chosenOption: string | null;
  outcomeLabel: string | null;
  disclosureEvents: DisclosureEvent[];
  notes: string | null;
}

export interface DerivedTheatreResponse {
  id: string;
  construct_id: string;
  state: string;
  spawned_from_checkpoint_id: string | null;
  certificate_id: string | null;
  created_at: string;
}
