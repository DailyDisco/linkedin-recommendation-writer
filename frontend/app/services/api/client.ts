import axios from 'axios';
import type {
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from 'axios';
import { toast } from 'sonner';
import { useAuthStore } from '../../hooks/useAuthStore';

// API base URL - proxy path for all environments
const API_BASE_URL = '/api/v1';

/**
 * Create and configure the base Axios instance
 */
function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120000, // 2 minutes for long-running GitHub analysis
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - attach auth token
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    error => Promise.reject(error)
  );

  // Response interceptor - handle common errors
  client.interceptors.response.use(
    response => response,
    error => handleResponseError(error)
  );

  return client;
}

/**
 * Get auth token from localStorage (Zustand persistence)
 * Reading directly from localStorage avoids race conditions with store hydration
 */
function getAuthToken(): string | null {
  try {
    const authStorage = localStorage.getItem('auth-storage');
    if (!authStorage) return null;

    const parsed = JSON.parse(authStorage);
    const accessToken = parsed?.state?.accessToken;
    if (!accessToken) return null;

    // Remove any extra quotes that might have been serialized
    return accessToken.replace(/^"|"$/g, '');
  } catch {
    return null;
  }
}

/**
 * Handle response errors globally
 */
function handleResponseError(error: unknown): Promise<never> {
  const axiosError = error as AxiosError;
  const status = axiosError.response?.status;
  const errorUrl = axiosError.config?.url;

  // Handle 401 - Session expired
  if (status === 401) {
    const authStore = useAuthStore.getState();
    const hasToken = !!authStore.accessToken;

    // Only redirect if user was logged in and it's not from login endpoint
    if (errorUrl && !errorUrl.endsWith('/login') && hasToken) {
      toast.error('Your session has expired. Please log in again.');
      authStore.logout();
      setTimeout(() => {
        window.location.href = '/login';
      }, 100);
    }
  }
  // Handle service unavailable
  else if (status === 502 || status === 503 || status === 504) {
    toast.error('Service temporarily unavailable. Please try again later.');
  }
  // Handle timeout
  else if (
    axiosError.code === 'ECONNABORTED' ||
    axiosError.message?.includes('timeout')
  ) {
    toast.error(
      'Request timed out. The server is taking longer than expected to respond.'
    );
  }
  // Handle network errors
  else if (!axiosError.response && axiosError.request) {
    toast.error(
      'Network error. Please check your internet connection and try again.'
    );
  }

  return Promise.reject(error);
}

// Type for Axios errors
interface AxiosError {
  response?: {
    status: number;
    data?: { detail?: string; message?: string };
  };
  request?: AxiosRequestConfig;
  message?: string;
  code?: string;
  config?: {
    url?: string;
    method?: string;
  };
}

// Export the configured client
export const api = createApiClient();
export default api;
