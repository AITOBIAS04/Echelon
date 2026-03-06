/**
 * Cycle 017 Type Stubs
 *
 * Optional mixin interfaces for fields that don't exist in API responses yet.
 * Components import these and check feature flags before rendering.
 *
 * When 017 ships:
 * 1. Extend the real types (e.g. TheatreResponse) with these fields
 * 2. Remove the feature flag gates in components
 * 3. Delete this file
 */

// ── Deployability Routing ───────────────────────────────────────────────
// Appears on: certificates, investigation certificates
// Flag: CYCLE_017_DEPLOYABILITY_ROUTING

export type RoutingHint = 'ALLOWED' | 'REVIEW_REQUIRED' | 'BLOCKED';

export interface DeployabilityRoutingFields {
  routing_hint?: RoutingHint;
  review_reason_code?: string;
}

// ── TAO Flow Metrics ────────────────────────────────────────────────────
// Appears on: timeline/theatre cards, feed ranking
// Flag: CYCLE_017_TAO_FLOW

export interface TaoFlowFields {
  net_inflow_24h?: number;
  net_inflow_7d?: number;
}

// ── Registry Schema Expansion ───────────────────────────────────────────
// Appears on: source metadata badges, investigation detail
// Flag: CYCLE_017_REGISTRY_SCHEMA

export type QueryDeterminism = 'pure_id_lookup' | 'search_endpoint' | 'bulk_export';

export interface RegistrySchemaFields {
  query_determinism?: QueryDeterminism;
  receipt_body_required?: boolean;
  requires_legal_review?: boolean;
}

// ── Coherence Review Gates ──────────────────────────────────────────────
// Appears on: post-routing policy display
// Flag: CYCLE_017_COHERENCE_GATES

export interface CoherenceGateFields {
  coherence_review_required?: boolean;
  coherence_gate_status?: 'PENDING' | 'PASSED' | 'FAILED';
}

// ── Composite: Certificate with 017 extensions ──────────────────────────

export interface Cycle017CertificateExtensions
  extends DeployabilityRoutingFields,
    CoherenceGateFields {}

// ── Composite: Timeline/Theatre with 017 extensions ─────────────────────

export interface Cycle017TimelineExtensions extends TaoFlowFields {}

// ── Composite: Source/Registry with 017 extensions ──────────────────────

export interface Cycle017RegistryExtensions extends RegistrySchemaFields {}
