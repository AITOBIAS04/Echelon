// Investigation Types — Aligned with backend/investigation/ models
// API response types use snake_case matching raw JSON from backend.
// No `any` types — all fields fully typed.

// ============================================
// ENUMS
// ============================================

export type ProvenanceClass =
  | 'public_primary'
  | 'public_secondary'
  | 'private_leak'
  | 'analyst_derived'
  | 'third_party_tool_output';

export type ClaimType = 'fact' | 'causal' | 'attribution';

export type ClaimStatus =
  | 'supported'
  | 'partially_supported'
  | 'unconfirmed'
  | 'contradicted';

export type StopCondition =
  | 'OUTCOME_RESOLUTION'
  | 'EVIDENCE_THRESHOLD'
  | 'SPONSOR_DEFINED';

export type RoutingDecision = 'ALLOWED' | 'REVIEW_REQUIRED';

// ============================================
// EVIDENCE ENVELOPE
// ============================================

export interface EvidenceItem {
  evidence_id: string;
  content_hash: string;
  provenance_class: ProvenanceClass;
  submitted_at: string;
  content_type: string;
  source_description: string;
  references: string[];
  source_id?: string;
  query_determinism?: string;
}

export interface RedactionEvent {
  redaction_id: string;
  evidence_id: string;
  reason_class: string;
  redacted_at: string;
}

export interface EvidenceEnvelopeManifest {
  items: EvidenceItem[];
  redactions: RedactionEvent[];
  provenance_summary: Record<string, number>;
  envelope_hash: string;
}

// ============================================
// CLAIM GRAPH
// ============================================

export interface CorroborationCheck {
  claim_id: string;
  source_id: string;
  upstream_group: string;
  status: 'confirmed' | 'contradicted' | 'unavailable';
  confidence: number;
}

export interface ClaimNode {
  claim_id: string;
  claim_text: string;
  claim_type: string;
  evidence_refs: string[];
  counter_signals: string[];
  status: string;
  confidence: number;
  independence_groups: string[];
}

export interface ClaimGraphSummary {
  claims: ClaimNode[];
  root_hash: string;
  status_summary: Record<string, number>;
}

// ============================================
// COUNTER-SIGNAL
// ============================================

export interface CounterSignal {
  counter_signal_id: string;
  signal_class: string;
  detected_at: string;
  evidence_ref: string | null;
  material: boolean;
  resolution_impact: string;
  detection_method: string;
}

// ============================================
// DRIFT
// ============================================

export interface DriftEvent {
  drift_id: string;
  drift_type: string;
  detected_at: string;
  original_value: string;
  new_value: string;
  evidence_ref: string | null;
  impact_assessment: string;
}

// ============================================
// ENTITY PROFILE
// ============================================

export interface EntityProfile {
  entity_id: string;
  entity_name: string;
  jurisdiction: string | null;
  registration_number: string | null;
  profile_hash: string;
  resolved_at: string;
  data: Record<string, unknown>;
}

// ============================================
// INVESTIGATION CERTIFICATE
// ============================================

export interface InvestigationCertificate {
  // Identity
  certificate_id: string;
  theatre_id: string;
  construct_id: string;
  inquiry_class: string;

  // Stop condition
  stop_condition: string;
  stop_config: Record<string, unknown>;

  // Timestamps
  investigation_started_at: string;
  investigation_completed_at: string;

  // Evidence envelope summary
  evidence_item_count: number;
  evidence_redaction_count: number;
  evidence_envelope_hash: string;
  provenance_summary: Record<string, number>;

  // Claim graph summary
  claim_count: number;
  claim_status_summary: Record<string, number>;
  claim_graph_root_hash: string;

  // Counter-signal summary
  counter_signals_checked: number;
  counter_signals_gaps: number;
  counter_signals_material: number;
  counter_signal_detail: CounterSignalDetail[];

  // Drift summary
  drift_event_count: number;
  has_material_drift: boolean;
  drift_events: DriftEvent[];

  // Routing
  routing_decision: RoutingDecision;
  routing_reason: string;

