import { apiClient } from './client';
import type { WingFlapFeedResponse, TimelineHealthResponse, Timeline } from '../types';

/**
 * Mock data for development when backend is not available
 */
const MOCK_WING_FLAPS: WingFlapFeedResponse = {
  flaps: [
    {
      id: 'flap_001',
      agent_name: 'WHALE_ALPHA',
      agent_archetype: 'WHALE',
      timeline_id: 'tl_oil_hormuz_001',
      timeline_name: 'Oil Crisis - Hormuz Strait',
      action: 'ANCHOR',
      direction: 'ANCHOR',
      flap_type: 'SHIELD',
      volume_usd: 50000,
      stability_delta: 2.5,
      spawned_ripple: false,
      timestamp: new Date().toISOString(),
      agent_id: 'agent_whale_001',
      timeline_stability: 54.7,
      timeline_price: 0.65,
      ripple_timeline_id: null,
      founder_id: null,
      founder_yield_earned: null,
    },
    {
      id: 'flap_002',
      agent_name: 'SHARK_BETA',
      agent_archetype: 'SHARK',
      timeline_id: 'tl_fed_rate_jan26',
      timeline_name: 'Fed Rate Decision - Jan 2026',
      action: 'DESTABILISE',
      direction: 'DESTABILISE',
      flap_type: 'SABOTAGE',
      volume_usd: 23000,
      stability_delta: -3.2,
      spawned_ripple: true,
      timestamp: new Date(Date.now() - 300000).toISOString(),
      agent_id: 'agent_shark_001',
      timeline_stability: 89.2,
      timeline_price: 0.88,
      ripple_timeline_id: 'tl_fed_rate_fork_001',
      founder_id: null,
      founder_yield_earned: null,
    },
    {
      id: 'flap_003',
      agent_name: 'DIPLOMAT_GAMMA',
      agent_archetype: 'DIPLOMAT',
      timeline_id: 'tl_tech_reg_001',
      timeline_name: 'Tech Regulation - EU AI Act',
      action: 'ANCHOR',
      direction: 'ANCHOR',
      flap_type: 'SHIELD',
      volume_usd: 15000,
      stability_delta: 1.8,
      spawned_ripple: false,
      timestamp: new Date(Date.now() - 600000).toISOString(),
      agent_id: 'agent_diplomat_001',
      timeline_stability: 55.8,
      timeline_price: 0.52,
      ripple_timeline_id: null,
      founder_id: null,
      founder_yield_earned: null,
    },
    {
      id: 'flap_004',
      agent_name: 'SABOTEUR_DELTA',
      agent_archetype: 'SABOTEUR',
      timeline_id: 'tl_oil_hormuz_001',
      timeline_name: 'Oil Crisis - Hormuz Strait',
      action: 'DESTABILISE',
      direction: 'DESTABILISE',
      flap_type: 'SABOTAGE',
      volume_usd: 18000,
      stability_delta: -1.5,
      spawned_ripple: false,
      timestamp: new Date(Date.now() - 900000).toISOString(),
      agent_id: 'agent_saboteur_001',
      timeline_stability: 54.7,
      timeline_price: 0.63,
      ripple_timeline_id: null,
      founder_id: null,
      founder_yield_earned: null,
    },
    {
      id: 'flap_005',
      agent_name: 'WHALE_ALPHA',
      agent_archetype: 'WHALE',
      timeline_id: 'tl_ghost_tanker',
      timeline_name: 'Ghost Tanker Tracker',
      action: 'ANCHOR',
      direction: 'ANCHOR',
      flap_type: 'PARADOX',
      volume_usd: 120000,
      stability_delta: 8.5,
      spawned_ripple: true,
      timestamp: new Date(Date.now() - 1200000).toISOString(),
      agent_id: 'agent_whale_001',
      timeline_stability: 72.3,
      timeline_price: 0.75,
      ripple_timeline_id: 'tl_ghost_tanker_fork_001',
      founder_id: null,
      founder_yield_earned: null,
    },
  ] as any,
  total_count: 5,
  has_more: false,
};

