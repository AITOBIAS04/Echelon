import type { InquiryClass, ExecutionPath } from './signal';

export interface TheatreTemplate {
  template_id: string;
  name: string;
  inquiry_class: InquiryClass;
  execution_path: ExecutionPath;
  criteria_ids: string[];
  fixture_count: number;
  pass_count: number;
  fail_count: number;
  existing_composite: number;
  construct_id: string;
  construct_version: string;
  scorer_version: string;
  commitment_hash: string;
  template_tags?: string[];
}

export interface CommitmentTarget {
  dataset_hashes: {
    ground_truth: string;
    fixtures: string;
  };
  template: {
    template_id: string;
    version: string;
    criteria_ids: string[];
    scoring_thresholds: Record<string, number>;
  };
  version_pins: {
    construct: string;
    scorer: string;
    methodology: string;
  };
}