  // Certificate hash
  certificate_hash: string;

  // Anchoring
  anchoring_status: 'pending' | 'anchored';
  anchoring_tx_hash: string | null;

  // Metadata
  issued_at: string;
  methodology_version: string;
  toolset_version: string;
}

export interface CounterSignalDetail {
  source: string;
  status: string;
  severity: string;
  is_material: boolean;
}

// ============================================
// INVESTIGATION LIST/DETAIL (API responses)
// ============================================

export interface InvestigationSummary {
  id: string;
  theatre_id: string;
  construct_id: string;
  inquiry_class: string;
  template_id?: string | null;
  template_name?: string | null;
  status: string;
  evidence_count: number;
  claim_count: number;
  counter_signal_count: number;
  drift_event_count: number;
  created_at: string;
  updated_at: string;
}

export interface InvestigationListResponse {
  investigations: InvestigationSummary[];
  total: number;
}

export interface CounterSignalFeedResponse {
  signals: CounterSignal[];
  summary: Record<string, number>;
}

export interface DriftFeedResponse {
  events: DriftEvent[];
  has_material_drift: boolean;
}

export interface InvestigationDetail {
  id: string;
  theatre_id: string;
  construct_id: string;
  inquiry_class: string;
  template_id?: string | null;
  template_name?: string | null;
  status: string;
  stop_condition: string;
  stop_config: Record<string, unknown>;
  domain_filters?: string[];
  committed_sources?: string[];
  created_at: string;
  updated_at: string;
  evidence: EvidenceEnvelopeManifest;
  claims: ClaimGraphSummary;
  counter_signals: CounterSignalFeedResponse;
  drift: DriftFeedResponse;
  has_legal_review_requirement?: boolean;
}

// ============================================
// SUBMISSION REQUEST TYPES
// ============================================

export interface EvidenceSubmitRequest {
  content_base64: string;
  provenance_class: ProvenanceClass;
  content_type?: string;
  source_description?: string;
  source_id?: string;
  receipt_body?: string;
  references?: string[];
}

export interface ClaimCreateRequest {
  claim_text: string;
  claim_type: ClaimType;
  evidence_refs?: string[];
}

export interface CounterSignalCreateRequest {
  signal_class: string;
  material?: boolean;
  resolution_impact?: string;
  detection_method?: string;
  evidence_ref?: string;
}

export type DriftType =
  | 'entity_restructure'
  | 'contract_amendment'
  | 'market_rule_change'
  | 'regulatory_status_change'
  | 'jurisdiction_change';

export type ImpactAssessment = 'non_material' | 'material';

export interface DriftCreateRequest {
  drift_type: DriftType;
  original_value?: string;
  new_value?: string;
  impact_assessment?: ImpactAssessment;
  evidence_ref?: string;
}

// ============================================
// READINESS RESPONSE
// ============================================

export type CertificateLifecycleStatus = 'READY' | 'ANCHORED' | 'ISSUED';

export interface ReadinessResponse {
  investigation_id: string;
  status: string;
  stop_condition: string;
  stop_condition_status: string | null;
  stop_condition_reason: string | null;
  stop_condition_evaluated_at: string | null;
  has_certificate: boolean;
  certificate_status: CertificateLifecycleStatus | null;
}

// ============================================
// CERTIFICATE RECORD (lifecycle states)
// ============================================

export interface CertificateRecordResponse {
  certificate_id: string;
  investigation_id: string;
  certificate_status: CertificateLifecycleStatus;
  certificate_hash: string;
  routing_decision: RoutingDecision;
  routing_reason: string;
  ready_at: string | null;
  anchored_at: string | null;
  issued_at: string | null;
  batch_anchor_hash: string | null;
  certificate_json: Record<string, unknown>;
}

export interface CertificateBuildResponse {
  certificate_id: string;
  certificate_status: CertificateLifecycleStatus;
  certificate_hash: string;
  ready_at: string;
  routing_decision: RoutingDecision;
}

export interface AnchorBatchResponse {
  issued_count: number;
  issued_certificate_ids: string[];
}
