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
    // Log API errors for debugging
    console.error('❌ API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.message,
      baseURL: error.config?.baseURL,
    });
    
    if (error.response?.status === 401) {
      // Could implement token refresh here
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
    
    // If it's a network error (CORS, connection refused, etc.)
    if (!error.response) {
      console.error('🌐 Network Error - Check:', {
        'Is backend running?': 'Check Railway logs',
        'Is CORS configured?': 'Check backend/main.py',
        'Is VITE_API_URL set?': import.meta.env.VITE_API_URL || 'NOT SET',
        'Current API URL': API_URL,
      });
    }
    
    return Promise.reject(error);
  }
);
