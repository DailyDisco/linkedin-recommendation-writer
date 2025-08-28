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
    custom_prompt: Optional[str] = Field(
        None, description="Custom prompt additions for personalization"
    )
    include_specific_skills: Optional[list] = Field(
        None, description="Specific skills to highlight"
    )
    target_role: Optional[str] = Field(
        None, description="Target role or industry for the recommendation"
    )


class RecommendationOption(BaseModel):
    """Schema for a single recommendation option."""

    id: int
    name: str
    content: str
    title: str
    word_count: int
    focus: str
    confidence_score: int


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
    selected_option: RecommendationOption = Field(
        ..., description="The selected recommendation option"
    )
    all_options: List[RecommendationOption] = Field(
        ..., description="All generated options for reference"
    )
    analysis_type: Optional[str] = Field(
        "profile", description="Type of analysis performed"
    )
    repository_url: Optional[str] = Field(
        None, description="Repository URL if repo-specific analysis"
    )


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
