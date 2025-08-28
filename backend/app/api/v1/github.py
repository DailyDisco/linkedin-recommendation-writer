"""GitHub API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_database_session,
    get_github_service,
    get_repository_service,
    validate_github_username,
)
from app.schemas.github import (
    GitHubAnalysisRequest,
    GitHubProfileResponse,
    LanguageStats,
    RepositoryInfo,
    SkillAnalysis,
)
from app.schemas.repository import (
    RepositoryContributorsRequest,
    RepositoryContributorsResponse,
)
from app.services.github_service import GitHubService
from app.services.repository_service import RepositoryService

logger = logging.getLogger(__name__)

router = APIRouter()


class GitHubServiceHealthResponse(BaseModel):
    """Response schema for GitHub service health check."""

    status: str  # "healthy", "unhealthy", "degraded"
    message: str
    github_token_configured: bool
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[int] = None


@router.get("/health", response_model=GitHubServiceHealthResponse)
async def check_github_service_health(
    github_service: GitHubService = Depends(get_github_service),
):
    """Check GitHub service health and configuration."""
    try:
        github_token_configured = github_service.github_client is not None

        if not github_token_configured:
            return GitHubServiceHealthResponse(
                status="unhealthy",
                message="GitHub token not configured. Please set GITHUB_TOKEN environment variable.",
                github_token_configured=False,
            )

        # Try to get rate limit information
        # rate_limit_info = ...  # Removed unused variable
        try:
            rate_limit = github_service.github_client.get_rate_limit()
            rate_limit_remaining = rate_limit.core.remaining
            rate_limit_reset = rate_limit.core.reset.timestamp()
        except Exception:
            rate_limit_remaining = None
            rate_limit_reset = None

        # Determine health status
        if rate_limit_remaining is not None and rate_limit_remaining > 100:
            status = "healthy"
            message = "GitHub service is healthy and has sufficient API quota."
        elif rate_limit_remaining is not None and rate_limit_remaining > 0:
            status = "degraded"
            message = f"GitHub service has limited API quota remaining ({rate_limit_remaining} requests)."
        else:
            status = "unhealthy"
            message = "GitHub API rate limit exceeded or service unavailable."

        return GitHubServiceHealthResponse(
            status=status,
            message=message,
            github_token_configured=github_token_configured,
            rate_limit_remaining=rate_limit_remaining,
            rate_limit_reset=rate_limit_reset,
        )

    except Exception as e:
        logger.error(f"Error checking GitHub service health: {e}")
        return GitHubServiceHealthResponse(
            status="unhealthy",
            message=f"Error checking GitHub service health: {str(e)}",
            github_token_configured=github_service.github_client is not None,
        )


@router.post("/analyze", response_model=GitHubProfileResponse)
async def analyze_github_profile(
    request: GitHubAnalysisRequest,
    db: AsyncSession = Depends(get_database_session),
    github_service: GitHubService = Depends(get_github_service),
):
    """Analyze a GitHub profile and return comprehensive data."""

    try:
        analysis = await github_service.analyze_github_profile(
            username=request.github_username,
            force_refresh=request.force_refresh,
            max_repositories=request.max_repositories,
        )

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub user '{request.github_username}' not found or could not be analyzed",
            )

        user_data = analysis["user_data"]
        repositories = analysis["repositories"]
        languages = analysis["languages"]
        skills = analysis["skills"]

        # Convert to response format
        response = GitHubProfileResponse(
            github_username=user_data["github_username"],
            github_id=user_data["github_id"],
            full_name=user_data.get("full_name"),
            bio=user_data.get("bio"),
            company=user_data.get("company"),
            location=user_data.get("location"),
            email=user_data.get("email"),
            blog=user_data.get("blog"),
            avatar_url=user_data.get("avatar_url"),
            public_repos=user_data["public_repos"],
            followers=user_data["followers"],
            following=user_data["following"],
            public_gists=user_data["public_gists"],
            repositories=[
                RepositoryInfo(
                    name=repo["name"],
                    description=repo.get("description"),
                    language=repo.get("language"),
                    stars=repo.get("stars", 0),
                    forks=repo.get("forks", 0),
                    size=repo.get("size", 0),
                    created_at=repo["created_at"],
                    updated_at=repo["updated_at"],
                    topics=repo.get("topics", []),
                    url=repo["url"],
                )
                for repo in repositories
            ],
            languages=[
                LanguageStats(
                    language=lang["language"],
                    percentage=lang["percentage"],
                    lines_of_code=lang["lines_of_code"],
                    repository_count=lang["repository_count"],
                )
                for lang in languages
            ],
            skills=SkillAnalysis(
                technical_skills=skills["technical_skills"],
                frameworks=skills["frameworks"],
                tools=skills["tools"],
                domains=skills["domains"],
                soft_skills=skills["soft_skills"],
            ),
            last_analyzed=analysis["analyzed_at"],
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing GitHub profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{username}", response_model=GitHubProfileResponse)
async def get_github_profile(
    username: str = Depends(validate_github_username),
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_database_session),
    github_service: GitHubService = Depends(get_github_service),
):
    """Get a GitHub profile analysis (convenience endpoint)."""

    request = GitHubAnalysisRequest(
        github_username=username,
        force_refresh=force_refresh,
    )

    return await analyze_github_profile(request, db, github_service)


@router.post("/repository/contributors", response_model=RepositoryContributorsResponse)
async def get_repository_contributors(
    request: RepositoryContributorsRequest,
    db: AsyncSession = Depends(get_database_session),
    repository_service: RepositoryService = Depends(get_repository_service),
):
    """Get contributors from a GitHub repository with their real names."""

    try:
        result = await repository_service.get_repository_contributors(
            repo_name=request.repository_name,
            max_contributors=request.max_contributors,
            force_refresh=request.force_refresh,
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{request.repository_name}' not found or could not be accessed",
            )

        return RepositoryContributorsResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting repository contributors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/repository/{owner}/{repo}/contributors",
    response_model=RepositoryContributorsResponse,
)
async def get_repository_contributors_by_path(
    owner: str,
    repo: str,
    max_contributors: int = 50,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_database_session),
    repository_service: RepositoryService = Depends(get_repository_service),
):
    """Get contributors from a GitHub repository (convenience endpoint)."""

    request = RepositoryContributorsRequest(
        repository_name=f"{owner}/{repo}",
        max_contributors=max_contributors,
        force_refresh=force_refresh,
    )

    return await get_repository_contributors(request, db, repository_service)
