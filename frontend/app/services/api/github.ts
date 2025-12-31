import { api } from './client';
import type {
  GitHubProfileAnalysis,
  RepositoryContributorsResponse,
} from '../../types';

/**
 * GitHub API endpoints for profile analysis and repository data
 */
export const githubApi = {
  /**
   * Analyze a GitHub user's profile
   */
  async analyzeProfile(
    username: string,
    forceRefresh = false
  ): Promise<GitHubProfileAnalysis> {
    const response = await api.post('/github/analyze', {
      username,
      force_refresh: forceRefresh,
    });
    return response.data;
  },

  /**
   * Get background task status for long-running profile analysis
   */
  async getTaskStatus(taskId: string): Promise<{
    task_id: string;
    status: string;
    message: string;
    username?: string;
    started_at?: string;
    updated_at?: string;
    result?: GitHubProfileAnalysis;
  }> {
    const response = await api.get(`/github/task/${taskId}`);
    return response.data;
  },

  /**
   * Get contributors for a repository
   */
  async getRepositoryContributors(
    repository: string,
    maxContributors = 50,
    forceRefresh = false
  ): Promise<RepositoryContributorsResponse> {
    const response = await api.post('/github/repository/contributors', {
      repository_full_name: repository,
      max_contributors: maxContributors,
      force_refresh: forceRefresh,
    });
    return response.data;
  },

  /**
   * Check GitHub API health and rate limit status
   */
  async checkHealth(): Promise<{
    status: string;
    message: string;
    github_token_configured: boolean;
    rate_limit_remaining?: number;
    rate_limit_reset?: number;
  }> {
    const response = await api.get('/github/health');
    return response.data;
  },
};
