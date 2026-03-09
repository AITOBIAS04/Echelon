/**
 * useInvestigationTemplates — React Query hook for investigation template endpoints.
 *
 * Long stale time — seeded template data changes rarely.
 */

import { useQuery } from '@tanstack/react-query';
import {
  fetchInvestigationTemplates,
  fetchInvestigationTemplate,
} from '../api/investigationTemplates';
import type {
  InvestigationTemplateListItem,
  InvestigationTemplateDetail,
} from '../api/investigationTemplates';

// ── List ────────────────────────────────────────────────────────────────

export function useInvestigationTemplates(params?: {
  inquiry_class?: string;
  status?: string;
}) {
  const query = useQuery({
    queryKey: ['investigation-templates', params],
    queryFn: () => fetchInvestigationTemplates(params),
    staleTime: 5 * 60 * 1000, // 5 minutes — seeded data changes rarely
  });

  return {
    templates: (query.data?.templates ?? []) as InvestigationTemplateListItem[],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
  };
}

// ── Detail ──────────────────────────────────────────────────────────────

export function useInvestigationTemplateDetail(templateId: string | null) {
  const query = useQuery({
    queryKey: ['investigation-template', templateId],
    queryFn: () => fetchInvestigationTemplate(templateId!),
    enabled: !!templateId,
    staleTime: 5 * 60 * 1000,
  });

  return {
    template: (query.data ?? null) as InvestigationTemplateDetail | null,
    isLoading: query.isLoading,
    error: query.error,
  };
}
