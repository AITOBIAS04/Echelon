/**
 * API Configuration
 * =================
 * Centralized configuration for all API endpoints.
 * Change NEXT_PUBLIC_API_URL in .env.local for deployment.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Polling intervals (in milliseconds)
export const POLL_INTERVALS = {
  FAST: 5000,      // 5s - for critical real-time data
  NORMAL: 10000,   // 10s - for markets, timelines
  SLOW: 30000,     // 30s - for stats, less critical
};

// API Endpoints
export const ENDPOINTS = {
  // Health
  HEALTH: `${API_BASE}/health`,
  
  // Markets
  MARKETS: `${API_BASE}/markets`,
  MARKETS_STATS: `${API_BASE}/markets/stats`,
  MARKETS_REFRESH: `${API_BASE}/markets/refresh`,
  MARKET_BY_ID: (id) => `${API_BASE}/markets/${id}`,
  MARKET_BET: (id) => `${API_BASE}/markets/${id}/bet`,
  
  // Timelines
  TIMELINES: `${API_BASE}/timelines`,
  TIMELINE_BY_ID: (id) => `${API_BASE}/timelines/${id}`,
  TIMELINE_SNAPSHOT: `${API_BASE}/timelines/snapshot`,
  TIMELINE_FORK: `${API_BASE}/timelines/fork`,
  TIMELINE_COMPARE: (a, b) => `${API_BASE}/timelines/${a}/compare/${b}`,
  
  // Auth
  TOKEN: `${API_BASE}/token`,
  SIGNUP: `${API_BASE}/signup`,
  USER_ME: `${API_BASE}/users/me`,
  
  // Simulation
  WORLD_STATE: `${API_BASE}/world-state`,
  AGENT_STATE: `${API_BASE}/agent-state`,
};

/**
 * Default fetcher for SWR
 * Handles JSON responses and errors
 */
export const fetcher = async (url) => {
  const res = await fetch(url);
  
  if (!res.ok) {
    const error = new Error('API request failed');
    error.status = res.status;
    try {
      error.info = await res.json();
    } catch {
      error.info = { message: res.statusText };
    }
    throw error;
  }
  
  return res.json();
};

/**
 * Authenticated fetcher for SWR
 * Includes Authorization header from localStorage
 */
export const authFetcher = async (url) => {
  const token = typeof window !== 'undefined' 
    ? localStorage.getItem('access_token') 
    : null;
  
  const headers = token 
    ? { 'Authorization': `Bearer ${token}` }
    : {};
  
  const res = await fetch(url, { headers });
  
  if (!res.ok) {
    const error = new Error('API request failed');
    error.status = res.status;
    try {
      error.info = await res.json();
    } catch {
      error.info = { message: res.statusText };
    }
    throw error;
  }
  
  return res.json();
};

/**
 * POST request helper
 * Supports both JWT and wallet authentication
 */
export const postRequest = async (url, data = {}, authenticated = false, walletAddress = null) => {
  const token = authenticated && typeof window !== 'undefined'
    ? localStorage.getItem('access_token')
    : null;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...(walletAddress && { 'X-Wallet-Address': walletAddress }),
  };
  
  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  
  const responseData = await res.json();
  
  if (!res.ok) {
    throw new Error(responseData.detail || 'Request failed');
  }
  
  return responseData;
};




