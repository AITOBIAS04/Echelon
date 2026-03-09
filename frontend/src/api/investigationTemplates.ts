/**
 * Investigation Templates API Client
 *
 * Wire to backend investigation template endpoints:
 *   GET  /api/v1/investigation-templates/         — list templates
 *   GET  /api/v1/investigation-templates/:id      — get template detail
 */

import { apiClient } from './client';

// ── Response Types ──────────────────────────────────────────────────────

export interface InvestigationTemplateListItem {
  template_id: string;
  name: string;
  description: string | null;
  inquiry_class: string;
  template_status: string;
  domain_filter_count: number;
  requires_legal_review: boolean;
}

export interface InvestigationTemplateListResponse {
  templates: InvestigationTemplateListItem[];
  total: number;
}

export interface InvestigationTemplateDetail {
  template_id: string;
  name: string;
  description: string | null;
  inquiry_class: string;
  domain_filters: string[];
  default_sources: string[];
  default_stop_condition: string;
  default_time_window_days: number | null;
  requires_legal_review: boolean;
  min_corroboration_groups: number;
  template_status: string;
  is_seeded: boolean;
  created_at: string;
}

// ── API Functions ───────────────────────────────────────────────────────

export async function fetchInvestigationTemplates(params?: {
  inquiry_class?: string;
  status?: string;
}): Promise<InvestigationTemplateListResponse> {
  const { data } = await apiClient.get<InvestigationTemplateListResponse>(
    '/api/v1/investigation-templates/',
    { params },
  );
  return data;
}

export async function fetchInvestigationTemplate(
  templateId: string,
): Promise<InvestigationTemplateDetail> {
  const { data } = await apiClient.get<InvestigationTemplateDetail>(
    `/api/v1/investigation-templates/${templateId}`,
  );
  return data;
}
