"""GitHub API endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.dependencies import get_github_service, get_repository_service, validate_github_username
from app.core.redis_client import get_cache, set_cache
from app.schemas.github import GitHubAnalysisRequest, ProfileAnalysisResponse, RepositoryAnalysisRequest, RepositoryAnalysisResponse, RepositoryContributorsRequest
from app.schemas.repository import RepositoryContributorsResponse
from app.services.github.github_repository_service import GitHubRepositoryService
from app.services.github.github_user_service import GitHubUserService

logger = logging.getLogger(__name__)

router = APIRouter()


def _handle_api_error(error: Exception, operation: str, status_code: int = 500) -> None:
    """Handle API errors consistently with logging and HTTP exceptions."""
    logger.error(f"Error in {operation}: {error}")
    if isinstance(error, HTTPException):
        raise error
    raise HTTPException(status_code=status_code, detail="Internal server error")


async def _process_github_analysis_background(task_id: str, username: str, force_refresh: bool = False, max_repositories: int = 10) -> None:
    """Background task to process GitHub analysis with progress updates."""
    try:
        logger.info(f"🔄 Starting background analysis for {username} (task: {task_id})")

        # Initialize services
        from app.services.github.github_commit_service import GitHubCommitService

        commit_service = GitHubCommitService()
        github_service = GitHubUserService(commit_service)

        # Update task status to processing
        await set_cache(
            f"task_status:{task_id}", {"status": "processing", "username": username, "started_at": datetime.utcnow().isoformat(), "message": "Initializing GitHub analysis...", "progress": 5}, ttl=3600
        )

        # Perform the analysis
        analysis = await github_service.analyze_github_profile(username=username, force_refresh=force_refresh, max_repositories=max_repositories)

        if analysis:
            # Store successful result
            await set_cache(f"task_result:{task_id}", analysis, ttl=3600)
            await set_cache(
                f"task_status:{task_id}",
                {"status": "completed", "username": username, "completed_at": datetime.utcnow().isoformat(), "message": "Analysis completed successfully", "progress": 100},
                ttl=3600,
            )
            logger.info(f"✅ Background analysis completed for {username}")
        else:
            # Store error result
            await set_cache(
                f"task_status:{task_id}",
                {"status": "failed", "username": username, "completed_at": datetime.utcnow().isoformat(), "message": "Analysis failed - user not found or analysis error", "progress": 0},
                ttl=3600,
            )
            logger.error(f"❌ Background analysis failed for {username}")

    except Exception as e:
        logger.error(f"💥 Background analysis error for {username}: {e}")
        await set_cache(
            f"task_status:{task_id}", {"status": "failed", "username": username, "completed_at": datetime.utcnow().isoformat(), "message": f"Analysis failed: {str(e)}", "progress": 0}, ttl=3600
        )


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
        core_rate_limit = rate_limit.rate
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
    request: GitHubAnalysisRequest,
    background_tasks: BackgroundTasks,
    github_user_service: GitHubUserService = Depends(get_github_service),
) -> Optional[ProfileAnalysisResponse]:
    """Analyze a GitHub profile - uses background processing for heavy analysis."""

    # Check cache first for quick response - include analysis context in cache key
    context_suffix = ""
    if hasattr(request, "analysis_context_type") and request.analysis_context_type != "profile":
        context_suffix = f":{request.analysis_context_type}"
        if hasattr(request, "repository_url") and request.repository_url:
            repo_path = request.repository_url.replace("https://github.com/", "").split("?")[0]
            context_suffix += f":{repo_path}"

    cache_key = f"github_profile:{request.username}{context_suffix}"
    cached_analysis = await get_cache(cache_key)

    if cached_analysis and not request.force_refresh:
        logger.info(f"💨 Returning cached GitHub analysis for {request.username}")
        return ProfileAnalysisResponse(**cached_analysis)

    # For heavy analysis, use background processing
    logger.info(f"🚀 Starting background GitHub analysis for {request.username}")

    # Generate unique task ID
    task_id = f"github_profile_{request.username}_{int(datetime.utcnow().timestamp())}"

    # Start background task
    background_tasks.add_task(_process_github_analysis_background, task_id=task_id, username=request.username, force_refresh=request.force_refresh, max_repositories=10)

    # Return immediate response with task ID
    return ProfileAnalysisResponse(
        user_data={"login": request.username, "processing": True, "task_id": task_id, "message": "Analysis started in background"},
        repositories=[],
        languages=[],
        skills={"status": "processing", "task_id": task_id, "message": "Analysis in progress"},
        commit_analysis={"task_id": task_id, "status": "processing", "message": "GitHub profile analysis started"},
        analyzed_at=datetime.utcnow().isoformat(),
        analysis_context_type="profile",
    )


@router.post("/analyze/sync", response_model=ProfileAnalysisResponse)
async def analyze_github_profile_sync(
    request: GitHubAnalysisRequest,
    github_user_service: GitHubUserService = Depends(get_github_service),
) -> Optional[ProfileAnalysisResponse]:
    """Analyze a GitHub profile synchronously (for quick analysis or when background processing is not needed)."""

    try:
        analysis = await github_user_service.analyze_github_profile(
            username=request.username,
            force_refresh=request.force_refresh,
            max_repositories=10,
        )

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub user '{request.username}' not found or could not be analyzed",
            )

        return ProfileAnalysisResponse(**analysis)

    except Exception as e:
        _handle_api_error(e, "GitHub profile analysis")
        return None  # type: ignore


@router.get("/task/{task_id}")
async def get_task_status(task_id: str) -> dict:
    """Get the status and result of a background analysis task."""

    try:
        # Check task status
        status_data = await get_cache(f"task_status:{task_id}")

        if not status_data:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # If completed, include result
        if status_data.get("status") == "completed":
            result_data = await get_cache(f"task_result:{task_id}")
            if result_data:
                return {"task_id": task_id, "status": "completed", "result": result_data, "completed_at": status_data.get("completed_at")}

        return {
            "task_id": task_id,
            "status": status_data.get("status", "unknown"),
            "message": status_data.get("message", ""),
            "username": status_data.get("username"),
            "started_at": status_data.get("started_at"),
            "updated_at": status_data.get("completed_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/user/{username}", response_model=ProfileAnalysisResponse)
async def get_github_profile(
    username: str = Depends(validate_github_username),
    force_refresh: bool = False,
    background_tasks: BackgroundTasks = None,
    github_user_service: GitHubUserService = Depends(get_github_service),
) -> Optional[ProfileAnalysisResponse]:
    """Get a GitHub profile analysis (convenience endpoint - uses background processing)."""

    # For GET requests, use synchronous processing for better compatibility
    try:
        analysis = await github_user_service.analyze_github_profile(
            username=username,
            force_refresh=force_refresh,
            max_repositories=10,
        )

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub user '{username}' not found or could not be analyzed",
            )

        return ProfileAnalysisResponse(**analysis)

    except Exception as e:
        _handle_api_error(e, "GitHub profile analysis")
        return None  # type: ignore


@router.get("/user/{username}/async")
async def get_github_profile_async(
    username: str = Depends(validate_github_username),
    force_refresh: bool = False,
    background_tasks: BackgroundTasks = None,
) -> dict:
    """Get a GitHub profile analysis asynchronously (returns task ID immediately)."""

    # Generate unique task ID
    task_id = f"github_profile_{username}_{int(datetime.utcnow().timestamp())}"

    # Start background task
    background_tasks.add_task(_process_github_analysis_background, task_id=task_id, username=username, force_refresh=force_refresh, max_repositories=10)

    return {"task_id": task_id, "status": "processing", "username": username, "message": "GitHub profile analysis started in background"}


@router.post("/repository/analyze", response_model=RepositoryAnalysisResponse)
async def analyze_repository(
    request: RepositoryAnalysisRequest,
    github_repository_service: GitHubRepositoryService = Depends(get_repository_service),
) -> Optional[RepositoryAnalysisResponse]:
    """Analyze a specific GitHub repository and return comprehensive data."""

    try:
        analysis = await github_repository_service.analyze_repository(
            repository_full_name=request.repository_full_name,
            force_refresh=request.force_refresh,
        )

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{request.repository_full_name}' not found or could not be analyzed",
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

    # Create a request object for the main endpoint
    request = RepositoryAnalysisRequest(repository_full_name=f"{owner}/{repo}", force_refresh=force_refresh)
    return await analyze_repository(request, github_repository_service)


@router.post("/repository/contributors", response_model=RepositoryContributorsResponse)
async def get_repository_contributors(
    request: RepositoryContributorsRequest,
    github_repository_service: GitHubRepositoryService = Depends(get_repository_service),
) -> Optional[RepositoryContributorsResponse]:
    """Get contributors from a GitHub repository with their real names."""

    try:
        result = await github_repository_service.get_repository_contributors(
            repo_name=request.repository_full_name,
            max_contributors=request.max_contributors,
            force_refresh=request.force_refresh,
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{request.repository_full_name}' not found or could not be accessed",
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

    # Create a request object for the main endpoint
    request = RepositoryContributorsRequest(
        repository_full_name=f"{owner}/{repo}",
        max_contributors=max_contributors,
        force_refresh=force_refresh,
    )
    return await get_repository_contributors(request, github_repository_service)


@router.get("/analyze/stream/{task_id}")
async def stream_github_analysis_progress(task_id: str):
    """Stream GitHub analysis progress updates via Server-Sent Events."""

    async def generate_progress_stream():
        """Generate SSE stream for GitHub analysis progress."""
        try:
            logger.info(f"🎯 SSE stream started for GitHub analysis task: {task_id}")

            while True:
                # Check task status
                status_data = await get_cache(f"task_status:{task_id}")

                if not status_data:
                    # Task not found or expired
                    yield 'data: {"status": "not_found", "message": "Task not found or expired"}\n\n'
                    break

                status = status_data.get("status", "unknown")
                message = status_data.get("message", "")
                progress = status_data.get("progress", 0)

                # Create progress update
                progress_data = {"task_id": task_id, "status": status, "stage": message, "progress": progress, "timestamp": datetime.utcnow().isoformat()}

                # If completed, include result
                if status == "completed":
                    result_data = await get_cache(f"task_result:{task_id}")
                    if result_data:
                        progress_data["result"] = result_data

                # Send progress update
                yield f"data: {progress_data}\n\n"

                # If completed or failed, end the stream
                if status in ["completed", "failed"]:
                    logger.info(f"🎯 SSE stream ended for task {task_id}: {status}")
                    break

                # Wait before next check
                import asyncio

                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in GitHub analysis SSE stream for task {task_id}: {e}")
            yield f'data: {{"status": "error", "message": "Stream error: {str(e)}"}}\n\n'

    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@router.post("/analyze/stream")
async def start_github_analysis_stream(
    request: GitHubAnalysisRequest,
    background_tasks: BackgroundTasks,
    github_user_service: GitHubUserService = Depends(get_github_service),
):
    """Start GitHub analysis with streaming progress updates."""
    try:
        logger.info("🚀 Starting streaming GitHub analysis...")
        logger.info(f"   • Username: {request.username}")
        logger.info(f"   • Force refresh: {request.force_refresh}")

        # Generate unique task ID
        import uuid

        task_id = str(uuid.uuid4())

        logger.info(f"   • Task ID: {task_id}")

        # Set initial status
        await set_cache(
            f"task_status:{task_id}", {"status": "queued", "username": request.username, "started_at": datetime.utcnow().isoformat(), "message": "Analysis queued...", "progress": 0}, ttl=3600
        )

        # Start background analysis
        background_tasks.add_task(_process_github_analysis_background, task_id, request.username, request.force_refresh)

        return {"task_id": task_id, "status": "started", "message": "GitHub analysis started. Use the task_id to stream progress updates.", "stream_url": f"/api/v1/github/analyze/stream/{task_id}"}

    except Exception as e:
        logger.error(f"Error starting GitHub analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")
