import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Log API URL for debugging (only in development)
if (import.meta.env.DEV) {
  console.log('🔍 API URL:', API_URL);
}

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors and log for debugging
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Only log errors in development, and make them less verbose
    if (import.meta.env.DEV) {
      // Log API errors for debugging (only in dev)
      if (error.response) {
        // Server responded with error status
        console.warn(`⚠️ API Error [${error.response.status}]:`, error.config?.url);
      } else if (error.request) {
        // Request was made but no response received
        // Only log if it's not a network suspend (which happens during page unload)
        if (!error.message?.includes('ERR_NETWORK_IO_SUSPENDED')) {
          console.warn('🌐 Network Error:', error.config?.url, {
            message: error.message,
            baseURL: API_URL,
            hint: 'Check if backend is running and VITE_API_URL is set correctly'
          });
        }
      }
    }
    
    if (error.response?.status === 401) {
      // Could implement token refresh here
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
    
    return Promise.reject(error);
  }
);
