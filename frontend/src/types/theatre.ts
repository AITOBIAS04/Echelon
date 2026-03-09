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

export interface TheatreInvestigationContextCertificateSummary {
  certificate_id: string;
  routing_hint: string | null;
  composite_score: number | null;
  verification_tier: string | null;
  coherence_gate_status: string | null;
  issued_at: string | null;
}

export interface TheatreInvestigationContextDeploymentSummary {
  active_count: number;
  archetype_breakdown: Record<string, number>;
}

export interface TheatreInvestigationContextConvergenceSummary {
  cell_count: number;
  nearby_signal_count: number;
  source_families: string[];
}

export interface TheatreInvestigationContextResponse {
  certificate_summary: TheatreInvestigationContextCertificateSummary | null;
  deployment_summary: TheatreInvestigationContextDeploymentSummary;
  paradox_risk_level: string | null;
  paradox_risk_factors_json: Record<string, unknown> | null;
  convergence_summary: TheatreInvestigationContextConvergenceSummary;
}

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
  paradox_risk_level: string | null;
  paradox_risk_factors_json: Record<string, unknown> | null;
  investigation_context?: TheatreInvestigationContextResponse | null;
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

export interface TemplateSummaryResponse {
  id: string;
  template_family: string;
  execution_path: string;
  display_name: string;
  description: string | null;
  schema_version: string;
  inquiry_class: InquiryClass | null;
  created_at: string;
}

export interface TemplateDetailResponse extends TemplateSummaryResponse {
  template_json: Record<string, unknown>;
}

export interface TemplateListResponse {
  templates: TemplateSummaryResponse[];
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

export type RoutingHint = 'ALLOWED' | 'REVIEW_REQUIRED' | 'BLOCKED';
export type GateStatus = 'PENDING' | 'PASSED' | 'FAILED';

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
  // Cycle-017: Policy Surface
  routing_hint: RoutingHint | null;
  review_reason_code: string | null;
  coherence_review_required: boolean;
  coherence_gate_status: string | null;
  coherence_reviewed_at: string | null;
  is_deployable: boolean;
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
  // Cycle-017: Policy Surface
  routing_hint: RoutingHint | null;
  coherence_gate_status: string | null;
  is_deployable: boolean;
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
