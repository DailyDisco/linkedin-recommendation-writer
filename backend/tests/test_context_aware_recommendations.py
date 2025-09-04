"""Tests for context-aware recommendation functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.recommendation_service import RecommendationService
from app.services.prompt_service import PromptService


class TestContextAwareRecommendations:
    """Test context-aware recommendation generation."""

    @pytest.fixture
    def mock_github_service(self):
        """Mock GitHub service."""
        service = AsyncMock()
        # Mock profile data
        service.analyze_github_profile.return_value = {
            "user_data": {
                "github_username": "testuser",
                "full_name": "Test User",
                "bio": "Software developer",
            },
            "repositories": [
                {"name": "repo1", "description": "Test repo 1"},
                {"name": "repo2", "description": "Test repo 2"},
            ],
            "languages": [
                {"language": "Python", "percentage": 60.0},
                {"language": "JavaScript", "percentage": 40.0},
            ],
            "skills": {
                "technical_skills": ["Python", "JavaScript"],
                "frameworks": ["Django", "React"],
                "tools": ["Git", "Docker"],
            },
            "analyzed_at": "2024-01-01T00:00:00Z",
        }
        return service

    @pytest.fixture
    def mock_repository_service(self):
        """Mock repository service."""
        service = AsyncMock()
        # Mock repository data
        service.analyze_repository.return_value = {
            "user_data": {
                "github_username": "testuser",
                "full_name": "Test User",
            },
            "repository_info": {
                "name": "test-repo",
                "description": "A test repository",
                "language": "Python",
                "stars": 50,
                "forks": 10,
            },
            "languages": [
                {"language": "Python", "percentage": 100.0},
            ],
            "skills": {
                "technical_skills": ["Python", "FastAPI"],
                "frameworks": ["FastAPI"],
                "tools": ["Docker"],
            },
            "analyzed_at": "2024-01-01T00:00:00Z",
            "analysis_context_type": "repo_only",
        }
        return service

    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service."""
        service = AsyncMock()
        service.generate_recommendation.return_value = {
            "content": "Test recommendation content",
            "title": "Test Recommendation",
            "word_count": 50,
        }
        return service

    @pytest.fixture
    def recommendation_service(self, mock_github_service, mock_repository_service, mock_ai_service):
        """Create recommendation service with mocked dependencies."""
        service = RecommendationService()
        service.github_service = mock_github_service
        service.repository_service = mock_repository_service
        service.ai_service = mock_ai_service
        service.recommendation_engine_service = AsyncMock()
        service.recommendation_engine_service.generate_recommendation = mock_ai_service.generate_recommendation

        # Mock the database operations to avoid complex SQLAlchemy mocking
        mock_profile = MagicMock()
        mock_profile.id = 1
        service._get_or_create_github_profile = AsyncMock(return_value=mock_profile)

        # Mock the create_recommendation_data method
        mock_recommendation_data = MagicMock()
        mock_recommendation_data.dict.return_value = {
            'id': 1,
            'title': 'Test Recommendation',
            'content': 'Test recommendation content',
            'recommendation_type': 'professional',
            'tone': 'professional',
            'length': 'medium',
            'word_count': 50,
            'ai_model': 'gemini',
            'generation_parameters': {},
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        service.recommendation_engine_service.create_recommendation_data = MagicMock(return_value=mock_recommendation_data)

        return service

    @pytest.mark.asyncio
    async def test_profile_context_fetches_full_profile(self, recommendation_service, mock_github_service):
        """Test that profile context fetches full GitHub profile data."""
        mock_db = AsyncMock()

        result = await recommendation_service.create_recommendation(
            db=mock_db,
            github_username="testuser",
            analysis_context_type="profile",
        )

        # Verify GitHub profile service was called
        mock_github_service.analyze_github_profile.assert_called_once_with(
            username="testuser",
            force_refresh=False
        )

        # Verify repository service was not called
        mock_github_service.repository_service.analyze_repository.assert_not_called()

        assert result.content == "Test recommendation content"

    @pytest.mark.asyncio
    async def test_repo_only_context_fetches_repository_data(self, recommendation_service, mock_repository_service, mock_github_service):
        """Test that repo_only context fetches repository-specific data."""
        mock_db = AsyncMock()

        result = await recommendation_service.create_recommendation(
            db=mock_db,
            github_username="testuser",
            analysis_context_type="repo_only",
            repository_url="https://github.com/testuser/test-repo",
        )

        # Verify repository service was called
        mock_repository_service.analyze_repository.assert_called_once_with(
            "testuser/test-repo",
            force_refresh=False
        )

        # Verify GitHub profile service was also called (for contributor data)
        mock_github_service.analyze_github_profile.assert_called_once_with(
            username="testuser",
            force_refresh=False
        )

        assert result.content == "Test recommendation content"

    @pytest.mark.asyncio
    async def test_repository_contributor_context_fetches_both(self, recommendation_service, mock_repository_service, mock_github_service):
        """Test that repository_contributor context fetches both profile and repository data."""
        mock_db = AsyncMock()

        result = await recommendation_service.create_recommendation(
            db=mock_db,
            github_username="testuser",
            analysis_context_type="repository_contributor",
            repository_url="https://github.com/testuser/test-repo",
        )

        # Verify both services were called
        mock_github_service.analyze_github_profile.assert_called_once_with(
            username="testuser",
            force_refresh=False
        )
        mock_repository_service.analyze_repository.assert_called_once_with(
            "testuser/test-repo",
            force_refresh=False
        )

        assert result.content == "Test recommendation content"


class TestPromptServiceContextAwareness:
    """Test that PromptService builds context-aware prompts."""

    @pytest.fixture
    def prompt_service(self):
        """Create prompt service instance."""
        return PromptService()

    def test_build_prompt_profile_context(self, prompt_service):
        """Test prompt building for profile context."""
        github_data = {
            "user_data": {
                "github_username": "testuser",
                "full_name": "Test User",
            },
            "repositories": [{"name": "repo1"}],
            "languages": [{"language": "Python"}],
            "skills": {"technical_skills": ["Python"], "frameworks": [], "tools": [], "domains": []},
        }

        prompt = prompt_service.build_prompt(
            github_data=github_data,
            analysis_context_type="profile",
        )

        assert "testuser" in prompt
        assert "Here's what I know about them:" in prompt
        assert "Name: Test User" in prompt  # Should include user name
        assert "Programming languages they work with: Python" in prompt  # Should include languages

    def test_build_prompt_repo_only_context(self, prompt_service):
        """Test prompt building for repo_only context."""
        github_data = {
            "user_data": {
                "github_username": "testuser",
                "full_name": "Test User",
            },
            "repository_info": {
                "name": "test-repo",
                "description": "A test repository",
                "language": "Python",
            },
            "languages": [{"language": "Python"}],
            "skills": {"technical_skills": ["Python"], "frameworks": [], "tools": [], "domains": []},
        }

        prompt = prompt_service.build_prompt(
            github_data=github_data,
            analysis_context_type="repo_only",
            repository_url="https://github.com/testuser/test-repo",
        )

        assert "CRITICAL: ONLY DISCUSS THIS SPECIFIC REPOSITORY" in prompt
        assert "test-repo" in prompt
        assert "https://github.com/testuser/test-repo" in prompt
        assert "ONLY mention work, skills, and contributions from THIS SPECIFIC REPOSITORY" in prompt
        # Ensure general profile information is NOT included
        assert "Here's what I know about them:" not in prompt
        assert "What their overall coding work shows:" not in prompt
        assert "Programming languages they work with:" not in prompt

    def test_build_prompt_repository_contributor_context(self, prompt_service):
        """Test prompt building for repository_contributor context."""
        github_data = {
            "user_data": {
                "github_username": "testuser",
                "full_name": "Test User",
            },
            "repository_info": {
                "name": "test-repo",
                "description": "A test repository",
                "language": "Python",
            },
            "repositories": [{"name": "repo1"}, {"name": "repo2"}],
            "languages": [{"language": "Python"}],
            "skills": {"technical_skills": ["Python"], "frameworks": [], "tools": [], "domains": []},
        }

        prompt = prompt_service.build_prompt(
            github_data=github_data,
            analysis_context_type="repository_contributor",
            repository_url="https://github.com/testuser/test-repo",
        )

        assert "FOCUS ON THEIR WORK IN THIS CONTEXT:" in prompt
        assert "test-repo" in prompt
        assert "https://github.com/testuser/test-repo" in prompt
        assert "Balance their specific contributions to this repository with relevant aspects of their overall profile" in prompt


if __name__ == "__main__":
    pytest.main([__file__])
