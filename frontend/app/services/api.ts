import axios from 'axios';
import type {
  GitHubProfile,
  RepositoryContributorsResponse,
  Recommendation,
  RecommendationRequest,
  RecommendationOptionsResponse,
  RecommendationOption,
  RegenerateRequest,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL ? `${API_BASE_URL}/api/v1` : '/api/v1',
  timeout: 60000, // Increased to 60 seconds for AI generation
});

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
};

export default api;
