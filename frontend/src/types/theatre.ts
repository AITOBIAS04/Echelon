// Theatre Types — Aligned with backend/schemas/theatre.py
// API response types use snake_case matching raw JSON from backend.

// ============================================
// THEATRE (GET /api/v1/theatres)
// ============================================

export type TheatreState =
  | 'DRAFT'
  | 'COMMITTED'
  | 'ACTIVE'
  | 'SETTLING'
  | 'RESOLVED'
  | 'ARCHIVED';

export type InquiryClass =
  | 'COUNTERFACTUAL'
  | 'INVESTIGATIVE'
  | 'INSPECTION'
  | 'SURVEY'
  | 'SCRUTINY';

export interface TheatreResponse {
  id: string;
  user_id: string;
  template_id: string;
  state: TheatreState;
  construct_id: string;
  inquiry_class: InquiryClass | null;
  commitment_hash: string | null;
  committed_at: string | null;
  progress: number;
  total_episodes: number;
  failure_count: number;
  error: string | null;
  resolved_at: string | null;
  certificate_id: string | null;
  stop_condition: string | null;
  stop_config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface TheatreListResponse {
  theatres: TheatreResponse[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================
// TEMPLATE
// ============================================

export interface TemplateResponse {
  id: string;
  template_family: string;
  execution_path: string;
  display_name: string;
  description: string | null;
  schema_version: string;
  inquiry_class: InquiryClass | null;
  created_at: string;
}

export interface TemplateListResponse {
  templates: TemplateResponse[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================
// COMMITMENT RECEIPT
// ============================================

export interface CommitmentReceiptResponse {
  theatre_id: string;
  commitment_hash: string;
  committed_at: string;
  version_pins: Record<string, string>;
  dataset_hashes: Record<string, string>;
}

// ============================================
// CALIBRATION CERTIFICATE
// ============================================

export interface TheatreCertificateResponse {
  id: string;
  theatre_id: string;
  template_id: string;
  construct_id: string;
  inquiry_class: InquiryClass | null;
  criteria_json: Record<string, unknown>;
  scores_json: Record<string, unknown>;
  composite_score: number;
  precision: number | null;
  recall: number | null;
  brier_score: number | null;
  ece: number | null;
  replay_count: number;
  evidence_bundle_hash: string;
  ground_truth_hash: string;
  construct_version: string;
  construct_chain_versions: Record<string, string> | null;
  scorer_version: string;
  methodology_version: string;
  dataset_hash: string;
  verification_tier: string;
  commitment_hash: string;
  issued_at: string;
  expires_at: string | null;
  theatre_committed_at: string;
  theatre_resolved_at: string;
  ground_truth_source: string;
  execution_path: string;
}

export interface TheatreCertificateSummaryResponse {
  id: string;
  theatre_id: string;
  construct_id: string;
  composite_score: number;
  verification_tier: string;
  replay_count: number;
  execution_path: string;
  issued_at: string;
}

export interface CertificateListResponse {
  certificates: TheatreCertificateSummaryResponse[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================
// THEATRE CREATION (POST /api/v1/theatres)
// ============================================

export interface TheatreCreateRequest {
  template_id: string;
  construct_id: string;
  template_json: Record<string, unknown>;
  inquiry_class?: InquiryClass;
  version_pins?: Record<string, string>;
  dataset_hashes?: Record<string, string>;
  stop_condition?: string;
  stop_config?: Record<string, unknown>;
}
