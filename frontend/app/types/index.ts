export interface GitHubUserData {
  github_username?: string;
  login?: string;
  github_id?: number;
  id?: number;
  full_name?: string;
  name?: string;
  bio?: string;
  company?: string;
  location?: string;
  email?: string;
  blog?: string;
  avatar_url?: string;
  public_repos?: number;
  followers?: number;
  following?: number;
  public_gists?: number;
}

export interface GitHubProfileAnalysis {
  user_data: GitHubUserData;
  repositories: Repository[];
  languages: LanguageStats[];
  skills: SkillAnalysis;
  commit_analysis: Record<string, unknown>;
  analyzed_at: string;
  analysis_context_type: string;
}

// Keep the old interface for backward compatibility, but mark as deprecated
/** @deprecated Use GitHubProfileAnalysis instead */
export interface GitHubProfile {
  github_username: string;
  github_id: number;
  full_name?: string;
  bio?: string;
  company?: string;
  location?: string;
  email?: string;
  blog?: string;
  avatar_url?: string;
  public_repos: number;
  followers: number;
  following: number;
  public_gists: number;
  repositories: Repository[];
  languages: LanguageStats[];
  skills: SkillAnalysis;
  last_analyzed: string;
}

export interface Repository {
  name: string;
  description?: string;
  language?: string;
  stars: number;
  forks: number;
  size: number;
  created_at: string;
  updated_at: string;
  topics: string[];
  url: string;
}

export interface LanguageStats {
  language: string;
  percentage: number;
  lines_of_code: number;
  repository_count: number;
}

export interface SkillAnalysis {
  technical_skills: string[];
  frameworks: string[];
  tools: string[];
  domains: string[];
  soft_skills: string[];
}

export interface RecommendationRequest {
  github_username: string;
  recommendation_type:
    | 'professional'
    | 'technical'
    | 'leadership'
    | 'academic'
    | 'personal';
  tone: 'professional' | 'friendly' | 'formal' | 'casual';
  length: 'short' | 'medium' | 'long';
  custom_prompt?: string;
  include_specific_skills?: string[];
  target_role?: string;
  analysis_type?: 'profile' | 'repo_only';
  repository_url?: string;
}

export interface Recommendation {
  id: number;
  title: string;
  content: string;
  recommendation_type: string;
  tone: string;
  length: string;
  word_count: number;
  ai_model: string;
  generation_parameters?: Record<string, unknown>;
  selected_option_id?: number;
  selected_option_name?: string;
  selected_option_focus?: string;
  created_at: string;
  updated_at: string;
  github_username?: string;
}

export interface KeywordRefinementResult {
  id: number;
  refined_content: string;
  refined_title: string;
  word_count: number;
  include_keywords_used?: string[];
  exclude_keywords_avoided?: string[];
  refinement_summary?: string;
  validation_issues?: string[];
  generation_parameters?: Record<string, unknown>;
}

// HTTP Error types for axios/fetch error handling
export interface HttpError {
  response?: {
    status: number;
    statusText: string;
    data?: {
      detail?: string;
      message?: string;
    };
  };
  code?: string;
  message?: string;
}

// Repository information types
export interface RepositoryInfo {
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  open_issues_count: number;
  created_at: string;
  updated_at: string;
  topics: string[];
  owner: {
    login: string;
    avatar_url: string;
    html_url: string;
  };
}

// Debug URL parsing types
export interface UrlParseResult {
  type: 'user' | 'repository';
  value: string;
  valid: boolean;
}

export interface RecommendationOption {
  id: number;
  name: string;
  content: string;
  title: string;
  word_count: number;
  focus: string;
}

export interface RecommendationOptionsResponse {
  options: RecommendationOption[];
  generation_parameters?: Record<string, unknown>;
  generation_prompt?: string;
}

export interface RegenerateRequest {
  original_content: string;
  refinement_instructions: string;
  github_username: string;
  recommendation_type?: RecommendationRequest['recommendation_type'];
  tone?: RecommendationRequest['tone'];
  length?: RecommendationRequest['length'];
}

export interface RecommendationListResponse {
  recommendations: Recommendation[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  detail: string;
  status?: number;
}

export interface LoadingState {
  isLoading: boolean;
  error?: string | null;
}

// Repository Contributors types
export interface ContributorInfo {
  username: string;
  full_name: string;
  first_name: string;
  last_name: string;
  email?: string;
  bio?: string;
  company?: string;
  location?: string;
  avatar_url: string;
  contributions: number;
  profile_url: string;
  followers: number;
  public_repos: number;
}

export interface SimpleRepositoryInfo {
  name: string;
  full_name: string;
  description?: string;
  language?: string;
  stars: number;
  forks: number;
  url: string;
  topics: string[];
  created_at?: string;
  updated_at?: string;
  owner?: {
    login: string;
    avatar_url?: string;
    html_url?: string;
  };
}

export interface RepositoryContributorsResponse {
  repository: SimpleRepositoryInfo;
  contributors: ContributorInfo[];
  total_contributors: number;
  fetched_at: string;
}

// Form types
export interface GenerateFormData {
  github_username: string;
  recommendation_type: RecommendationRequest['recommendation_type'];
  tone: RecommendationRequest['tone'];
  length: RecommendationRequest['length'];
  custom_prompt: string;
  target_role: string;
  include_specific_skills: string;
  analysis_type: 'profile' | 'repo_only';
  repository_url?: string;
}

// GitHub URL parsing utilities
export interface ParsedGitHubInput {
  type: 'username' | 'repo_url';
  username: string;
  repository?: string;
  fullUrl?: string;
}

// Enhanced UI types for better type safety
export interface UIState {
  isLoading: boolean;
  error: string | null;
  success: boolean;
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

export interface SortState {
  field: string;
  direction: 'asc' | 'desc';
}

export interface FilterState {
  query: string;
  type?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
}

export interface ReadmeGenerationData {
  repository_full_name: string;
  style?: string;
  include_sections?: string[];
  target_audience?: string;
}

export interface SkillAnalysisData {
  github_username: string;
  target_role: string;
  industry?: string;
  experience_level?: string;
}
