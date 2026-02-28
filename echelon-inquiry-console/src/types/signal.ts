export type InquiryClass =
  | 'COUNTERFACTUAL'
  | 'INVESTIGATIVE'
  | 'INSPECTION'
  | 'SURVEY'
  | 'SCRUTINY';

export type ExecutionPath = 'PRODUCT' | 'MARKET';

export interface Signal {
  id: string;
  source_id: string;
  source_group: string;
  source_name: string;
  jurisdiction: string;
  headline: string;
  summary: string;
  timestamp: string;
  confidence: number;
  settlement_eligible: boolean;
  access_surface: 'public_api' | 'paid_gateway' | 'portal_scrape';
  receipt_mode: 'http_transcript' | 'signed_payload' | 'screenshot';
  suggested_class: InquiryClass;
}
