"""Recommendation-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.security_config import security_utils


class RecommendationRequest(BaseModel):
    """Request schema for generating recommendations."""

    github_username: str = Field(..., description="GitHub username to analyze", min_length=1, max_length=39)
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
    custom_prompt: Optional[str] = Field(None, description="Custom prompt additions for personalization", max_length=1000)
    include_specific_skills: Optional[List[str]] = Field(None, description="Specific skills to highlight", max_items=20)
    target_role: Optional[str] = Field(None, description="Target role or industry for the recommendation", max_length=200)
    include_keywords: Optional[List[str]] = Field(None, description="Keywords/phrases that must be included", max_items=10)
    exclude_keywords: Optional[List[str]] = Field(None, description="Keywords/phrases that must NOT be included", max_items=10)
    analysis_context_type: Optional[str] = Field("profile", description="Type of analysis performed: 'profile' or 'repo_only'")
    repository_url: Optional[str] = Field(None, description="Repository URL if repo-specific analysis", max_length=500)

    @field_validator("github_username")
    @classmethod
    def validate_github_username(cls, v: str) -> str:
        """Validate GitHub username format."""
        if not security_utils.validate_github_username(v):
            raise ValueError("Invalid GitHub username format")
        return v

    @field_validator("repository_url")
    @classmethod
    def validate_repository_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate repository URL if provided."""
        if v and not security_utils.validate_url(v, ["github.com"]):
            raise ValueError("Invalid repository URL or not a GitHub URL")
        return v

    @field_validator("custom_prompt", "target_role")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to remove dangerous content."""
        if v:
            return security_utils.sanitize_text(v)
        return v

    @field_validator("include_keywords", "exclude_keywords", "include_specific_skills")
    @classmethod
    def validate_and_sanitize_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and sanitize list inputs."""
        if v:
            # Limit list size and sanitize each item
            sanitized = []
            for item in v[:20]:  # Limit to 20 items
                if isinstance(item, str):
                    sanitized_item = security_utils.sanitize_text(item)
                    if sanitized_item and len(sanitized_item) <= 100:  # Max 100 chars per item
                        sanitized.append(sanitized_item)
            return sanitized if sanitized else None
        return v


class RecommendationOption(BaseModel):
    """Schema for a single recommendation option."""

    id: int
    name: str
    content: str
    title: str
    word_count: int
    focus: str
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

    model_config = {"from_attributes": True}

    id: int
    title: str
    content: str
    recommendation_type: str
    tone: str
    length: str
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


class RecommendationVersionInfo(BaseModel):
    """Schema for recommendation version information."""

    id: int
    version_number: int
    change_type: str
    change_description: Optional[str]
    word_count: int
    created_at: datetime
    created_by: Optional[str]
    include_keywords_used: Optional[List[str]] = None
    exclude_keywords_avoided: Optional[List[str]] = None


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
    word_count: int
    created_at: datetime
    created_by: Optional[str]
    include_keywords_used: Optional[List[str]] = None
    exclude_keywords_avoided: Optional[List[str]] = None


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


class RecommendationOptionsResponse(BaseModel):
    """Response schema for multiple recommendation options."""

    options: List[RecommendationOption]
    generation_parameters: Optional[Dict[str, Any]] = None
    generation_prompt: Optional[str] = None


class DynamicRefinementRequest(BaseModel):
    """Schema for dynamic refinement requests during streaming."""

    original_content: str = Field(..., description="Original recommendation content to refine")
    refinement_instructions: str = Field(..., description="Instructions for how to refine the recommendation")
    github_username: str = Field(..., description="GitHub username for context")
    recommendation_type: Optional[str] = Field("professional", description="Type of recommendation")
    tone: Optional[str] = Field("professional", description="Tone of the recommendation")
    length: Optional[str] = Field("medium", description="Length of the recommendation")
    analysis_context_type: Optional[str] = Field("profile", description="Type of analysis performed")
    repository_url: Optional[str] = Field(None, description="Repository URL if repo-specific analysis")
    dynamic_tone: Optional[str] = Field(None, description="Dynamic tone override")
    dynamic_length: Optional[str] = Field(None, description="Dynamic length override")
    include_keywords: Optional[List[str]] = Field(None, description="Keywords to include")
    exclude_keywords: Optional[List[str]] = Field(None, description="Keywords to exclude")
    force_refresh: Optional[bool] = Field(False, description="Bypass cache and force fresh generation")


class StreamProgressResponse(BaseModel):
    """Schema for streaming progress updates."""

    stage: str = Field(..., description="Current processing stage")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    status: str = Field(..., description="Current status: preparing, analyzing, processing, generating, finalizing, complete, error")
    result: Optional[Dict[str, Any]] = Field(None, description="Final result when complete")
    error: Optional[str] = Field(None, description="Error message if status is error")


class RecommendationListResponse(BaseModel):
    """Response schema for listing recommendations."""

    recommendations: list[RecommendationResponse]
    total: int
    page: int = 1
    page_size: int = 10
