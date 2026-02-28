import type { InquiryClass, ExecutionPath } from './signal';

export interface CalibrationCertificate {
  certificate_id: string;
  template_id: string;
  inquiry_class: InquiryClass;
  execution_path: ExecutionPath;
  construct_id: string;
  construct_version: string;
  scorer_version: string;
  issued_at: string;
  expires_at: string;
  replay_count: number;
  criteria_ids: string[];
  criteria_scores: Record<string, number>;
  composite_score: number;
  verification_tier: 'UNVERIFIED' | 'BACKTESTED' | 'PROVEN';
  dataset_hash: string;
  evidence_bundle_hash: string;
  commitment_hash: string;
  methodology: string;
}
