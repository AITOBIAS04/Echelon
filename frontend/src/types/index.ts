// ============================================
// ENUMS — Aligned with backend/schemas/butterfly_schemas.py
// ============================================

import type { AgentArchetype } from './agents';

export type WingFlapType =
  // Original 010b types
  | 'TRADE'
  | 'SHIELD'
  | 'SABOTAGE'
  | 'RIPPLE'
  | 'PARADOX'
  | 'FOUNDER_YIELD'
  | 'ENTROPY'
  // 016 Coherence Lock additions
  | 'MIRROR_SYNC'
  | 'MIRROR_TRADE'
  | 'EVIDENCE'
  | 'CLAIM'
  | 'COUNTER_SIGNAL'
  | 'CORROBORATION'
  | 'DETONATION'
  | 'FORK_SPAWN'
  | 'STOP_CONDITION'
  | 'CERTIFICATE';

export type StabilityDirection = 'STABILISE' | 'DESTABILISE' | 'NEUTRAL';

export type ParadoxStatus = 'ACTIVE' | 'EXTRACTING' | 'DETONATED' | 'RESOLVED';
export type SeverityClass = 'CLASS_1_CRITICAL' | 'CLASS_2_SEVERE' | 'CLASS_3_MODERATE' | 'CLASS_4_MINOR';

// ============================================
// WING FLAP — backend/schemas/butterfly_schemas.py
// ============================================

export interface WingFlap {
  id: string;
  timestamp: string;
  timeline_id: string;
  timeline_name: string;
  agent_id: string;
  agent_name: string;
  agent_archetype: AgentArchetype;
  flap_type: WingFlapType;
  action: string;
  stability_delta: number;
  direction: StabilityDirection;
  volume_usd: number;
  timeline_stability: number;
  timeline_price: number;
  spawned_ripple: boolean;
  ripple_timeline_id: string | null;
  founder_id: string | null;
  founder_yield_earned: number | null;
}

export interface WingFlapFeedResponse {
  flaps: WingFlap[];
  total_count: number;
  has_more: boolean;
}

// ============================================
// TIMELINE — backend/schemas/butterfly_schemas.py TimelineHealth
// ============================================

export interface Timeline {
  id: string;
  name: string;

  // Core metrics (API: 0-100 percentage)
  stability: number;
  surface_tension: number;
  price_yes: number;
  price_no: number;

  // OSINT alignment
  osint_alignment: number;
  logic_gap: number;

  // Gravity
  gravity_score: number;
  gravity_factors: Record<string, number>;

  // Liquidity
  total_volume_usd: number;
  liquidity_depth_usd: number;

  // Agents
  active_agent_count: number;
  dominant_agent_id: string | null;
  dominant_agent_name: string | null;

  // Founder
  founder_id: string | null;
  founder_name: string | null;
  founder_yield_rate: number;

  // Decay
  decay_rate_per_hour: number;
  decay_multiplier: number;
  hours_until_reaper: number | null;

  // Paradox
  has_active_paradox: boolean;
  paradox_id: string | null;
  paradox_detonation_time: string | null;

  // Anchor / Fork (016 Coherence Lock)
  is_anchor: boolean;
  anchor_timeline_id: string | null;
  fork_divergence: number;
  last_sync_at: string | null;

  // TAO Flow (Cycle-017)
  net_inflow_24h?: number;
  net_inflow_7d?: number;

  // Connections
  connected_timeline_ids: string[];
  parent_timeline_id: string | null;
}

export interface TimelineHealthResponse {
  timelines: Timeline[];
  total_count: number;
}

// ============================================
// PARADOX — backend/schemas/paradox_schemas.py
// ============================================

export interface Paradox {
  id: string;
  timeline_id: string;
  timeline_name: string;
  status: ParadoxStatus;
  severity_class: SeverityClass;
  logic_gap: number;
  spawned_at: string;
  detonation_time: string;
  time_remaining_seconds: number;
  decay_multiplier: number;
  extraction_cost_usdc: number;
  extraction_cost_echelon: number;
  carrier_sanity_cost: number;
  carrier_agent_id: string | null;
  carrier_agent_name: string | null;
  carrier_agent_sanity: number | null;
  connected_timelines: string[];
}

export interface ParadoxListResponse {
  paradoxes: Paradox[];
  total_active: number;
}

// ============================================
// USER / AUTH
// ============================================

