import { apiClient } from './client';
import type { WingFlapFeedResponse, TimelineHealthResponse, Timeline } from '../types';

export const butterflyApi = {
  getWingFlaps: async (params?: {
    timeline_id?: string;
    agent_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<WingFlapFeedResponse> => {
    const { data } = await apiClient.get('/api/v1/butterfly/wing-flaps', { params });
    return data;
  },

  getTimelineHealth: async (params?: {
    sort_by?: string;
    sort_order?: string;
    limit?: number;
  }): Promise<TimelineHealthResponse> => {
    const { data } = await apiClient.get('/api/v1/butterfly/timelines/health', { params });
    return data;
  },

  getTimeline: async (timelineId: string): Promise<Timeline> => {
    const { data } = await apiClient.get(`/api/v1/butterfly/timelines/${timelineId}/health`);
    return data;
  },
};
