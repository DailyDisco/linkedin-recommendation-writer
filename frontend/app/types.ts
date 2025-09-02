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

export interface RepositoryInfo {
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
  owner: {
    login: string;
    avatar_url: string;
    html_url: string;
  };
}

export interface HttpError {
  response?: {
    status: number;
    data?: { detail?: string; message?: string };
  };
  request?: unknown;
  message?: string;
  code?: string;
}

export interface GitHubUserData {
  login: string;
  id: number;
  avatar_url: string;
  html_url: string;
  name?: string;
  company?: string;
  location?: string;
  email?: string;
  bio?: string;
  public_repos: number;
  public_gists: number;
  followers: number;
  following: number;
  created_at: string;
  updated_at: string;
}

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  language?: string;
  stargazers_count: number;
  forks_count: number;
  html_url: string;
  created_at: string;
  updated_at: string;
  pushed_at: string;
  size: number;
  topics?: string[];
}

export interface LanguageStats {
  language: string;
  bytes: number;
  percentage: number;
}

export interface SkillAnalysis {
  technical_skills: string[];
  frameworks: string[];
  tools: string[];
  proficiency_levels: Record<string, string>;
}

export interface CommitAnalysis {
  total_commits: number;
  recent_activity: number;
  commit_frequency: string;
  activity_trend: string;
}

export interface GitHubProfileAnalysis {
  user_data: GitHubUserData;
  repositories: GitHubRepository[];
  languages: LanguageStats[];
  skills: SkillAnalysis;
  commit_analysis: CommitAnalysis;
  analyzed_at: string;
  analysis_context_type: string;
}

export interface RepositoryContributorsResponse {
  repository: RepositoryInfo;
  contributors: ContributorInfo[];
  total_contributors: number;
  fetched_at: string;
}

export interface Recommendation {
  id: number;
  title: string;
  content: string;
  recommendation_type: string;
  tone: string;
  length: string;
  word_count: number;
  created_at: string;
  github_username: string;
  selected_option_id?: number;
  selected_option_name?: string;
  selected_option_focus?: string;
  generated_options?: RecommendationOption[];
  generation_parameters: Record<string, unknown>;
  analysis_context_type?: string;
  repository_url?: string;
}

export interface RecommendationRequest {
  github_username: string;
  recommendation_type?: string;
  tone?: string;
  length?: string;
  custom_prompt?: string;
  target_role?: string;
  specific_skills?: string[];
  include_keywords?: string[];
  exclude_keywords?: string[];
  analysis_context_type?: string;
  repository_url?: string;
}

export interface RecommendationOption {
  id: number;
  name: string;
  content: string;
  title: string;
  word_count: number;
  focus: string;
  explanation: string;
  generation_parameters: Record<string, unknown>;
}

export interface RegenerateRequest {
  original_content: string;
  refinement_instructions: string;
  github_username: string;
  recommendation_type?: string;
  tone?: string;
  length?: string;
  exclude_keywords?: string[];
}

export interface SkillMatch {
  skill: string;
  match_level: string;
  evidence: string[];
}

export interface SkillGapAnalysisResponse {
  github_username: string;
  target_role: string;
  overall_match_score: number;
  skill_analysis: SkillMatch[];
  strengths: string[];
  gaps: string[];
  recommendations: string[];
  learning_resources: string[];
  analysis_summary: string;
  generated_at: string;
}
