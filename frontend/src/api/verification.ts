/**
 * Verification API Client
 *
 * All functions use the shared apiClient which handles
 * Bearer token injection and error logging.
 */

import { apiClient } from './client';
import type {
  VerificationRun,
  VerificationRunListResponse,
  VerificationRunCreateRequest,
  Certificate,
  CertificateListResponse,
  RunFilters,
  CertFilters,
} from '../types/verification';

// ── Runs (authenticated) ──────────────────────────────────────────────────

export async function fetchVerificationRuns(
  params: RunFilters = {}
): Promise<VerificationRunListResponse> {
  const query: Record<string, string> = {};
  if (params.status) query.status = params.status;
  if (params.construct_id) query.construct_id = params.construct_id;
  if (params.limit != null) query.limit = String(params.limit);
  if (params.offset != null) query.offset = String(params.offset);

  const { data } = await apiClient.get<VerificationRunListResponse>(
    '/api/v1/verification/runs',
    { params: query }
  );
  return data;
}

export async function fetchVerificationRun(
  runId: string
): Promise<VerificationRun> {
  const { data } = await apiClient.get<VerificationRun>(
    `/api/v1/verification/runs/${runId}`
  );
  return data;
}

export async function createVerificationRun(
  body: VerificationRunCreateRequest
): Promise<VerificationRun> {
  const { data } = await apiClient.post<VerificationRun>(
    '/api/v1/verification/runs',
    body
  );
  return data;
}

// ── Certificates (public — no auth needed) ────────────────────────────────

export async function fetchCertificates(
  params: CertFilters = {}
): Promise<CertificateListResponse> {
  const query: Record<string, string> = {};
  if (params.construct_id) query.construct_id = params.construct_id;
  if (params.sort) query.sort = params.sort;
  if (params.limit != null) query.limit = String(params.limit);
  if (params.offset != null) query.offset = String(params.offset);

  const { data } = await apiClient.get<CertificateListResponse>(
    '/api/v1/verification/certificates',
    { params: query }
  );
  return data;
}

export async function fetchCertificate(
  certId: string
): Promise<Certificate> {
  const { data } = await apiClient.get<Certificate>(
    `/api/v1/verification/certificates/${certId}`
  );
  return data;
}
