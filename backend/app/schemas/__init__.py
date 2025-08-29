"""Pydantic schemas package."""

from .github import GitHubAnalysisRequest, GitHubProfileResponse, LanguageStats, SkillAnalysis
from .recommendation import (
    KeywordRefinementRequest,
    ReadmeGenerationRequest,
    ReadmeGenerationResponse,
    RecommendationCreate,
    RecommendationFromOptionRequest,
    RecommendationListResponse,
    RecommendationOption,
    RecommendationOptionsResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from .repository import RepositoryInfo
from .user import Token, TokenData, UserCreate, UserLogin, UserResponse

__all__ = [
    "GitHubAnalysisRequest",
    "GitHubProfileResponse",
    "LanguageStats",
    "RepositoryInfo",
    "SkillAnalysis",
    "KeywordRefinementRequest",
    "RecommendationCreate",
    "RecommendationFromOptionRequest",
    "RecommendationListResponse",
    "RecommendationOption",
    "RecommendationOptionsResponse",
    "RecommendationRequest",
    "RecommendationResponse",
    "ReadmeGenerationRequest",
    "ReadmeGenerationResponse",
    "Token",
    "TokenData",
    "UserCreate",
    "UserLogin",
    "UserResponse",
]