export interface User {
  id: string;
  username: string;
  email: string;
  tier: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// ============================================
// RE-EXPORTS
// ============================================

// Watchlist
export type {
  WatchlistItem,
  WatchlistItemType,
  WatchlistAddRequest,
  WatchlistResponse,
  WatchlistFilter,
  WatchlistState,
  WatchlistTimeline,
} from './watchlist';

// Portfolio
export type {
  UserPosition,
  UserPositionsResponse,
  PortfolioSummary,
  PrivateFork,
  PrivateForksResponse,
  ChartTimeframe,
  PositionTab,
  EquityDataPoint,
} from './portfolio';

// Agents
export type {
  AgentArchetype,
  Agent,
  AgentListResponse,
  SanityLevel,
  AgentView,
} from './agents';
export { getSanityLevel } from './agents';

// Investigation
export type {
  ProvenanceClass,
  ClaimType,
  ClaimStatus,
  StopCondition,
  RoutingDecision,
  EvidenceItem,
  RedactionEvent,
  EvidenceEnvelopeManifest,
  CorroborationCheck,
  ClaimNode,
  ClaimGraphSummary,
  CounterSignal,
  DriftEvent,
  EntityProfile,
  InvestigationCertificate,
  CounterSignalDetail,
  CounterSignalFeedResponse,
  DriftFeedResponse,
  InvestigationSummary,
  InvestigationListResponse,
  InvestigationDetail,
} from './investigation';

// Theatre
export type {
  TheatreState,
  InquiryClass,
  RoutingHint,
  GateStatus,
  TheatreResponse,
  TheatreListResponse,
  TemplateSummaryResponse,
  TemplateDetailResponse,
  TemplateListResponse,
  CommitmentReceiptResponse,
  TheatreCertificateResponse,
  TheatreCertificateSummaryResponse,
  CertificateListResponse,
  TheatreCreateRequest,
} from './theatre';

// Timeline Detail
export type {
  TimelineDetail,
  TimelineHealthSnapshot,
  ForkEvent,
  ForkOption,
  SabotageEvent,
  EvidenceEntry,
  ExtractionAttempt,
  UserPosition as TimelineUserPosition,
} from './timeline-detail';

export type { ParadoxStatus as TimelineParadoxStatus } from './timeline-detail';

// Breach
export type {
  BreachSeverity,
  BreachCategory,
  Breach,
  AffectedTimeline,
  AffectedAgent,
  Beneficiary,
  EvidenceChange,
  SuggestedAction,
  BreachStats,
} from './breach';

// Marketplace
export type {
  MarketCategory,
  RibbonEvent,
  SortOption,
  MarketFilterState,
  PaginationState,
  MarketStats,
  CompareSlot,
  BetFormData,
  // Legacy types (used by mock hooks, removed in tasks 1.3-1.5)
  Market,
  Intercept,
  Breach as MarketplaceBreach,
  Alert,
  CreateAlertForm,
  UserPosition as MarketplaceUserPosition,
  RLMFTrainingData,
} from './marketplace';

// Exports
export type {
  ExportDatasetKind,
  ExportScope,
  ExportFilter,
  ExportJob,
  DatasetSchemaField,
  DatasetPreview,
} from './exports';

// Replay
export type {
  DisclosureEventType,
  DisclosureEvent,
  ForkOptionPricePath,
  ReplayForkOption,
  ForkReplay,
  ReplayPointer,
} from './replay';

// Graph
export type {
  GraphNodeType,
  GraphEdgeRelation,
  GraphNode,
  GraphEdge,
  EntityGraph,
} from './graph';

// Presets
export type {
  WatchlistSortKey,
  WatchlistSortDir,
  WatchlistFilterConfig,
  AlertRule,
  WatchlistSavedView,
} from './presets';

// Risk
export type {
  PositionExposure,
  TimelineRiskState,
  TopRisk,
  PortfolioRiskSummary,
} from './risk';

// Launchpad
export type {
  LaunchPhase,
  LaunchCategory,
  LaunchCard,
  LaunchpadFeed,
} from './launchpad';

// Ops Board
export type {
  OpsLaneId,
  OpsCardType,
  OpsSignalTag,
  OpsCard,
  LiveNowSummary,
  OpsBoardData,
} from './opsBoard';

// Live Tape
export type {
  TapeEventType,
  EventImpact,
  TapeEvent,
} from './liveTape';
