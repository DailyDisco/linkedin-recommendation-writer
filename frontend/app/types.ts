export interface GitHubProfileAnalysis {
  github_username: string;
  name: string;
  avatar_url: string;
  bio: string;
  public_repos: number;
  followers: number;
  following: number;
  starred_repositories: number;
  contributions_last_year: number;
  organizations: Array<{ login: string; avatar_url: string }>;
  top_languages: Array<{ language: string; percentage: number }>;
  top_repositories: Array<{
    name: string;
    description: string;
    stargazers_count: number;
    forks_count: number;
    language: string;
    html_url: string;
  }>;
  analysis_summary: string;
  skills: {
    technical_skills: string[];
    frameworks: string[];
    tools: string[];
    domains: string[];
  };
  starred_technologies: {
    languages: Record<string, number>;
    topics: string[];
    technology_focus: Record<string, number>;
  };
  commit_analysis: {
    total_commits_analyzed: number;
    active_days: number;
    commit_frequency: Record<string, number>;
    top_keywords: string[];
    primary_strength: string;
    excellence_areas: Record<string, string>;
  };
  total_contributions: number;
  average_commits_per_day: number;
  repositories_contributed_to: number;
}

export interface RepositoryContributorsResponse {
  repository_full_name: string;
  total_contributors: number;
  contributors: Array<{
    username: string;
    avatar_url: string;
    contributions: number;
  }>;
}

export interface Recommendation {
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
  confidence_score: number;
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
  confidence_score: number;
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
