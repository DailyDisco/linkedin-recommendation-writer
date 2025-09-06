import axios from 'axios';
import { toast } from 'sonner';
import type {
  GitHubProfileAnalysis,
  RepositoryContributorsResponse,
  Recommendation,
  RecommendationRequest,
  RecommendationOption,
  RegenerateRequest,
  RecommendationOptionsResponse,
} from '../types';
import type { RecommendationFormData } from '../hooks/useRecommendationState';
import type { AxiosRequestConfig } from 'axios';

// Determine API base URL based on environment
// Use proxy path for development, full URL for production
const apiBaseUrl = '/api';

// Debug logging
if (typeof window !== 'undefined') {
  console.log('API Base URL:', apiBaseUrl);
  console.log('Window location hostname:', window.location.hostname);
  console.log('Window location href:', window.location.href);
}

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 120000, // Increased to 2 minutes for long-running GitHub analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the auth token
api.interceptors.request.use(
  config => {
    // Get token from Zustand store state by reading from localStorage
    // This maintains consistency with the store while being synchronous
    const authStorage = localStorage.getItem('auth-storage');
    if (authStorage) {
      try {
        const parsed = JSON.parse(authStorage);
        const accessToken = parsed?.state?.accessToken;
        if (accessToken) {
          const cleanToken = accessToken.replace(/^"|"$/g, ''); // Ensure no extra quotes
          config.headers.Authorization = `Bearer ${cleanToken}`;
        }
      } catch (error) {
        console.error('Failed to parse auth storage:', error);
      }
    }

    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling from lib/api.ts
api.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    // Handle specific error types globally
    if (error.response?.status === 401) {
      console.log('🔐 API Interceptor: 401 error detected');
      console.log(
        '🔐 API Interceptor: Request URL:',
        (error as HttpError).config?.url || 'unknown'
      );
      console.log(
        '🔐 API Interceptor: Request method:',
        (error as HttpError).config?.method || 'unknown'
      );
      console.log('🔐 API Interceptor: Error response:', error.response);
      console.log('🔐 API Interceptor: Timestamp:', new Date().toISOString());

      // Import the auth store dynamically to avoid circular dependencies
      import('../hooks/useAuthStore')
        .then(({ useAuthStore }) => {
          const authStore = useAuthStore.getState();

          // Check if user is logged in using the Zustand store
          const hasToken = !!authStore.accessToken;
          console.log('🔐 API Interceptor: Has token:', hasToken);
          console.log(
            '🔐 API Interceptor: Token exists:',
            !!authStore.accessToken
          );

          // Only redirect to login if the error is 401, user has a token (is logged in),
          // and it's not from the login endpoint itself
          if (
            (error as HttpError).config.url &&
            !(error as HttpError).config.url.endsWith('/login') &&
            hasToken
          ) {
            console.log(
              'Global 401 interceptor: Redirecting to login for authenticated user.',
              (error as HttpError).config.url,
              (error as HttpError).response?.status
            );
            // Show toast notification before redirecting
            toast.error('Your session has expired. Please log in again.');

            console.log('🔐 API Interceptor: Calling store logout method');
            // Use the proper logout method from the store instead of directly manipulating localStorage
            authStore.logout();

            // Small delay to ensure logout completes before redirect
            setTimeout(() => {
              console.log(
                '🔐 API Interceptor: Redirecting to login after logout'
              );
              window.location.href = '/login';
            }, 100);
          } else {
            console.log(
              'Global 401 interceptor: NOT redirecting - user is anonymous or this is login endpoint.',
              error.config.url,
              error.response?.status,
              'hasToken:',
              hasToken
            );
          }
        })
        .catch(() => {
          console.error('🔐 API Interceptor: Failed to load auth store');
          // Fallback to basic localStorage handling if dynamic import fails
          const authStorage = localStorage.getItem('auth-storage');
          let hasToken = false;
          if (authStorage) {
            try {
              const parsed = JSON.parse(authStorage);
              hasToken = !!parsed?.state?.accessToken;
            } catch {
              // Ignore parsing errors
            }
          }

          console.log('🔐 API Interceptor: Fallback - hasToken:', hasToken);

          if (
            (error as HttpError).config.url &&
            !(error as HttpError).config.url.endsWith('/login') &&
            hasToken
          ) {
            console.log('🔐 API Interceptor: Fallback - redirecting to login');
            toast.error('Your session has expired. Please log in again.');
            localStorage.removeItem('auth-storage');
            window.location.href = '/login';
          }
        });
    } else if (
      error.response?.status === 503 ||
      error.response?.status === 502 ||
      error.response?.status === 504
    ) {
      // Show toast for service unavailable errors
      toast.error('Service temporarily unavailable. Please try again later.');
    } else if (
      error.code === 'ECONNABORTED' ||
      error.message?.includes('timeout')
    ) {
      // Show toast for timeout errors
      toast.error(
        'Request timed out. The server is taking longer than expected to respond.'
      );
    } else if (!error.response && error.request) {
      // Show toast for network errors
      toast.error(
        'Network error. Please check your internet connection and try again.'
      );
    }

    return Promise.reject(error);
  }
);

