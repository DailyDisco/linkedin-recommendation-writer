"""Test configuration and fixtures."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.dependencies import get_redis
from app.core.redis_client import get_redis as get_redis_client
from app.main import app


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.exists = AsyncMock(return_value=0)
    return mock_client


@pytest.fixture
def mock_database_session():
    """Mock database session for testing."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.execute = AsyncMock()
    return mock_session


@pytest.fixture
def test_settings():
    """Test settings that don't require external dependencies."""
    return Settings(
        ENVIRONMENT="test",
        API_DEBUG=True,
        API_HOST="127.0.0.1",
        API_PORT=8000,
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret-key-for-testing-only-not-secure",
        GITHUB_TOKEN="test_github_token",
        GEMINI_API_KEY="test_gemini_key",
        ENABLE_RATE_LIMITING=False,  # Disable for tests
        LOG_LEVEL="WARNING",  # Reduce log noise
    )


@pytest.fixture(autouse=True)
def mock_external_dependencies(mock_redis, mock_database_session):
    """Automatically mock external dependencies for all tests."""

    # Mock Redis
    original_get_redis = get_redis
    async def mock_get_redis():
        return mock_redis

    # Mock Redis client
    original_get_redis_client = get_redis_client
    async def mock_get_redis_client():
        return mock_redis

    # Apply mocks
    import app.core.redis_client
    app.core.redis_client.get_redis = mock_get_redis_client

    import app.core.dependencies
    app.core.dependencies.get_redis = mock_get_redis

    yield

    # Restore originals after test
    app.core.redis_client.get_redis = original_get_redis_client
    app.core.dependencies.get_redis = original_get_redis


@pytest.fixture
def client():
    """Test client with mocked dependencies."""
    # Override settings for testing
    app.state.settings = Settings(
        ENVIRONMENT="test",
        API_DEBUG=True,
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret-key-for-testing-only-not-secure",
        GITHUB_TOKEN="test_github_token",
        GEMINI_API_KEY="test_gemini_key",
        ENABLE_RATE_LIMITING=False,
    )

    return TestClient(app)
