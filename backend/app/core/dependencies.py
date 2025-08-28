"""Dependency injection container and providers."""

import logging
from typing import AsyncGenerator

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.exceptions import DatabaseError
from app.core.redis_client import get_redis
from app.services.ai_service import AIService
from app.services.github_service import GitHubService
from app.services.recommendation_service import RecommendationService
from app.services.repository_service import RepositoryService

logger = logging.getLogger(__name__)


# Database Dependencies
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Handles connection lifecycle and error management.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise DatabaseError("transaction", str(e))
    finally:
        await session.close()


# Redis Dependencies
async def get_redis_client():
    """Dependency that provides Redis client."""
    try:
        return await get_redis()
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return None  # Redis is non-critical


# Request Context Dependencies
def get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", "unknown")


# Service Dependencies
class ServiceContainer:
    """Service container for dependency injection with proper lifecycle management."""

    _instances: dict = {}

    @classmethod
    def _get_service(cls, service_name: str, service_class):
        """Generic service getter with singleton pattern."""
        if service_name not in cls._instances:
            logger.info(f"Initializing {service_name} service")
            cls._instances[service_name] = service_class()
        return cls._instances[service_name]

    @classmethod
    def get_github_service(cls) -> GitHubService:
        """Get or create GitHub service instance."""
        return cls._get_service("github", GitHubService)

    @classmethod
    def get_ai_service(cls) -> AIService:
        """Get or create AI service instance."""
        return cls._get_service("ai", AIService)

    @classmethod
    def get_recommendation_service(cls) -> RecommendationService:
        """Get or create recommendation service instance."""
        return cls._get_service("recommendation", RecommendationService)

    @classmethod
    def get_repository_service(cls) -> RepositoryService:
        """Get or create repository service instance."""
        return cls._get_service("repository", RepositoryService)

    @classmethod
    def clear_instances(cls):
        """Clear all service instances (useful for testing)."""
        cls._instances.clear()


# Service provider functions
def get_github_service() -> GitHubService:
    """Dependency provider for GitHub service."""
    return ServiceContainer.get_github_service()


def get_ai_service() -> AIService:
    """Dependency provider for AI service."""
    return ServiceContainer.get_ai_service()


def get_recommendation_service() -> RecommendationService:
    """Dependency provider for recommendation service."""
    return ServiceContainer.get_recommendation_service()


def get_repository_service() -> RepositoryService:
    """Dependency provider for repository service."""
    return ServiceContainer.get_repository_service()


# Validation Dependencies
async def validate_github_username(username: str) -> str:
    """Validate GitHub username format."""
    if not username or len(username) < 1 or len(username) > 39:
        raise HTTPException(
            status_code=400,
            detail="GitHub username must be between 1 and 39 characters",
        )

    # Basic validation for allowed characters
    import re

    if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", username):
        raise HTTPException(status_code=400, detail="Invalid GitHub username format")

    return username


# Pagination Dependencies
class PaginationParams:
    """Pagination parameters."""

    def __init__(self, page: int = 1, page_size: int = 10):
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")

        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


def get_pagination_params(page: int = 1, page_size: int = 10) -> PaginationParams:
    """Dependency provider for pagination parameters."""
    return PaginationParams(page, page_size)
