/**
 * useTheatreTemplates — React Query hook for theatre template catalog.
 *
 * Used by Create Theatre flow to browse and select templates.
 */

import { useQuery } from '@tanstack/react-query';
import { templateApi } from '../api/theatres';
import type {
  TemplateDetailResponse,
  TemplateListResponse,
} from '../types/theatre';

export function useTheatreTemplates() {
  const query = useQuery<TemplateListResponse>({
    queryKey: ['theatre-templates'],
    queryFn: () => templateApi.listTemplates({ limit: 100 }),
    staleTime: 60_000, // Templates change infrequently
  });

  return {
    templates: query.data?.templates ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    isEmpty: !query.isLoading && (query.data?.templates?.length ?? 0) === 0,
  };
}

export function useTheatreTemplate(templateId: string | null) {
  const query = useQuery<TemplateDetailResponse>({
    queryKey: ['theatre-template', templateId],
    queryFn: () => templateApi.getTemplate(templateId!),
    enabled: !!templateId,
    staleTime: 60_000,
  });

  return {
    template: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
}
