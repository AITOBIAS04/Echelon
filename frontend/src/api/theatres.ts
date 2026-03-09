/**
 * Theatre API Module
 *
 * Wire to backend theatre endpoints:
 *   POST   /api/v1/theatres              — create theatre
 *   GET    /api/v1/theatres/:id          — get theatre
 *   POST   /api/v1/theatres/:id/commit   — commit theatre
 *   POST   /api/v1/theatres/:id/run      — run theatre
 *   POST   /api/v1/theatres/:id/settle   — settle theatre
 *   GET    /api/v1/theatres/:id/commitment — get commitment receipt
 *   GET    /api/v1/theatres/:id/certificate — get theatre certificate
 *   GET    /api/v1/theatres/:id/replay   — get replay
 *   GET    /api/v1/templates             — list templates
 *   GET    /api/v1/templates/:id         — get template
 *   GET    /api/v1/certificates          — list certificates
 *   GET    /api/v1/certificates/:id      — get certificate
 *
 * Note: There is no GET /api/v1/theatres (list) endpoint.
 * The theatre listing uses butterfly timeline health API (via useMarketplace).
 */

import { apiClient } from './client';
import type {
  TheatreResponse,
  TheatreCreateRequest,
  CommitmentReceiptResponse,
  TheatreCertificateResponse,
  TemplateDetailResponse,
  TemplateListResponse,
  CertificateListResponse,
} from '../types/theatre';

// ── Theatre CRUD ────────────────────────────────────────────────────────

export const theatreApi = {
  /** Create a new theatre in DRAFT state */
  createTheatre: async (req: TheatreCreateRequest): Promise<TheatreResponse> => {
    const { data } = await apiClient.post('/api/v1/theatres', req);
    return data;
  },

  /** Get a single theatre by ID */
  getTheatre: async (
    theatreId: string,
    options?: { includeInvestigationContext?: boolean },
  ): Promise<TheatreResponse> => {
    const params = options?.includeInvestigationContext
      ? { include: 'investigation_context' }
      : undefined;
    const { data } = await apiClient.get(`/api/v1/theatres/${theatreId}`, { params });
    return data;
  },

  /** Commit a DRAFT theatre — locks parameters, generates commitment hash */
  commitTheatre: async (theatreId: string): Promise<CommitmentReceiptResponse> => {
    const { data } = await apiClient.post(`/api/v1/theatres/${theatreId}/commit`);
    return data;
  },

  /** Start running a COMMITTED theatre */
  runTheatre: async (theatreId: string): Promise<TheatreResponse> => {
    const { data } = await apiClient.post(`/api/v1/theatres/${theatreId}/run`);
    return data;
  },

  /** Settle an ACTIVE theatre — triggers resolution and certificate generation */
  settleTheatre: async (theatreId: string): Promise<TheatreResponse> => {
    const { data } = await apiClient.post(`/api/v1/theatres/${theatreId}/settle`);
    return data;
  },

  /** Get commitment receipt for a committed theatre */
  getCommitment: async (theatreId: string): Promise<CommitmentReceiptResponse> => {
    const { data } = await apiClient.get(`/api/v1/theatres/${theatreId}/commitment`);
    return data;
  },

  /** Get calibration certificate for a resolved theatre */
  getTheatreCertificate: async (theatreId: string): Promise<TheatreCertificateResponse> => {
    const { data } = await apiClient.get(`/api/v1/theatres/${theatreId}/certificate`);
    return data;
  },

  /** Get fork replay for a theatre */
  getReplay: async (theatreId: string): Promise<unknown> => {
    const { data } = await apiClient.get(`/api/v1/theatres/${theatreId}/replay`);
    return data;
  },
};

// ── Templates ───────────────────────────────────────────────────────────

export const templateApi = {
  /** List available theatre templates */
  listTemplates: async (params?: {
    limit?: number;
    offset?: number;
  }): Promise<TemplateListResponse> => {
    const { data } = await apiClient.get('/api/v1/templates', { params });
    return data;
  },

  /** Get a single template by ID */
  getTemplate: async (templateId: string): Promise<TemplateDetailResponse> => {
    const { data } = await apiClient.get(`/api/v1/templates/${templateId}`);
    return data;
  },
};

// ── Theatre Certificates (list) ─────────────────────────────────────────

export const theatreCertificateApi = {
  /** List all theatre certificates */
  listCertificates: async (params?: {
    limit?: number;
    offset?: number;
  }): Promise<CertificateListResponse> => {
    const { data } = await apiClient.get('/api/v1/certificates', { params });
    return data;
  },

  /** Get a single certificate by ID */
  getCertificate: async (certificateId: string): Promise<TheatreCertificateResponse> => {
    const { data } = await apiClient.get(`/api/v1/certificates/${certificateId}`);
    return data;
  },
};
