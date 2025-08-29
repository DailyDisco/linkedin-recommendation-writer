"""GitHub API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Form
from pydantic import BaseModel

from app.core.dependencies import get_github_service, get_repository_service, validate_github_username
from app.schemas.github import ProfileAnalysisResponse, RepositoryAnalysisResponse
from app.schemas.repository import RepositoryContributorsResponse
from app.services.github_repository_service import GitHubRepositoryService
from app.services.github_user_service import GitHubUserService

logger = logging.getLogger(__name__)

router = APIRouter()


def _handle_api_error(error: Exception, operation: str, status_code: int = 500) -> None:
    """Handle API errors consistently with logging and HTTP exceptions."""
    logger.error(f"Error in {operation}: {error}")
    if isinstance(error, HTTPException):
        raise error
    raise HTTPException(status_code=status_code, detail="Internal server error")


class GitHubServiceHealthResponse(BaseModel):
    """Response schema for GitHub service health check."""

    status: str  # "healthy", "unhealthy", "degraded"
    message: str


@router.get("/health", response_model=GitHubServiceHealthResponse)
async def get_github_service_health(
    github_user_service: GitHubUserService = Depends(get_github_service),
) -> GitHubServiceHealthResponse:
    """Get GitHub service health status."""
    if not github_user_service.github_client:
        return GitHubServiceHealthResponse(status="error", message="GitHub client not initialized.")
    try:
        github_user_service.github_client.get_user("octocat")  # Test with a public user
        # Check rate limit
        rate_limit = github_user_service.github_client.get_rate_limit()
        core_rate_limit = rate_limit.core
        if core_rate_limit.remaining < 500:
            logger.warning("GitHub API rate limit low: {remaining}/{limit}".format(remaining=core_rate_limit.remaining, limit=core_rate_limit.limit))
            return GitHubServiceHealthResponse(
                status="warning",
                message=(f"GitHub API rate limit remaining: {core_rate_limit.remaining}/" f"{core_rate_limit.limit}. Reset at {core_rate_limit.reset}."),
            )
        return GitHubServiceHealthResponse(status="ok", message="GitHub service is healthy.")
    except Exception as e:
        logger.error(f"GitHub service health check failed: {e}")
        return GitHubServiceHealthResponse(status="error", message=f"GitHub service is unhealthy: {e}")


@router.post("/analyze", response_model=ProfileAnalysisResponse)
async def analyze_github_profile(
    username: str = Form(...),
    force_refresh: bool = Form(False),
    github_user_service: GitHubUserService = Depends(get_github_service),
) -> Optional[ProfileAnalysisResponse]:
    """Analyze a GitHub profile and return comprehensive data."""

    try:
        analysis = await github_user_service.analyze_github_profile(
            username=username,
            force_refresh=force_refresh,
            max_repositories=10,  # Assuming a default max_repositories for this endpoint
        )

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub user '{username}' not found or could not be analyzed",
            )

        return ProfileAnalysisResponse(**analysis)

    except Exception as e:
        _handle_api_error(e, "GitHub profile analysis")
        # This return statement will never be reached, but mypy requires it
        return None  # type: ignore


@router.get("/user/{username}", response_model=ProfileAnalysisResponse)
async def get_github_profile(
    username: str = Depends(validate_github_username),
    force_refresh: bool = False,
    github_user_service: GitHubUserService = Depends(get_github_service),
) -> Optional[ProfileAnalysisResponse]:
    """Get a GitHub profile analysis (convenience endpoint)."""

    return await analyze_github_profile(username, force_refresh, github_user_service)


@router.post("/repository/analyze", response_model=RepositoryAnalysisResponse)
async def analyze_repository(
    repository_full_name: str = Form(...),
    force_refresh: bool = Form(False),
    github_repository_service: GitHubRepositoryService = Depends(get_repository_service),
) -> Optional[RepositoryAnalysisResponse]:
    """Analyze a specific GitHub repository and return comprehensive data."""

    try:
        analysis = await github_repository_service.analyze_repository(
            repository_full_name=repository_full_name,
            force_refresh=force_refresh,
        )

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{repository_full_name}' not found or could not be analyzed",
            )
        return RepositoryAnalysisResponse(**analysis)

    except Exception as e:
        _handle_api_error(e, "repository analysis")
        # This return statement will never be reached, but mypy requires it
        return None  # type: ignore


@router.get("/repository/{owner}/{repo}", response_model=RepositoryAnalysisResponse)
async def get_repository_analysis_by_path(
    owner: str,
    repo: str,
    force_refresh: bool = False,
    github_repository_service: GitHubRepositoryService = Depends(get_repository_service),
) -> Optional[RepositoryAnalysisResponse]:
    """Get a GitHub repository analysis (convenience endpoint)."""
    return await analyze_repository(f"{owner}/{repo}", force_refresh, github_repository_service)


@router.post("/repository/contributors", response_model=RepositoryContributorsResponse)
async def get_repository_contributors(
    repository_full_name: str = Form(...),
    max_contributors: int = Form(50),
    force_refresh: bool = Form(False),
    github_repository_service: GitHubRepositoryService = Depends(get_repository_service),
) -> Optional[RepositoryContributorsResponse]:
    """Get contributors from a GitHub repository with their real names."""

    try:
        result = await github_repository_service.get_repository_contributors(
            repo_name=repository_full_name,
            max_contributors=max_contributors,
            force_refresh=force_refresh,
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{repository_full_name}' not found or could not be accessed",
            )

        return RepositoryContributorsResponse(**result)

    except Exception as e:
        _handle_api_error(e, "repository contributors analysis")
        # This return statement will never be reached, but mypy requires it
        return None  # type: ignore


@router.get(
    "/repository/{owner}/{repo}/contributors",
    response_model=RepositoryContributorsResponse,
)
async def get_repository_contributors_by_path(
    owner: str,
    repo: str,
    max_contributors: int = 50,
    force_refresh: bool = False,
    github_repository_service: GitHubRepositoryService = Depends(get_repository_service),
) -> Optional[RepositoryContributorsResponse]:
    """Get contributors from a GitHub repository (convenience endpoint)."""

    return await get_repository_contributors(f"{owner}/{repo}", max_contributors, force_refresh, github_repository_service)