const MOCK_TIMELINES: TimelineHealthResponse = {
  timelines: [
    {
      id: 'tl_oil_hormuz_001',
      name: 'Oil Crisis - Hormuz Strait',
      image_url: 'https://images.unsplash.com/photo-1518457683858-667fcf3a9a3c?w=80&h=80&fit=crop',
      stability: 54.7,
      surface_tension: 0.45,
      price_yes: 0.65,
      price_no: 0.35,
      osint_alignment: 68,
      logic_gap: 0.42,
      gravity_score: 85,
      gravity_factors: { 'oil': 0.85, 'geopolitics': 0.72, 'shipping': 0.68 },
      total_volume_usd: 450000,
      liquidity_depth_usd: 125000,
      active_agent_count: 12,
      dominant_agent_id: 'agent_whale_001',
      dominant_agent_name: 'WHALE_ALPHA',
      founder_id: null,
      founder_name: null,
      founder_yield_rate: 0.02,
      decay_rate_per_hour: 2.1,
      hours_until_reaper: 48,
      has_active_paradox: true,
      paradox_id: 'paradox_001',
      paradox_detonation_time: new Date(Date.now() + 172800000).toISOString(),
      connected_timeline_ids: [],
      parent_timeline_id: null,
    },
    {
      id: 'tl_fed_rate_jan26',
      name: 'Fed Rate Decision - Jan 2026',
      image_url: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=80&h=80&fit=crop',
      stability: 89.2,
      surface_tension: 0.15,
      price_yes: 0.88,
      price_no: 0.12,
      osint_alignment: 92,
      logic_gap: 0.08,
      gravity_score: 45,
      gravity_factors: { 'fed': 0.45, 'economy': 0.38 },
      total_volume_usd: 320000,
      liquidity_depth_usd: 95000,
      active_agent_count: 8,
      dominant_agent_id: null,
      dominant_agent_name: null,
      founder_id: null,
      founder_name: null,
      founder_yield_rate: 0.02,
      decay_rate_per_hour: 0.5,
      hours_until_reaper: 120,
      has_active_paradox: false,
      paradox_id: null,
      paradox_detonation_time: null,
      connected_timeline_ids: [],
      parent_timeline_id: null,
    },
    {
      id: 'tl_tech_reg_001',
      name: 'Tech Regulation - EU AI Act',
      image_url: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=80&h=80&fit=crop',
      stability: 55.8,
      surface_tension: 0.52,
      price_yes: 0.52,
      price_no: 0.48,
      osint_alignment: 52,
      logic_gap: 0.60,
gravity_score: 72,
      gravity_factors: { 'ai': 0.72, 'regulation': 0.65, 'eu': 0.48 },
      total_volume_usd: 280000,
      liquidity_depth_usd: 85000,
      active_agent_count: 15,
      dominant_agent_id: null,
      dominant_agent_name: null,
      founder_id: null,
      founder_name: null,
      founder_yield_rate: 0.02,
      decay_rate_per_hour: 1.8,
      hours_until_reaper: 72,
      has_active_paradox: false,
      paradox_id: null,
      paradox_detonation_time: null,
      connected_timeline_ids: [],
      parent_timeline_id: null,
    },
    {
      id: 'tl_ghost_tanker',
      name: 'Ghost Tanker Tracker',
      image_url: 'https://images.unsplash.com/photo-1591076482161-42ce6d7a4610?w=80&h=80&fit=crop',
      stability: 72.3,
      surface_tension: 0.38,
      price_yes: 0.75,
      price_no: 0.25,
      osint_alignment: 78,
      logic_gap: 0.28,
      gravity_score: 88,
      gravity_factors: { 'shipping': 0.88, 'oil': 0.75, 'satellite': 0.62 },
      total_volume_usd: 180000,
      liquidity_depth_usd: 55000,
      active_agent_count: 6,
      dominant_agent_id: 'agent_whale_001',
      dominant_agent_name: 'WHALE_ALPHA',
      founder_id: null,
      founder_name: null,
      founder_yield_rate: 0.02,
      decay_rate_per_hour: 1.2,
      hours_until_reaper: 96,
      has_active_paradox: true,
      paradox_id: 'paradox_002',
      paradox_detonation_time: new Date(Date.now() + 345600000).toISOString(),
      connected_timeline_ids: ['tl_oil_hormuz_001'],
      parent_timeline_id: null,
    },
    {
      id: 'tl_cyber_attack_q1',
      name: 'Cyber Attack - Q1 2026',
      image_url: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=80&h=80&fit=crop',
      stability: 65.2,
      surface_tension: 0.42,
      price_yes: 0.58,
      price_no: 0.42,
      osint_alignment: 58,
      logic_gap: 0.35,
      gravity_score: 55,
      gravity_factors: { 'cyber': 0.55, 'security': 0.48 },
      total_volume_usd: 220000,
      liquidity_depth_usd: 68000,
      active_agent_count: 9,
      dominant_agent_id: null,
      dominant_agent_name: null,
      founder_id: null,
      founder_name: null,
      founder_yield_rate: 0.02,
      decay_rate_per_hour: 1.5,
      hours_until_reaper: 84,
      has_active_paradox: false,
      paradox_id: null,
      paradox_detonation_time: null,
      connected_timeline_ids: [],
      parent_timeline_id: null,
    },
  ] as any,
  total_count: 5,
};

export const butterflyApi = {
  getWingFlaps: async (params?: {
    timeline_id?: string;
    agent_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<WingFlapFeedResponse> => {
    try {
      const { data } = await apiClient.get('/api/v1/butterfly/wing-flaps', { params });
      return data;
    } catch (error) {
      // Return mock data if API fails
      console.warn('Using mock wing flaps data (API unavailable)');
      return MOCK_WING_FLAPS;
    }
  },

  getTimelineHealth: async (params?: {
    sort_by?: string;
    sort_order?: string;
    limit?: number;
  }): Promise<TimelineHealthResponse> => {
    try {
      const { data } = await apiClient.get('/api/v1/butterfly/timelines/health', { params });
      return data;
    } catch (error) {
      // Return mock data if API fails
      console.warn('Using mock timeline health data (API unavailable)');
      return MOCK_TIMELINES;
    }
  },

  getTimeline: async (timelineId: string): Promise<Timeline> => {
    try {
      const { data } = await apiClient.get(`/api/v1/butterfly/timelines/${timelineId}/health`);
      return data;
    } catch (error) {
      // Try to find in mock data
      const mockTimeline = MOCK_TIMELINES.timelines.find((t: any) => t.id === timelineId);
      if (mockTimeline) {
        return mockTimeline;
      }
      throw error;
    }
  },
};
