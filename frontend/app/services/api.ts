import axios from 'axios';
import type {
  GitHubProfile,
  RepositoryContributorsResponse,
  Recommendation,
  RecommendationRequest,
  RecommendationOption,
  RegenerateRequest,
  MultiContributorData, // Added for new API functions
} from '../types';

const API_BASE_URL =
  import.meta.env.NEXT_PUBLIC_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  '';

const api = axios.create({
  baseURL: API_BASE_URL ? `${API_BASE_URL}/api/v1` : '/api/v1',
  timeout: 60000, // Increased to 60 seconds for AI generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the auth token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('accessToken'); // Standardizing on 'accessToken'
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log(
        'Sending Authorization header:',
        config.headers.Authorization
      ); // Added for debugging
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling from lib/api.ts
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('accessToken'); // Standardizing on 'accessToken'
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const githubApi = {
  analyzeProfile: async (username: string): Promise<GitHubProfile> => {
    const response = await api.post('/github/analyze', {
      github_username: username,
    });
    return response.data;
  },

  getRepositoryContributors: async (
    repository: string,
    maxContributors: number = 50
  ): Promise<RepositoryContributorsResponse> => {
    const response = await api.post('/github/repository/contributors', {
      repository_name: repository,
      max_contributors: maxContributors,
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
    repositoryUrl?: string
  ): Promise<Recommendation> => {
    const response = await api.post('/recommendations/create-from-option', {
      github_username: githubUsername,
      selected_option: selectedOption,
      all_options: allOptions,
      analysis_type: analysisType || 'profile',
      repository_url: repositoryUrl,
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

  async generateReadme(data: {
    repository_full_name: string;
    style?: string;
    include_sections?: string[];
    target_audience?: string;
  }) {
    const response = await api.post('/recommendations/generate-readme', data);
    return response.data;
  },

  async analyzeSkillGaps(data: {
    github_username: string;
    target_role: string;
    industry?: string;
    experience_level?: string;
  }) {
    const response = await api.post(
      '/recommendations/analyze-skill-gaps',
      data
    );
    return response.data;
  },

  async generateMultiContributor(data: MultiContributorData) {
    const response = await api.post(
      '/recommendations/generate-multi-contributor',
      data
    );
    return response.data;
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

export const handleApiError = (error: any) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    return {
      status,
      message: data.detail || data.message || 'An error occurred',
      data: data,
    };
  } else if (error.request) {
    // Network error
    return {
      status: 0,
      message: 'Network error - please check your connection',
      data: null,
    };
  } else {
    // Other error
    return {
      status: -1,
      message: error.message || 'An unexpected error occurred',
      data: null,
    };
  }
};

// Types for API responses
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  message?: string;
}

export interface RecommendationResponse {
  id: number;
  title: string;
  content: string;
  recommendation_type: string;
  tone: string;
  length: string;
  confidence_score: number;
  word_count: number;
  created_at: string;
  github_username: string;
}

// Merged and updated RecommendationOptionsResponse
export interface RecommendationOptionsResponse {
  options: Array<{
    id: number;
    name: string;
    content: string;
    title: string;
    word_count: number;
    focus: string;
    confidence_score: number;
    explanation: string;
  }>;
  generation_parameters: any;
}

export default api;
