/**
 * Common API response types
 */

export interface ApiResponse<T = unknown> {
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
  word_count: number;
  created_at: string;
  github_username: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    perPage: number;
    total: number;
    totalPages: number;
  };
}

export interface CursorPaginatedResponse<T> {
  data: T[];
  meta: {
    nextCursor: string | null;
    hasMore: boolean;
  };
}
