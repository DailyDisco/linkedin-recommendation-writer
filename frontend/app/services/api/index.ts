/**
 * API Service - Domain-specific modules
 *
 * This barrel file re-exports all API modules for convenient imports.
 * For backward compatibility, it also exports combined objects that
 * mirror the original api.ts structure.
 */

// Export domain-specific APIs
export { api } from './client';
export { authApi, userApi } from './auth';
export { githubApi } from './github';
export { recommendationApi } from './recommendations';
export { billingApi } from './billing';

// Export error handling utilities
export {
  ApiErrorType,
  handleApiError,
  handleApiErrorLegacy,
  type HttpError,
  type ApiErrorResult,
} from './errors';

// Re-export types for convenience
export type { ApiResponse, RecommendationResponse } from './types';

// ========== Backward Compatibility ==========

// Combined apiClient for existing code that uses apiClient.methodName()
import { authApi, userApi } from './auth';
import { recommendationApi } from './recommendations';

export const apiClient = {
  // Auth
  login: authApi.login,
  register: authApi.register,
  logout: authApi.logout,
  changePassword: authApi.changePassword,

  // User
  updateUserProfile: (
    _userId: number,
    data: Parameters<typeof userApi.updateProfile>[0]
  ) => userApi.updateProfile(data),

  // Recommendations
  generateRecommendation: recommendationApi.generate,
  generateRecommendationOptions: recommendationApi.generateOptions,
  createFromOption: recommendationApi.createFromOption,
  regenerateRecommendation: recommendationApi.regenerate,
  getRecommendations: recommendationApi.getRecommendations,
  getRecommendation: recommendationApi.getById,
  refineKeywords: recommendationApi.refineKeywords,
  getPromptSuggestions: recommendationApi.getPromptSuggestions,
  getAutocompleteSuggestions: recommendationApi.getAutocompleteSuggestions,
  chatWithAssistant: recommendationApi.chatWithAssistant,
  getVersionHistory: recommendationApi.getVersionHistory,
  compareVersions: recommendationApi.compareVersions,
  revertVersion: recommendationApi.revertVersion,
};

// Default export for simple imports
import { api } from './client';
export default api;
