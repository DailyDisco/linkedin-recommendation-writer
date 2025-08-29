"""Recommendation-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """Request schema for generating recommendations."""

    github_username: str = Field(..., description="GitHub username to analyze")
    recommendation_type: str = Field(
        "professional",
        description="Type of recommendation",
        pattern="^(professional|technical|leadership|academic|personal)$",
    )
    tone: str = Field(
        "professional",
        description="Tone of the recommendation",
        pattern="^(professional|friendly|formal|casual)$",
    )
    length: str = Field(
        "medium",
        description="Length of the recommendation",
        pattern="^(short|medium|long)$",
    )
    custom_prompt: Optional[str] = Field(None, description="Custom prompt additions for personalization")
    include_specific_skills: Optional[list] = Field(None, description="Specific skills to highlight")
    target_role: Optional[str] = Field(None, description="Target role or industry for the recommendation")
    include_keywords: Optional[List[str]] = Field(None, description="Keywords/phrases that must be included in the recommendation")
    exclude_keywords: Optional[List[str]] = Field(None, description="Keywords/phrases that must NOT be included in the recommendation")
    analysis_context_type: Optional[str] = Field("profile", description="Type of analysis performed: 'profile' or 'repo_only'")
    repository_url: Optional[str] = Field(None, description="Repository URL if repo-specific analysis")


class RecommendationOption(BaseModel):
    """Schema for a single recommendation option."""

    id: int
    name: str
    content: str
    title: str
    word_count: int
    focus: str
    confidence_score: int
    explanation: str = Field(..., description="Explanation of what makes this option unique and when to choose it")


class KeywordRefinementRequest(BaseModel):
    """Schema for keyword refinement requests."""

    recommendation_id: int = Field(..., description="ID of the existing recommendation to refine")
    include_keywords: Optional[List[str]] = Field(None, description="Keywords/phrases that must be included")
    exclude_keywords: Optional[List[str]] = Field(None, description="Keywords/phrases that must NOT be included")
    refinement_instructions: Optional[str] = Field(None, description="Additional instructions for the refinement")


class KeywordRefinementResponse(BaseModel):
    """Schema for keyword refinement responses."""

    original_recommendation_id: int
    refined_content: str
    refined_title: str
    word_count: int
    confidence_score: int
    include_keywords_used: List[str] = Field(default_factory=list, description="Keywords that were successfully included")
    exclude_keywords_avoided: List[str] = Field(default_factory=list, description="Keywords that were successfully avoided")
    refinement_summary: str = Field(..., description="Summary of changes made during refinement")
    generation_parameters: Dict[str, Any]


class RecommendationCreate(BaseModel):
    """Schema for creating a recommendation record."""

    github_profile_id: int
    title: str
    content: str
    recommendation_type: str = "professional"
    tone: str = "professional"
    length: str = "medium"
    ai_model: str
    generation_prompt: Optional[str] = None
    generation_parameters: Optional[Dict[str, Any]] = None
    confidence_score: int = 0
    word_count: int = 0

    # Selected option information (when created from multiple options)
    selected_option_id: Optional[int] = None
    selected_option_name: Optional[str] = None
    selected_option_focus: Optional[str] = None
    generated_options: Optional[List[Dict[str, Any]]] = None


class RecommendationFromOptionRequest(BaseModel):
    """Schema for creating a recommendation from a selected option."""

    github_username: str = Field(..., description="GitHub username")
    selected_option: RecommendationOption = Field(..., description="The selected recommendation option")
    all_options: List[RecommendationOption] = Field(..., description="All generated options for reference")
    analysis_context_type: Optional[str] = Field("profile", description="Type of analysis performed")
    repository_url: Optional[str] = Field(None, description="Repository URL if repo-specific analysis")
    recommendation_type: Optional[str] = Field(None, description="Type of recommendation")
    tone: Optional[str] = Field(None, description="Tone of the recommendation")
    length: Optional[str] = Field(None, description="Length of the recommendation")


class RecommendationResponse(BaseModel):
    """Response schema for recommendations."""

    id: int
    title: str
    content: str
    recommendation_type: str
    tone: str
    length: str
    confidence_score: int
    word_count: int

    # Generation metadata
    ai_model: str
    generation_parameters: Optional[Dict[str, Any]] = None

    # Selected option information (when created from multiple options)
    selected_option_id: Optional[int] = None
    selected_option_name: Optional[str] = None
    selected_option_focus: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Related data
    github_username: Optional[str] = None

    # Keyword refinement metadata (optional, only present for refined recommendations)
    refinement_summary: Optional[str] = None
    include_keywords_used: Optional[List[str]] = None
    exclude_keywords_avoided: Optional[List[str]] = None
    validation_issues: Optional[List[str]] = None
    original_recommendation_id: Optional[int] = None


class ReadmeGenerationRequest(BaseModel):
    """Schema for README generation requests."""

    repository_full_name: str = Field(..., description="Full repository name (owner/repo)")
    style: str = Field("comprehensive", description="README style: comprehensive, minimal, or technical")
    include_sections: Optional[List[str]] = Field(None, description="Specific sections to include")
    target_audience: Optional[str] = Field("developers", description="Target audience: developers, users, or both")


class ReadmeGenerationResponse(BaseModel):
    """Schema for README generation responses."""

    repository_name: str
    repository_full_name: str
    generated_content: str
    sections: Dict[str, str] = Field(default_factory=dict, description="Generated sections with their content")
    word_count: int
    confidence_score: int
    generation_parameters: Dict[str, Any]
    analysis_summary: str = Field(..., description="Summary of repository analysis used for generation")


class RecommendationVersionInfo(BaseModel):
    """Schema for recommendation version information."""

    id: int
    version_number: int
    change_type: str
    change_description: Optional[str]
    confidence_score: int
    word_count: int
    created_at: datetime
    created_by: Optional[str]


class RecommendationVersionDetail(BaseModel):
    """Schema for detailed recommendation version information."""

    id: int
    recommendation_id: int
    version_number: int
    change_type: str
    change_description: Optional[str]
    title: str
    content: str
    generation_parameters: Optional[Dict[str, Any]]
    confidence_score: int
    word_count: int
    created_at: datetime
    created_by: Optional[str]


class RecommendationVersionHistoryResponse(BaseModel):
    """Schema for recommendation version history response."""

    recommendation_id: int
    total_versions: int
    current_version: int
    versions: List[RecommendationVersionInfo]


class VersionComparisonResponse(BaseModel):
    """Schema for version comparison response."""

    recommendation_id: int
    version_a: RecommendationVersionDetail
    version_b: RecommendationVersionDetail
    differences: Dict[str, Any] = Field(default_factory=dict, description="Key differences between versions")


class RevertToVersionRequest(BaseModel):
    """Schema for reverting to a specific version."""

    version_id: int = Field(..., description="ID of the version to revert to")
    revert_reason: Optional[str] = Field(None, description="Reason for reverting to this version")


class SkillGapAnalysisRequest(BaseModel):
    """Schema for skill gap analysis requests."""

    github_username: str = Field(..., description="GitHub username to analyze")
    target_role: str = Field(..., description="Target job role or position")
    industry: Optional[str] = Field("technology", description="Industry context")
    experience_level: Optional[str] = Field("mid", description="Experience level: junior, mid, senior")


class SkillMatch(BaseModel):
    """Schema for individual skill match analysis."""

    skill: str
    match_level: str = Field(..., description="strong, moderate, weak, missing")
    evidence: List[str] = Field(default_factory=list, description="Evidence from GitHub profile")
    confidence_score: int = Field(..., description="Confidence in the assessment (0-100)")


class SkillGapAnalysisResponse(BaseModel):
    """Schema for skill gap analysis responses."""

    github_username: str
    target_role: str
    overall_match_score: int = Field(..., description="Overall match percentage (0-100)")
    skill_analysis: List[SkillMatch] = Field(default_factory=list, description="Detailed skill-by-skill analysis")
    strengths: List[str] = Field(default_factory=list, description="Key strengths identified")
    gaps: List[str] = Field(default_factory=list, description="Skills that need development")
    recommendations: List[str] = Field(default_factory=list, description="Specific recommendations for improvement")
    learning_resources: List[str] = Field(default_factory=list, description="Suggested learning resources")
    analysis_summary: str = Field(..., description="Overall summary of the analysis")
    generated_at: datetime


class ContributorInfo(BaseModel):
    """Schema for individual contributor information."""

    username: str
    full_name: Optional[str]
    contributions: int
    primary_languages: List[str]
    top_skills: List[str]
    contribution_focus: str  # e.g., "frontend", "backend", "testing", etc.
    key_contributions: List[str]


class MultiContributorRequest(BaseModel):
    """Schema for multi-contributor recommendation requests."""

    repository_full_name: str = Field(..., description="Full repository name (owner/repo)")
    max_contributors: int = Field(5, description="Maximum number of contributors to include")
    min_contributions: int = Field(1, description="Minimum contributions required")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")
    recommendation_type: str = Field("professional", description="Type of recommendation")
    tone: str = Field("professional", description="Tone of recommendation")
    length: str = Field("medium", description="Length of recommendation")


class MultiContributorResponse(BaseModel):
    """Schema for multi-contributor recommendation responses."""

    repository_name: str
    repository_full_name: str
    total_contributors: int
    contributors_analyzed: int
    contributors: List[ContributorInfo]
    recommendation: str
    team_highlights: List[str] = Field(default_factory=list, description="Key team achievements")
    collaboration_insights: List[str] = Field(default_factory=list, description="Insights about team collaboration")
    technical_diversity: Dict[str, int] = Field(default_factory=dict, description="Language/technology distribution")
    word_count: int
    confidence_score: int
    generated_at: datetime

    class Config:
        from_attributes = True


class RecommendationOptionsResponse(BaseModel):
    """Response schema for multiple recommendation options."""

    options: List[RecommendationOption]
    generation_parameters: Optional[Dict[str, Any]] = None
    generation_prompt: Optional[str] = None


class RecommendationListResponse(BaseModel):
    """Response schema for listing recommendations."""

    recommendations: list[RecommendationResponse]
    total: int
    page: int = 1
    page_size: int = 10
