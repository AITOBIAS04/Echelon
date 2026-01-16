// ============================================
// ENUMS
// ============================================

export type AgentArchetype = 'SHARK' | 'SPY' | 'DIPLOMAT' | 'SABOTEUR' | 'WHALE' | 'DEGEN';
export type WingFlapType = 'TRADE' | 'SHIELD' | 'SABOTAGE' | 'RIPPLE' | 'PARADOX' | 'FOUNDER_YIELD';
export type StabilityDirection = 'ANCHOR' | 'DESTABILISE';
export type ParadoxStatus = 'ACTIVE' | 'EXTRACTING' | 'DETONATED' | 'RESOLVED';
export type SeverityClass = 'CLASS_1_CRITICAL' | 'CLASS_2_SEVERE' | 'CLASS_3_MODERATE' | 'CLASS_4_MINOR';

// ============================================
// WING FLAP
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
// TIMELINE
// ============================================

export interface Timeline {
  id: string;
  name: string;
  stability: number;
  surface_tension: number;
  price_yes: number;
  price_no: number;
  osint_alignment: number;
  logic_gap: number;
  gravity_score: number;
  gravity_factors: Record<string, number>;
  total_volume_usd: number;
  liquidity_depth_usd: number;
  active_agent_count: number;
  dominant_agent_id: string | null;
  dominant_agent_name: string | null;
  founder_id: string | null;
  founder_name: string | null;
  founder_yield_rate: number;
  decay_rate_per_hour: number;
  hours_until_reaper: number | null;
  has_active_paradox: boolean;
  paradox_id: string | null;
  paradox_detonation_time: string | null;
  connected_timeline_ids: string[];
  parent_timeline_id: string | null;
}

export interface TimelineHealthResponse {
  timelines: Timeline[];
  total_count: number;
}

// ============================================
// PARADOX
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
// WATCHLIST
// ============================================

export type {
  WatchlistTimeline,
  WatchlistFilter,
  WatchlistState,
} from './watchlist';

// ============================================
// TIMELINE DETAIL
// ============================================

export type {
  TimelineDetail,
  TimelineHealthSnapshot,
  ForkEvent,
  ForkOption,
  SabotageEvent,
  EvidenceEntry,
  ExtractionAttempt,
  UserPosition,
} from './timeline-detail';

// Export TimelineParadoxStatus to avoid conflict with ParadoxStatus type union
export type { ParadoxStatus as TimelineParadoxStatus } from './timeline-detail';

// ============================================
// BREACH
// ============================================

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

// ============================================
// EXPORTS
// ============================================

export type {
  ExportDatasetKind,
  ExportScope,
  ExportFilter,
  ExportJob,
  DatasetSchemaField,
  DatasetPreview,
} from './exports';

// ============================================
// REPLAY
// ============================================

export type {
  DisclosureEventType,
  DisclosureEvent,
  ForkOptionPricePath,
  ReplayForkOption,
  ForkReplay,
  ReplayPointer,
} from './replay';

// ============================================
// GRAPH
// ============================================

export type {
  GraphNodeType,
  GraphEdgeRelation,
  GraphNode,
  GraphEdge,
  EntityGraph,
} from './graph';

// ============================================
// PRESETS
// ============================================

export type {
  WatchlistSortKey,
  WatchlistSortDir,
  WatchlistFilterConfig,
  AlertRule,
  WatchlistSavedView,
} from './presets';

// ============================================
// RISK
// ============================================

export type {
  PositionExposure,
  TimelineRiskState,
  TopRisk,
  PortfolioRiskSummary,
} from './risk';
