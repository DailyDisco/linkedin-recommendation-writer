import axios from 'axios';

// Configure axios instance
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const apiEndpoints = {
  // Auth
  login: '/auth/login',
  register: '/auth/register',
  logout: '/auth/logout',

  // Recommendations
  generateRecommendation: '/recommendations/generate',
  generateRecommendationOptions: '/recommendations/generate-options',
  createFromOption: '/recommendations/create-from-option',
  regenerateRecommendation: '/recommendations/regenerate',
  getRecommendations: '/recommendations',
  getRecommendation: (id: number) => `/recommendations/${id}`,

  // Advanced Features
  refineKeywords: '/recommendations/refine-keywords',
  generateReadme: '/recommendations/generate-readme',
  analyzeSkillGaps: '/recommendations/analyze-skill-gaps',
  generateMultiContributor: '/recommendations/generate-multi-contributor',

  // Version History
  getVersionHistory: (id: number) => `/recommendations/${id}/versions`,
  compareVersions: (id: number, versionA: number, versionB: number) =>
    `/recommendations/${id}/versions/compare?version_a_id=${versionA}&version_b_id=${versionB}`,
  revertVersion: (id: number) => `/recommendations/${id}/versions/revert`,
};

// API functions
export const apiClient = {
  // Auth
  async login(credentials: { username: string; password: string }) {
    const response = await api.post(apiEndpoints.login, credentials);
    return response.data;
  },

  async register(userData: {
    username: string;
    email: string;
    password: string;
  }) {
    const response = await api.post(apiEndpoints.register, userData);
    return response.data;
  },

  async logout() {
    const response = await api.post(apiEndpoints.logout);
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
    const response = await api.post(apiEndpoints.generateRecommendation, data);
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
    const response = await api.post(
      apiEndpoints.generateRecommendationOptions,
      data
    );
    return response.data;
  },

  async createFromOption(data: {
    github_username: string;
    selected_option: any;
    all_options: any[];
    analysis_context_type?: string;
    repository_url?: string;
  }) {
    const response = await api.post(apiEndpoints.createFromOption, data);
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
    const response = await api.post(
      apiEndpoints.regenerateRecommendation,
      data
    );
    return response.data;
  },

  async getRecommendations(params?: {
    github_username?: string;
    recommendation_type?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await api.get(apiEndpoints.getRecommendations, { params });
    return response.data;
  },

  async getRecommendation(id: number) {
    const response = await api.get(apiEndpoints.getRecommendation(id));
    return response.data;
  },

  // Advanced Features
  async refineKeywords(data: {
    recommendation_id: number;
    include_keywords?: string[];
    exclude_keywords?: string[];
    refinement_instructions?: string;
  }) {
    const response = await api.post(apiEndpoints.refineKeywords, data);
    return response.data;
  },

  async generateReadme(data: {
    repository_full_name: string;
    style?: string;
    include_sections?: string[];
    target_audience?: string;
  }) {
    const response = await api.post(apiEndpoints.generateReadme, data);
    return response.data;
  },

  async analyzeSkillGaps(data: {
    github_username: string;
    target_role: string;
    industry?: string;
    experience_level?: string;
  }) {
    const response = await api.post(apiEndpoints.analyzeSkillGaps, data);
    return response.data;
  },

  async generateMultiContributor(data: {
    repository_full_name: string;
    max_contributors?: number;
    min_contributions?: number;
    focus_areas?: string[];
    recommendation_type?: string;
    tone?: string;
    length?: string;
  }) {
    const response = await api.post(
      apiEndpoints.generateMultiContributor,
      data
    );
    return response.data;
  },

  // Version History
  async getVersionHistory(recommendationId: number) {
    const response = await api.get(
      apiEndpoints.getVersionHistory(recommendationId)
    );
    return response.data;
  },

  async compareVersions(
    recommendationId: number,
    versionA: number,
    versionB: number
  ) {
    const response = await api.get(
      apiEndpoints.compareVersions(recommendationId, versionA, versionB)
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
      apiEndpoints.revertVersion(recommendationId),
      data
    );
    return response.data;
  },
};

// Error handling utilities
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