export const githubApi = {
  analyzeProfile: async (
    username: string,
    forceRefresh: boolean = false
  ): Promise<GitHubProfileAnalysis> => {
    const response = await api.post('/github/analyze', {
      username,
      force_refresh: forceRefresh,
    });
    return response.data;
  },

  getTaskStatus: async (
    taskId: string
  ): Promise<{
    task_id: string;
    status: string;
    message: string;
    username?: string;
    started_at?: string;
    updated_at?: string;
    result?: GitHubProfileAnalysis;
  }> => {
    const response = await api.get(`/github/task/${taskId}`);
    return response.data;
  },

  getRepositoryContributors: async (
    repository: string,
    maxContributors: number = 50,
    forceRefresh: boolean = false
  ): Promise<RepositoryContributorsResponse> => {
    const response = await api.post('/github/repository/contributors', {
      repository_full_name: repository,
      max_contributors: maxContributors,
      force_refresh: forceRefresh,
    });
    return response.data;
  },

  checkHealth: async (): Promise<{
    status: string;
    message: string;
    github_token_configured: boolean;
    rate_limit_remaining?: number;
    rate_limit_reset?: number;
  }> => {
    const response = await api.get('/github/health');
    return response.data;
  },
};

export const recommendationApi = {
  // Removed login and register as they are now in apiClient
  generate: async (request: RecommendationRequest): Promise<Recommendation> => {
    const response = await api.post('/recommendations/generate', request);
    return response.data;
  },

  generateOptions: async (
    request: RecommendationRequest
  ): Promise<RecommendationOptionsResponse> => {
    const response = await api.post(
      '/recommendations/generate-options',
      request
    );
    return response.data;
  },

  createFromOption: async (
    githubUsername: string,
    selectedOption: RecommendationOption,
    allOptions: RecommendationOption[],
    analysisType?: string,
    repositoryUrl?: string,
    recommendationType?: string,
    tone?: string,
    length?: string
  ): Promise<Recommendation> => {
    const response = await api.post('/recommendations/create-from-option', {
      github_username: githubUsername,
      selected_option: selectedOption,
      all_options: allOptions,
      analysis_context_type: analysisType || 'profile',
      repository_url: repositoryUrl,
      recommendation_type: recommendationType,
      tone: tone,
      length: length,
    });
    return response.data;
  },

  regenerate: async (request: RegenerateRequest): Promise<Recommendation> => {
    const response = await api.post('/recommendations/regenerate', request);
    return response.data;
  },

  getAll: async (): Promise<Recommendation[]> => {
    const response = await api.get('/recommendations/');
    return response.data.recommendations;
  },

  getById: async (id: number): Promise<Recommendation> => {
    const response = await api.get(`/recommendations/${id}`);
    return response.data;
  },

  getUserDetails: async (): Promise<{
    id: number;
    email: string;
    username: string;
    full_name: string;
    is_active: boolean;
    recommendation_count: number;
    last_recommendation_date: string | null;
    daily_limit: number;
  }> => {
    const response = await api.get('/users/me');
    return response.data;
  },
};

