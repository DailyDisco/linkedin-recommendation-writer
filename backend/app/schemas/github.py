"""GitHub-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GitHubAnalysisRequest(BaseModel):
    """Request schema for GitHub profile analysis."""

    username: str = Field(..., description="GitHub username to analyze")
    force_refresh: bool = Field(False, description="Force refresh of cached data")


class RepositoryAnalysisRequest(BaseModel):
    """Request schema for GitHub repository analysis."""

    repository_full_name: str = Field(..., description="Full name of the repository (owner/repo)")
    force_refresh: bool = Field(False, description="Force refresh of cached data")


class RepositoryContributorsRequest(BaseModel):
    """Request schema for GitHub repository contributors analysis."""

    repository_full_name: str = Field(..., description="Full name of the repository (owner/repo)")
    max_contributors: int = Field(50, ge=1, le=100, description="Maximum number of contributors to return")
    force_refresh: bool = Field(False, description="Force refresh of cached data")


class RepositoryInfo(BaseModel):
    """Repository information schema."""

    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    size: int = 0
    created_at: datetime
    updated_at: datetime
    topics: List[str] = []
    url: str


class ContributorInfo(BaseModel):
    """Contributor information schema."""

    login: str
    id: int
    contributions: int
    avatar_url: Optional[str] = None


class LanguageStats(BaseModel):
    """Programming language statistics schema."""

    language: str
    percentage: float
    lines_of_code: int
    repository_count: int


class SkillAnalysis(BaseModel):
    """Skill analysis schema."""

    technical_skills: List[str] = []
    frameworks: List[str] = []
    tools: List[str] = []
    domains: List[str] = []
    soft_skills: List[str] = []


class GitHubProfileResponse(BaseModel):
    """Response schema for GitHub profile data."""

    # Basic profile info
    github_username: str
    github_id: int
    full_name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    blog: Optional[str] = None
    avatar_url: Optional[str] = None

    # GitHub statistics
    public_repos: int
    followers: int
    following: int
    public_gists: int

    # Analysis results
    repositories: List[RepositoryInfo] = []
    languages: List[LanguageStats] = []
    skills: SkillAnalysis

    # Metadata
    last_analyzed: datetime

    class Config:
        from_attributes = True


class ProfileAnalysisResponse(BaseModel):
    """Response schema for comprehensive GitHub profile analysis."""

    # Core analysis data
    user_data: Dict[str, Any]
    repositories: List[Dict[str, Any]]
    languages: List[Dict[str, Any]]
    skills: Dict[str, Any]
    commit_analysis: Dict[str, Any]

    # Metadata
    analyzed_at: str
    analysis_context_type: str = "profile"

    class Config:
        from_attributes = True


class RepositoryAnalysisResponse(BaseModel):
    """Response schema for comprehensive GitHub repository analysis."""

    # Core analysis data
    repository_info: Dict[str, Any]
    languages: List[Dict[str, Any]]
    commits: List[Dict[str, Any]]
    skills: Dict[str, Any]
    commit_analysis: Dict[str, Any]

    # Metadata
    analyzed_at: str
    analysis_time_seconds: float
    analysis_context_type: str = "repository"

    class Config:
        from_attributes = True
