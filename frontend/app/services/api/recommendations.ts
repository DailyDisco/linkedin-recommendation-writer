import { api } from './client';
import type { Recommendation, RecommendationOption } from '../../types';
import type { RecommendationFormData } from '../../hooks/useRecommendationState';

/**
 * Recommendation generation and management API endpoints
 */
export const recommendationApi = {
  /**
   * Get all recommendations for the current user
   */
  async getAll(): Promise<Recommendation[]> {
    const response = await api.get('/recommendations/');
    return response.data.recommendations;
  },

  /**
   * Get current user details (backward compatibility)
   * @deprecated Use userApi.getCurrentUser() instead
   */
  async getUserDetails(): Promise<{
    id: number;
    email: string;
    username: string;
    full_name: string;
    is_active: boolean;
    recommendation_count: number;
    last_recommendation_date: string | null;
    daily_limit: number;
  }> {
    const response = await api.get('/users/me');
    return response.data;
  },

  /**
   * Get recommendations with filtering and pagination
   */
  async getRecommendations(params?: {
    github_username?: string;
    recommendation_type?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await api.get('/recommendations', { params });
    return response.data;
  },

  /**
   * Get a single recommendation by ID
   */
  async getById(id: number) {
    const response = await api.get(`/recommendations/${id}`);
    return response.data;
  },

  /**
   * Generate a single recommendation
   */
  async generate(data: {
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

  /**
   * Generate multiple recommendation options to choose from
   */
  async generateOptions(data: {
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

  /**
   * Create a recommendation from a selected option
   */
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

  /**
   * Regenerate/refine an existing recommendation
   */
  async regenerate(data: {
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

  /**
   * Refine keywords in a recommendation
   */
  async refineKeywords(data: {
    recommendation_id: number;
    include_keywords?: string[];
    exclude_keywords?: string[];
    refinement_instructions?: string;
  }) {
    const response = await api.post('/recommendations/refine-keywords', data);
    return response.data;
  },

  /**
   * Get prompt suggestions based on user profile
   */
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

  /**
   * Get autocomplete suggestions for form fields
   */
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

  /**
   * Chat with AI assistant for recommendation guidance
   */
  async chatWithAssistant(data: {
    github_username: string;
    conversation_history: Array<{ role: string; content: string }>;
    user_message: string;
    current_form_data: RecommendationFormData;
  }) {
    const response = await api.post('/recommendations/chat-assistant', data);
    return response.data;
  },

  /**
   * Get version history for a recommendation
   */
  async getVersionHistory(recommendationId: number) {
    const response = await api.get(
      `/recommendations/${recommendationId}/versions`
    );
    return response.data;
  },

  /**
   * Compare two versions of a recommendation
   */
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

  /**
   * Revert to a previous version
   */
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
