"""Pydantic schemas package."""

from app.schemas.github import GitHubAnalysisRequest, GitHubProfileResponse
from app.schemas.recommendation import (RecommendationCreate,
                                        RecommendationRequest,
                                        RecommendationResponse)
from app.schemas.repository import (ContributorInfo,
                                    RepositoryContributorsRequest,
                                    RepositoryContributorsResponse,
                                    RepositoryInfo)

__all__ = [
    "GitHubProfileResponse",
    "GitHubAnalysisRequest",
    "RecommendationRequest",
    "RecommendationResponse",
    "RecommendationCreate",
    "RepositoryContributorsRequest",
    "RepositoryContributorsResponse",
    "ContributorInfo",
    "RepositoryInfo"
]
