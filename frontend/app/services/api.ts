/**
 * API Service - Re-export for backward compatibility
 *
 * This file maintains backward compatibility with existing imports.
 * New code should import from '@/services/api/' directly.
 *
 * @example
 * // Legacy import (still works)
 * import { githubApi, apiClient, billingApi } from '../services/api';
 *
 * // New preferred import
 * import { githubApi } from '../services/api/github';
 * import { authApi } from '../services/api/auth';
 */

// Re-export everything from the new modular structure
export {
  api,
  apiClient,
  authApi,
  userApi,
  githubApi,
  recommendationApi,
  billingApi,
  ApiErrorType,
  handleApiError,
  handleApiErrorLegacy,
  type HttpError,
  type ApiErrorResult,
  type ApiResponse,
  type RecommendationResponse,
} from './api/index';

// Default export
export { default } from './api/index';