export const apiClient = {
  // Auth
  async login(credentials: { username: string; password: string }) {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  async register(userData: {
    username: string;
    email: string;
    password: string;
  }) {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  async logout() {
    const response = await api.post('/auth/logout');
    return response.data;
  },

  // Recommendations
  async generateRecommendation(data: {
    github_username: string;
    recommendation_type?: string;
    tone?: string;
    length?: string;
    custom_prompt?: string;
    target_role?: string;
    include_specific_skills?: string[];
    include_keywords?: string[];
    exclude_keywords?: string[];
  }) {
    const response = await api.post('/recommendations/generate', data);
    return response.data;
  },

  async generateRecommendationOptions(data: {
    github_username: string;
    recommendation_type?: string;
    tone?: string;
    length?: string;
    custom_prompt?: string;
    target_role?: string;
    include_specific_skills?: string[];
    include_keywords?: string[];
    exclude_keywords?: string[];
    force_refresh?: boolean;
    analysis_context_type?: string;
    repository_url?: string;
  }) {
    const response = await api.post('/recommendations/generate-options', data);
    return response.data;
  },

  async createFromOption(data: {
    github_username: string;
    selected_option: RecommendationOption;
    all_options: RecommendationOption[];
    analysis_context_type?: string;
    repository_url?: string;
    force_refresh?: boolean;
  }) {
    const response = await api.post(
      '/recommendations/create-from-option',
      data
    );
    return response.data;
  },

  async regenerateRecommendation(data: {
    original_content: string;
    refinement_instructions: string;
    github_username: string;
    recommendation_type?: string;
    tone?: string;
    length?: string;
    exclude_keywords?: string[];
    force_refresh?: boolean;
  }) {
    const response = await api.post('/recommendations/regenerate', data);
    return response.data;
  },

  async getRecommendations(params?: {
    github_username?: string;
    recommendation_type?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await api.get('/recommendations', { params });
    return response.data;
  },

  async getRecommendation(id: number) {
    const response = await api.get(`/recommendations/${id}`);
    return response.data;
  },

  // Advanced Features
  async refineKeywords(data: {
    recommendation_id: number;
    include_keywords?: string[];
    exclude_keywords?: string[];
    refinement_instructions?: string;
  }) {
    const response = await api.post('/recommendations/refine-keywords', data);
    return response.data;
  },

  // Prompt Assistant
  async getPromptSuggestions(data: {
    github_username: string;
    recommendation_type: string;
    tone: string;
    length: string;
  }) {
    const response = await api.post(
      '/recommendations/prompt-suggestions',
      data
    );
    return response.data;
  },

  async getAutocompleteSuggestions(data: {
    github_username: string;
    field_name: 'specific_skills' | 'notable_achievements';
    current_input: string;
  }): Promise<string[]> {
    const response = await api.post(
      '/recommendations/autocomplete-suggestions',
      data
    );
    return response.data;
  },

  async updateUserProfile(
    userId: number,
    data: {
      full_name?: string;
      username?: string;
      bio?: string;
      email_notifications_enabled?: boolean;
      default_tone?: string;
      language?: string;
    }
  ) {
    const response = await api.put('/users/me', data);
    return response.data;
  },

  async changePassword(data: {
    current_password: string;
    new_password: string;
  }) {
    const response = await api.put('/auth/change-password', data);
    return response.data;
  },

  async chatWithAssistant(data: {
    github_username: string;
    conversation_history: Array<{ role: string; content: string }>;
    user_message: string;
    current_form_data: RecommendationFormData;
  }) {
    console.log(
      'chatWithAssistant called with URL:',
      api.defaults.baseURL + '/recommendations/chat-assistant'
    );
    console.log('Request data:', data);
    try {
      const response = await api.post('/recommendations/chat-assistant', data);
      console.log('chatWithAssistant response:', response);
      return response.data;
    } catch (error) {
      console.error('chatWithAssistant error:', error);
      console.error(
        'Error details:',
        (error as HttpError).response?.data || (error as HttpError).message
      );
      throw error;
    }
  },

  // Version History
  async getVersionHistory(recommendationId: number) {
    const response = await api.get(
      `/recommendations/${recommendationId}/versions`
    );
    return response.data;
  },

  async compareVersions(
    recommendationId: number,
    versionA: number,
    versionB: number
  ) {
    const response = await api.get(
      `/recommendations/${recommendationId}/versions/compare?version_-id=${versionA}&version_b_id=${versionB}`
    );
    return response.data;
  },

  async revertVersion(
    recommendationId: number,
    data: {
      version_id: number;
      revert_reason?: string;
    }
  ) {
    const response = await api.post(
      `/recommendations/${recommendationId}/versions/revert`,
      data
    );
    return response.data;
  },
};

// Enhanced error types for better categorization
export enum ApiErrorType {
  NETWORK_ERROR = 'network_error',
  AUTHENTICATION_ERROR = 'authentication_error',
  AUTHORIZATION_ERROR = 'authorization_error',
  VALIDATION_ERROR = 'validation_error',
  NOT_FOUND_ERROR = 'not_found_error',
  RATE_LIMIT_ERROR = 'rate_limit_error',
  SERVER_ERROR = 'server_error',
  SERVICE_UNAVAILABLE = 'service_unavailable',
  TIMEOUT_ERROR = 'timeout_error',
  UNKNOWN_ERROR = 'unknown_error',
}

// Comprehensive error mapping with recovery suggestions
const ERROR_MAPPINGS = {
  [ApiErrorType.NETWORK_ERROR]: {
    title: 'Connection Problem',
    message:
      'Unable to connect to our servers. Please check your internet connection.',
    suggestions: [
      'Check your internet connection',
      'Try refreshing the page',
      'Wait a moment and try again',
    ],
    canRetry: true,
    showReportButton: false,
  },
  [ApiErrorType.AUTHENTICATION_ERROR]: {
    title: 'Authentication Required',
    message: 'Your session has expired or you need to log in.',
    suggestions: [
      'Log in again to continue',
      'Check if your account is active',
    ],
    canRetry: false,
    showReportButton: false,
  },
  [ApiErrorType.AUTHORIZATION_ERROR]: {
    title: 'Access Denied',
    message: "You don't have permission to perform this action.",
    suggestions: [
      'Contact your administrator',
      'Check your account permissions',
      'Try logging in with a different account',
    ],
    canRetry: false,
    showReportButton: true,
  },
  [ApiErrorType.VALIDATION_ERROR]: {
    title: 'Invalid Input',
    message: 'Please check your input and try again.',
    suggestions: [
      'Review the form fields',
      'Ensure all required fields are filled',
      'Check data formats (email, dates, etc.)',
    ],
    canRetry: true,
    showReportButton: false,
  },
  [ApiErrorType.NOT_FOUND_ERROR]: {
    title: 'Not Found',
    message: 'The requested resource could not be found.',
    suggestions: [
      'Check the URL or link',
      'Try searching for the content',
      'Go back to the previous page',
    ],
    canRetry: false,
    showReportButton: true,
  },
  [ApiErrorType.RATE_LIMIT_ERROR]: {
    title: 'Too Many Requests',
    message: "You've made too many requests. Please wait before trying again.",
    suggestions: [
      'Wait a few minutes',
      'Reduce the frequency of requests',
      'Contact support if you need higher limits',
    ],
    canRetry: true,
    showReportButton: false,
  },
  [ApiErrorType.SERVER_ERROR]: {
    title: 'Server Error',
    message: "Our servers encountered an error. We're working to fix this.",
    suggestions: [
      'Try again in a few minutes',
      'Refresh the page',
      'Contact support if the problem persists',
    ],
    canRetry: true,
    showReportButton: true,
  },
  [ApiErrorType.SERVICE_UNAVAILABLE]: {
    title: 'Service Unavailable',
    message: 'The service is temporarily unavailable. Please try again later.',
    suggestions: [
      'Check our status page',
      'Try again in 10-15 minutes',
      'Contact support for urgent issues',
    ],
    canRetry: true,
    showReportButton: true,
  },
  [ApiErrorType.TIMEOUT_ERROR]: {
    title: 'Request Timeout',
    message: 'The request took too long to complete.',
    suggestions: [
      'Check your internet connection',
      'Try again with less data',
      'Contact support if this persists',
    ],
    canRetry: true,
    showReportButton: true,
  },
  [ApiErrorType.UNKNOWN_ERROR]: {
    title: 'Unexpected Error',
    message: 'An unexpected error occurred. Our team has been notified.',
    suggestions: [
      'Try refreshing the page',
      'Clear your browser cache',
      'Contact support if this continues',
    ],
    canRetry: true,
    showReportButton: true,
  },
};

/**
 * Determine error type based on HTTP status and error details
 */
function determineErrorType(status: number, error: HttpError): ApiErrorType {
  const data = error.response?.data;
  const message = data?.detail || data?.message || error.message || '';

  // Network errors
  if (status === 0 || !error.response) {
    return ApiErrorType.NETWORK_ERROR;
  }

  // Authentication/Authorization
  if (status === 401) {
    return ApiErrorType.AUTHENTICATION_ERROR;
  }
  if (status === 403) {
    return ApiErrorType.AUTHORIZATION_ERROR;
  }

  // Client errors
  if (status === 400) {
    return ApiErrorType.VALIDATION_ERROR;
  }
  if (status === 404) {
    return ApiErrorType.NOT_FOUND_ERROR;
  }
  if (status === 429) {
    return ApiErrorType.RATE_LIMIT_ERROR;
  }

  // Server errors
  if (status >= 500) {
    if (status === 502 || status === 503 || status === 504) {
      return ApiErrorType.SERVICE_UNAVAILABLE;
    }
    return ApiErrorType.SERVER_ERROR;
  }

  // Timeout detection
  if (
    message.toLowerCase().includes('timeout') ||
    error.code === 'ECONNABORTED'
  ) {
    return ApiErrorType.TIMEOUT_ERROR;
  }

  return ApiErrorType.UNKNOWN_ERROR;
}

/**
 * Enhanced API error handler with comprehensive mapping and recovery suggestions
 */
export const handleApiError = (
  error: unknown,
  options: {
    showToast?: boolean;
    showRecoverySuggestions?: boolean;
    context?: string;
    onRetry?: () => void;
  } = {}
) => {
  const { showToast = true, context = '', onRetry } = options;

  let errorType: ApiErrorType;
  let status = -1;
  let errorData: unknown = null;

  if ((error as HttpError).response) {
    // Server responded with error status
    const httpError = error as HttpError;
    const { status: responseStatus, data } = httpError.response!;
    status = responseStatus;
    errorData = data;
    errorType = determineErrorType(status, httpError);
  } else if ((error as HttpError).request) {
    // Network error
    errorType = ApiErrorType.NETWORK_ERROR;
    status = 0;
  } else {
    // Other error
    errorType = ApiErrorType.UNKNOWN_ERROR;
    status = -1;
  }

  const errorMapping = ERROR_MAPPINGS[errorType];
  const errorId = `api_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Log structured error information
  console.group(`🚨 API Error - ${context || 'Unknown Context'}`);
  console.error('Error ID:', errorId);
  console.error('Type:', errorType);
  console.error('Status:', status);
  console.error('Message:', (error as HttpError)?.message || 'Unknown error');
  console.error('Data:', errorData);
  console.error('Timestamp:', new Date().toISOString());
  console.groupEnd();

  // Show toast notification
  if (showToast) {
    const toastMessage = errorMapping.message;

    if (errorMapping.canRetry && onRetry) {
      toast.error(toastMessage, {
        description: errorMapping.title,
        action: {
          label: 'Retry',
          onClick: onRetry,
        },
        duration: 8000,
      });
    } else {
      toast.error(toastMessage, {
        description: errorMapping.title,
        duration: 6000,
      });
    }
  }

  return {
    type: errorType,
    status,
    message: errorMapping.message,
    title: errorMapping.title,
    suggestions: errorMapping.suggestions,
    canRetry: errorMapping.canRetry,
    showReportButton: errorMapping.showReportButton,
    errorId,
    data: errorData,
    originalError: error,
  };
};

/**
 * Legacy function for backward compatibility
 * @deprecated Use handleApiError with options object instead
 */
export const handleApiErrorLegacy = (
  error: unknown,
  showToast: boolean = true
) => {
  return handleApiError(error, { showToast });
};

// Types for API responses
export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  message?: string;
}

export interface HttpError {
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

export interface RecommendationResponse {
  id: number;
  title: string;
  content: string;
  recommendation_type: string;
  tone: string;
  length: string;
  word_count: number;
  created_at: string;
  github_username: string;
}

export default api;
