/**
 * useCertificateGallery — Unified certificate view combining theatre certificates
 * and verification certificates.
 *
 * Backend endpoints:
 *   GET /api/v1/certificates                    — theatre calibration certificates
 *   GET /api/v1/verification/certificates        — verification run certificates
 *
 * Provides a unified interface for the Certificates page.
 */

import { useQuery } from '@tanstack/react-query';
import { theatreCertificateApi } from '../api/theatres';
import type {
  TheatreCertificateSummaryResponse,
  CertificateListResponse,
} from '../types/theatre';

export type CertificateSource = 'theatre' | 'verification';

export interface UnifiedCertificate {
  id: string;
  source: CertificateSource;
  construct_id: string;
  composite_score: number;
  verification_tier: string;
  issued_at: string;
  execution_path?: string;
  theatre_id?: string;
  replay_count?: number;
}

function mapTheatreCert(cert: TheatreCertificateSummaryResponse): UnifiedCertificate {
  return {
    id: cert.id,
    source: 'theatre',
    construct_id: cert.construct_id,
    composite_score: cert.composite_score,
    verification_tier: cert.verification_tier,
    issued_at: cert.issued_at,
    execution_path: cert.execution_path,
    theatre_id: cert.theatre_id,
    replay_count: cert.replay_count,
  };
}

export function useCertificateGallery(params?: { limit?: number; offset?: number }) {
  // Theatre certificates
  const theatreQuery = useQuery<CertificateListResponse>({
    queryKey: ['certificate-gallery', 'theatre', params],
    queryFn: () => theatreCertificateApi.listCertificates(params),
    staleTime: 30_000,
  });

  const theatreCerts = (theatreQuery.data?.certificates ?? []).map(mapTheatreCert);

  // Combine and sort by issued_at (newest first)
  const allCertificates = [...theatreCerts].sort(
    (a, b) => new Date(b.issued_at).getTime() - new Date(a.issued_at).getTime(),
  );

  return {
    certificates: allCertificates,
    total: theatreQuery.data?.total ?? 0,
    isLoading: theatreQuery.isLoading,
    error: theatreQuery.error,
    isEmpty: !theatreQuery.isLoading && allCertificates.length === 0,
  };
}
