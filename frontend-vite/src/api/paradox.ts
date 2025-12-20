import { apiClient } from './client';
import type { ParadoxListResponse, Paradox } from '../types';

export const paradoxApi = {
  getActiveParadoxes: async (): Promise<ParadoxListResponse> => {
    const { data } = await apiClient.get('/api/v1/paradox/active');
    return data;
  },

  getParadox: async (paradoxId: string): Promise<Paradox> => {
    const { data } = await apiClient.get(`/api/v1/paradox/${paradoxId}`);
    return data;
  },
};
