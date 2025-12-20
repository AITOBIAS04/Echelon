import { apiClient } from './client';
import type { User, AuthResponse } from '../types';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// Re-export types for convenience
export type { User, AuthResponse };

export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const { data } = await apiClient.post('/api/v1/auth/login', credentials);
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
    }
    return data;
  },

  register: async (userData: RegisterRequest): Promise<{ user_id: string; message: string }> => {
    const response = await apiClient.post('/api/v1/auth/register', userData);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/api/v1/auth/me');
    // Map user_id to id if needed
    const data = response.data;
    return {
      id: data.user_id || data.id,
      username: data.username,
      email: data.email,
      tier: data.tier,
    };
  },

  logout: (): void => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

