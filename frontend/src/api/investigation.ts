/**
 * Investigation API Client
 *
 * All functions use the shared apiClient which handles
 * Bearer token injection and error logging.
 */

import { apiClient } from './client';
import type {
  InvestigationListResponse,
  InvestigationDetail,
  InvestigationSummary,
  EvidenceEnvelopeManifest,
  ClaimGraphSummary,
  CounterSignalFeedResponse,
  DriftFeedResponse,
  EvidenceSubmitRequest,
  EvidenceItem,
  ClaimCreateRequest,
  ClaimNode,
  CounterSignalCreateRequest,
  CounterSignal,
  DriftCreateRequest,
  DriftEvent,
  ReadinessResponse,
  CertificateRecordResponse,
  CertificateBuildResponse,
  AnchorBatchResponse,
} from '../types/investigation';

// ── List & Detail ────────────────────────────────────────────────────────

export async function fetchInvestigations(): Promise<InvestigationListResponse> {
  const { data } = await apiClient.get<InvestigationListResponse>(
    '/api/v1/investigations/'
  );
  return data;
}

export async function fetchInvestigation(
  investigationId: string
): Promise<InvestigationDetail> {
  const { data } = await apiClient.get<InvestigationDetail>(
    `/api/v1/investigations/${investigationId}`
  );
  return data;
}

// ── Sub-resources ────────────────────────────────────────────────────────

export async function fetchEvidence(
  investigationId: string
): Promise<EvidenceEnvelopeManifest> {
  const { data } = await apiClient.get<EvidenceEnvelopeManifest>(
    `/api/v1/investigations/${investigationId}/evidence`
  );
  return data;
}

export async function fetchClaims(
  investigationId: string
): Promise<ClaimGraphSummary> {
  const { data } = await apiClient.get<ClaimGraphSummary>(
    `/api/v1/investigations/${investigationId}/claims`
  );
  return data;
}

export async function fetchCounterSignals(
  investigationId: string
): Promise<CounterSignalFeedResponse> {
  const { data } = await apiClient.get<CounterSignalFeedResponse>(
    `/api/v1/investigations/${investigationId}/counter-signals`
  );
  return data;
}

export async function fetchDrift(
  investigationId: string
): Promise<DriftFeedResponse> {
  const { data } = await apiClient.get<DriftFeedResponse>(
    `/api/v1/investigations/${investigationId}/drift`
  );
  return data;
}

export async function fetchCertificate(
  investigationId: string
): Promise<CertificateRecordResponse> {
  const { data } = await apiClient.get<CertificateRecordResponse>(
    `/api/v1/investigations/${investigationId}/certificate`
  );
  return data;
}

// ── Create ───────────────────────────────────────────────────────────────

export async function createInvestigation(body: {
  theatre_id?: string;
  construct_id?: string;
  inquiry_class?: string;
  domain_filters?: string[];
  stop_condition?: string;
  stop_config?: Record<string, unknown>;
}): Promise<InvestigationSummary> {
  const { data } = await apiClient.post<InvestigationSummary>(
    '/api/v1/investigations/',
    body
  );
  return data;
}

// ── Mutations (submit evidence, claims, counter-signals, drift) ─────────

export async function submitEvidence(
  investigationId: string,
  body: EvidenceSubmitRequest,
): Promise<EvidenceItem> {
  const { data } = await apiClient.post<EvidenceItem>(
    `/api/v1/investigations/${investigationId}/evidence`,
    body,
  );
  return data;
}

export async function submitClaim(
  investigationId: string,
  body: ClaimCreateRequest,
): Promise<ClaimNode> {
  const { data } = await apiClient.post<ClaimNode>(
    `/api/v1/investigations/${investigationId}/claims`,
    body,
  );
  return data;
}

export async function submitCounterSignal(
  investigationId: string,
  body: CounterSignalCreateRequest,
): Promise<CounterSignal> {
  const { data } = await apiClient.post<CounterSignal>(
    `/api/v1/investigations/${investigationId}/counter-signals`,
    body,
  );
  return data;
}

export async function submitDrift(
  investigationId: string,
  body: DriftCreateRequest,
): Promise<DriftEvent> {
  const { data } = await apiClient.post<DriftEvent>(
    `/api/v1/investigations/${investigationId}/drift`,
    body,
  );
  return data;
}

// ── Readiness & Certificate Lifecycle ───────────────────────────────────

export async function fetchReadiness(
  investigationId: string,
): Promise<ReadinessResponse> {
  const { data } = await apiClient.get<ReadinessResponse>(
    `/api/v1/investigations/${investigationId}/readiness`,
  );
  return data;
}

export async function fetchCertificateRecord(
  investigationId: string,
): Promise<CertificateRecordResponse> {
  const { data } = await apiClient.get<CertificateRecordResponse>(
    `/api/v1/investigations/${investigationId}/certificate`,
  );
  return data;
}

export async function buildCertificate(
  investigationId: string,
): Promise<CertificateBuildResponse> {
  const { data } = await apiClient.post<CertificateBuildResponse>(
    `/api/v1/investigations/${investigationId}/certificate/build`,
  );
  return data;
}

export async function anchorBatch(): Promise<AnchorBatchResponse> {
  const { data } = await apiClient.post<AnchorBatchResponse>(
    '/api/v1/investigations/certificates/anchor-batch',
  );
  return data;
}
