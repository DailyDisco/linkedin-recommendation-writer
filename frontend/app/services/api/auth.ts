import { api } from './client';

/**
 * Authentication API endpoints
 */
export const authApi = {
  /**
   * Login with username/password
   */
  async login(credentials: { username: string; password: string }) {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  /**
   * Register a new user
   */
  async register(userData: {
    username: string;
    email: string;
    password: string;
  }) {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  /**
   * Logout current user
   */
  async logout() {
    const response = await api.post('/auth/logout');
    return response.data;
  },

  /**
   * Change user password
   */
  async changePassword(data: {
    current_password: string;
    new_password: string;
  }) {
    const response = await api.put('/auth/change-password', data);
    return response.data;
  },
};

/**
 * User profile API endpoints
 */
export const userApi = {
  /**
   * Get current user details
   */
  async getCurrentUser(): Promise<{
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
   * Update user profile
   */
  async updateProfile(data: {
    full_name?: string;
    username?: string;
    bio?: string;
    email_notifications_enabled?: boolean;
    default_tone?: string;
    language?: string;
  }) {
    const response = await api.put('/users/me', data);
    return response.data;
  },
};
