/**
 * Verification API Types
 *
 * Mirrors backend Pydantic schemas from backend/schemas/verification.py.
 */

// ── Run Status ────────────────────────────────────────────────────────────

export type VerificationRunStatus =
  | 'PENDING'
  | 'INGESTING'
  | 'INVOKING'
  | 'SCORING'
  | 'CERTIFYING'
  | 'COMPLETED'
  | 'FAILED';

/** Terminal statuses — runs in these states will not change. */
export const TERMINAL_STATUSES: VerificationRunStatus[] = ['COMPLETED', 'FAILED'];

/** Active statuses — runs in these states are still progressing. */
export const ACTIVE_STATUSES: VerificationRunStatus[] = [
  'INGESTING',
  'INVOKING',
  'SCORING',
  'CERTIFYING',
];

// ── Verification Run ──────────────────────────────────────────────────────

export interface VerificationRun {
  run_id: string;
  status: VerificationRunStatus;
  progress: number;
  total: number;
  construct_id: string;
  repo_url: string;
  error: string | null;
  certificate_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface VerificationRunListResponse {
  runs: VerificationRun[];
  total: number;
  limit: number;
  offset: number;
}

export interface VerificationRunCreateRequest {
  repo_url: string;
  construct_id: string;
  oracle_type: 'http' | 'python';
  oracle_url?: string;
  oracle_module?: string;
  oracle_callable?: string;
  github_token?: string;
  limit: number;
  min_replays: number;
}

// ── Replay Score ──────────────────────────────────────────────────────────

export interface ReplayScore {
  id: string;
  ground_truth_id: string;
  precision: number;
  recall: number;
  reply_accuracy: number;
  claims_total: number;
  claims_supported: number;
  changes_total: number;
  changes_surfaced: number;
  scoring_model: string;
  scoring_latency_ms: number;
  scored_at: string;
}

// ── Certificate ───────────────────────────────────────────────────────────

export interface Certificate {
  id: string;
  construct_id: string;
  domain: string;
  replay_count: number;
  precision: number;
  recall: number;
  reply_accuracy: number;
  composite_score: number;
  brier: number;
  sample_size: number;
  ground_truth_source: string;
  methodology_version: string;
  scoring_model: string;
  created_at: string;
  replay_scores: ReplayScore[];
}

export interface CertificateSummary {
  id: string;
  construct_id: string;
  domain: string;
  replay_count: number;
  composite_score: number;
  brier: number;
  created_at: string;
}

export interface CertificateListResponse {
  certificates: CertificateSummary[];
  total: number;
  limit: number;
  offset: number;
}

// ── Filter / Query Params ─────────────────────────────────────────────────

export interface RunFilters {
  status?: VerificationRunStatus;
  construct_id?: string;
  limit?: number;
  offset?: number;
}

export interface CertFilters {
  construct_id?: string;
  sort?: 'brier_asc' | 'created_desc';
  limit?: number;
  offset?: number;
}
