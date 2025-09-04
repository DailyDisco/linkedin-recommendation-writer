"""Tests for RecommendationEngineService."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.services.recommendation_engine_service import RecommendationEngineService
from app.schemas.recommendation import RecommendationCreate, RecommendationOptionsResponse, RecommendationOption


class TestRecommendationEngineService:
    """Test suite for RecommendationEngineService."""

    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        ai_service = Mock()
        ai_service.generate_recommendation = AsyncMock()
        ai_service.regenerate_recommendation = AsyncMock()
        ai_service.refine_recommendation_with_keywords = AsyncMock()
        return ai_service

    @pytest.fixture
    def engine_service(self, mock_ai_service):
        """Create RecommendationEngineService instance."""
        return RecommendationEngineService(mock_ai_service)

    @pytest.fixture
    def sample_github_data(self):
        """Sample GitHub data for testing."""
        return {
            "skills": {
                "technical_skills": ["Python", "JavaScript"],
                "frameworks": ["Django", "React"],
                "tools": ["Git", "Docker"],
                "domains": ["Web Development"],
                "dependencies_found": []
            },
            "repositories": [
                {"name": "test-repo", "language": "Python", "description": "A test repo"}
            ]
        }

    @pytest.fixture
    def sample_ai_result(self):
        """Sample AI result for testing."""
        return {
            "title": "Test Recommendation",
            "content": "This is a test recommendation content.",
            "word_count": 50,
            "generation_parameters": {
                "model": "test-model",
                "temperature": 0.7
            },
            "generation_prompt": "Test prompt"
        }

    def test_init(self, engine_service, mock_ai_service):
        """Test RecommendationEngineService initialization."""
        assert isinstance(engine_service, RecommendationEngineService)
        assert engine_service.ai_service == mock_ai_service

    @pytest.mark.asyncio
    async def test_generate_recommendation(self, engine_service, mock_ai_service, sample_github_data, sample_ai_result):
        """Test generating a recommendation."""
        mock_ai_service.generate_recommendation.return_value = sample_ai_result

        result = await engine_service.generate_recommendation(
            github_data=sample_github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium"
        )

        assert result == sample_ai_result
        mock_ai_service.generate_recommendation.assert_called_once_with(
            github_data=sample_github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium",
            custom_prompt=None,
            target_role=None,
            specific_skills=None,
            exclude_keywords=None
        )

    @pytest.mark.asyncio
    async def test_generate_recommendation_with_all_params(self, engine_service, mock_ai_service, sample_github_data, sample_ai_result):
        """Test generating a recommendation with all parameters."""
        mock_ai_service.generate_recommendation.return_value = sample_ai_result

        result = await engine_service.generate_recommendation(
            github_data=sample_github_data,
            recommendation_type="technical",
            tone="casual",
            length="long",
            custom_prompt="Custom prompt",
            target_role="developer",
            specific_skills=["Python", "React"],
            exclude_keywords=["bad", "word"]
        )

        assert result == sample_ai_result
        mock_ai_service.generate_recommendation.assert_called_once_with(
            github_data=sample_github_data,
            recommendation_type="technical",
            tone="casual",
            length="long",
            custom_prompt="Custom prompt",
            target_role="developer",
            specific_skills=["Python", "React"],
            exclude_keywords=["bad", "word"]
        )

    @pytest.mark.asyncio
    async def test_regenerate_recommendation(self, engine_service, mock_ai_service, sample_github_data, sample_ai_result):
        """Test regenerating a recommendation."""
        mock_ai_service.regenerate_recommendation.return_value = sample_ai_result

        result = await engine_service.regenerate_recommendation(
            original_content="Original content",
            refinement_instructions="Make it better",
            github_data=sample_github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium"
        )

        assert result == sample_ai_result
        mock_ai_service.regenerate_recommendation.assert_called_once_with(
            original_content="Original content",
            refinement_instructions="Make it better",
            github_data=sample_github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium"
        )

    @pytest.mark.asyncio
    async def test_refine_recommendation_with_keywords(self, engine_service, mock_ai_service, sample_github_data, sample_ai_result):
        """Test refining a recommendation with keywords."""
        mock_ai_service.refine_recommendation_with_keywords.return_value = sample_ai_result

        result = await engine_service.refine_recommendation_with_keywords(
            original_content="Original content",
            refinement_instructions="Add keywords",
            github_data=sample_github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium",
            include_keywords=["leadership", "teamwork"],
            exclude_keywords=["negative"]
        )

        assert result == sample_ai_result
        mock_ai_service.refine_recommendation_with_keywords.assert_called_once_with(
            original_content="Original content",
            refinement_instructions="Add keywords",
            github_data=sample_github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium",
            include_keywords=["leadership", "teamwork"],
            exclude_keywords=["negative"]
        )

    def test_create_recommendation_data(self, engine_service, sample_ai_result):
        """Test creating recommendation data structure."""
        recommendation_data = engine_service.create_recommendation_data(
            ai_result=sample_ai_result,
            github_profile_id=123,
            recommendation_type="professional",
            tone="professional",
            length="medium"
        )

        assert isinstance(recommendation_data, RecommendationCreate)
        assert recommendation_data.github_profile_id == 123
        assert recommendation_data.title == "Test Recommendation"
        assert recommendation_data.content == "This is a test recommendation content."
        assert recommendation_data.recommendation_type == "professional"
        assert recommendation_data.tone == "professional"
        assert recommendation_data.length == "medium"
        assert recommendation_data.word_count == 50
        assert recommendation_data.ai_model == "test-model"
        assert recommendation_data.generation_prompt == "Test prompt"

    @pytest.mark.asyncio
    async def test_generate_recommendation_options(self, engine_service, mock_ai_service, sample_github_data):
        """Test generating recommendation options."""
        # Mock AI service to return different results for each variation
        mock_ai_service.generate_recommendation.side_effect = [
            {
                "title": "Professional Recommendation",
                "content": "Professional content",
                "word_count": 100,
                "generation_parameters": {"model": "test-model"},
                "name": "Professional Option",
                "focus": "Professional tone",
                "explanation": "Best for formal business communications"
            },
            {
                "title": "Friendly Recommendation",
                "content": "Friendly content",
                "word_count": 80,
                "generation_parameters": {"model": "test-model"},
                "name": "Friendly Option",
                "focus": "Friendly tone",
                "explanation": "Best for networking and personal connections"
            },
            {
                "title": "Formal Recommendation",
                "content": "Formal content",
                "word_count": 120,
                "generation_parameters": {"model": "test-model"},
                "name": "Formal Option",
                "focus": "Formal tone",
                "explanation": "Best for academic and senior-level positions"
            },
            {
                "title": "Casual Recommendation",
                "content": "Casual content",
                "word_count": 60,
                "generation_parameters": {"model": "test-model"},
                "name": "Casual Option",
                "focus": "Casual tone",
                "explanation": "Best for startup and creative environments"
            }
        ]

        result = await engine_service.generate_recommendation_options(
            github_data=sample_github_data,
            base_recommendation_type="professional",
            base_tone="professional",
            base_length="medium"
        )

        assert isinstance(result, RecommendationOptionsResponse)
        assert len(result.options) == 4

        # Check that each option has the expected properties
        for i, option in enumerate(result.options):
            assert isinstance(option, RecommendationOption)
            assert option.id == i + 1
            assert "Recommendation" in option.title
            assert option.word_count > 0
            assert option.name is not None
            assert option.focus is not None
            assert option.explanation is not None

        # Verify AI service was called 4 times with different parameters
        assert mock_ai_service.generate_recommendation.call_count == 4

    @pytest.mark.asyncio
    async def test_generate_recommendation_options_with_params(self, engine_service, mock_ai_service, sample_github_data):
        """Test generating recommendation options with custom parameters."""
        mock_ai_service.generate_recommendation.return_value = {
            "title": "Test Option",
            "content": "Test content",
            "word_count": 50,
            "generation_parameters": {"model": "test-model"},
            "name": "Test Option",
            "focus": "Test focus",
            "explanation": "Test explanation"
        }

        result = await engine_service.generate_recommendation_options(
            github_data=sample_github_data,
            base_recommendation_type="technical",
            base_tone="casual",
            base_length="short",
            target_role="developer",
            specific_skills=["Python"]
        )

        assert isinstance(result, RecommendationOptionsResponse)
        assert len(result.options) == 4

        # Verify AI service was called with the custom parameters as base
        call_args = mock_ai_service.generate_recommendation.call_args_list[0][1]
        assert call_args["recommendation_type"] == "technical"
        assert call_args["target_role"] == "developer"
        assert call_args["specific_skills"] == ["Python"]

    def test_analyze_recommendation_quality_high_score(self, engine_service):
        """Test analyzing recommendation quality with high score."""
        content = "John is an excellent software developer with strong skills in Python, JavaScript, and React. He has built multiple web applications and demonstrates great problem-solving abilities. His GitHub profile shows consistent contributions and well-structured code."

        result = engine_service.analyze_recommendation_quality(content, 45)

        assert isinstance(result, dict)
        assert "quality_score" in result
        assert "issues" in result
        assert "suggestions" in result
        assert result["quality_score"] >= 40  # Should be decent score
        assert result["structure_score"] > 0

    def test_analyze_recommendation_quality_low_score(self, engine_service):
        """Test analyzing recommendation quality with low score."""
        content = "Good developer."  # Very short and lacks structure

        result = engine_service.analyze_recommendation_quality(content, 3)

        assert isinstance(result, dict)
        assert result["quality_score"] < 70  # Should be lower score
        assert len(result["issues"]) > 0  # Should have issues
        assert len(result["suggestions"]) > 0  # Should have suggestions

    def test_analyze_recommendation_quality_perfect_score(self, engine_service):
        """Test analyzing recommendation quality with perfect content."""
        content = ("John Doe is an exceptional software engineer with extensive experience in full-stack development. "
                  "His technical expertise includes Python, JavaScript, React, and Node.js. "
                  "John has successfully delivered multiple complex projects, demonstrating strong problem-solving skills "
                  "and the ability to work effectively in team environments. His GitHub contributions showcase clean, "
                  "well-documented code and consistent commitment to best practices.")

        result = engine_service.analyze_recommendation_quality(content, 85)

        assert isinstance(result, dict)
        assert result["quality_score"] <= 100
        assert result["structure_score"] > 10  # Good structure score

    @pytest.mark.asyncio
    async def test_create_recommendation_from_option(self, engine_service):
        """Test creating a recommendation from a selected option."""
        from unittest.mock import AsyncMock
        from sqlalchemy.ext.asyncio import AsyncSession

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock the Recommendation class
        with patch('app.services.recommendation_engine_service.Recommendation') as mock_recommendation_class:
            mock_recommendation = Mock()
            mock_recommendation.id = 456
            mock_recommendation_class.return_value = mock_recommendation

            # Mock RecommendationResponse
            with patch('app.services.recommendation_engine_service.RecommendationResponse') as mock_response_class:
                mock_response = Mock()
                mock_response_class.from_orm.return_value = mock_response

                option = RecommendationOption(
                    id=1,
                    name="Test Option",
                    title="Test Option",
                    content="Full content",
                    focus="Professional focus",
                    explanation="Best for professional communications",
                    word_count=50
                )

                result = await engine_service.create_recommendation_from_option(
                    db=mock_db,
                    github_profile_id=123,
                    option=option,
                    recommendation_type="professional"
                )

                assert result is not None
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()

    @pytest.mark.parametrize("content_length,expected_issues", [
        (5, ["Content is too short"]),
        (150, []),  # Normal length
        (600, ["Content is too long"]),  # Too long
    ])
    def test_analyze_recommendation_quality_length_analysis(self, engine_service, content_length, expected_issues):
        """Test recommendation quality analysis for different content lengths."""
        content = " ".join(["word"] * content_length)

        result = engine_service.analyze_recommendation_quality(content, content_length)

        for issue in expected_issues:
            assert issue in result["issues"]

    def test_analyze_recommendation_quality_no_structure(self, engine_service):
        """Test recommendation quality analysis for content with no structure."""
        content = "John is a good developer he knows python and javascript he works hard"

        result = engine_service.analyze_recommendation_quality(content, 12)

        assert "structure" in " ".join(result["issues"]).lower()
        assert result["structure_score"] <= 10  # Should have some structure but not great

    @pytest.mark.asyncio
    async def test_generate_recommendation_repo_only_context_filters_data(self, engine_service, mock_ai_service):
        """Test that repo_only context properly filters out general user data to prevent data leakage."""

        # Mock data with both general user profile and repository-specific info
        github_data_repo_only = {
            "user_data": {
                "github_username": "octocat",
                "full_name": "Octo Cat",
                "bio": "General bio about Octocat.",
                "company": "GitHub",
                "location": "San Francisco",
                "public_repos": 10,
                "followers": 100,
                "starred_technologies": {"languages": {"Python": 5}},
                "organizations": [{"login": "octo-org"}],
            },
            "repository_info": {
                "name": "test-repo",
                "full_name": "octocat/test-repo",
                "description": "A repository for testing.",
                "language": "TypeScript",
                "stars": 50,
                "forks": 10,
                "owner": {"login": "octocat"},
            },
            "repository_languages": [{"language": "TypeScript", "percentage": 80}],
            "repository_skills": {"technical_skills": ["React", "Node.js"], "frameworks": ["Express"]},
            "repository_commit_analysis": {
                "total_commits": 20,
                "excellence_areas": {"primary_strength": "code_quality"},
            },
            # General user data that should be ignored in repo_only mode
            "languages": [{"language": "Python", "percentage": 90}],
            "skills": {"technical_skills": ["Python", "Flask"]},
            "commit_analysis": {"total_commits": 500, "excellence_areas": {"primary_strength": "feature_development"}},
        }

        # Mock the AI service response
        mock_ai_service.generate_recommendation.return_value = {
            "options": [
                {
                    "id": 1,
                    "name": "Option 1",
                    "content": "Test recommendation content",
                    "title": "Test Title",
                    "word_count": 50,
                    "focus": "technical_expertise",
                }
            ],
            "generation_parameters": {},
            "generation_prompt": "mocked prompt"
        }

        # Call the service with repo_only context
        result = await engine_service.generate_recommendation(
            github_data=github_data_repo_only,
            recommendation_type="professional",
            tone="professional",
            length="medium",
            analysis_context_type="repo_only",
            repository_url="https://github.com/octocat/test-repo",
        )

        # Verify the AI service was called
        mock_ai_service.generate_recommendation.assert_called_once()

        # Get the arguments passed to the AI service
        call_args, call_kwargs = mock_ai_service.generate_recommendation.call_args
        filtered_github_data = call_args[0]  # First positional argument is github_data

        # Assert that general user data has been filtered out
        user_data = filtered_github_data.get("user_data", {})

        # These should be absent or empty in repo_only mode
        assert user_data.get("bio") is None or user_data.get("bio") == ""
        assert "starred_technologies" not in user_data
        assert "organizations" not in user_data
        assert user_data.get("company") is None or user_data.get("company") == ""
        assert user_data.get("location") is None or user_data.get("location") == ""
        assert user_data.get("public_repos") is None
        assert user_data.get("followers") is None

        # These should be present (essential identifying info)
        assert user_data.get("github_username") == "octocat"
        assert user_data.get("full_name") == "Octo Cat"

        # Repository-specific data should be used instead of general data
        languages = filtered_github_data.get("languages", [])
        assert len(languages) > 0
        assert languages[0]["language"] == "TypeScript"
        assert "Python" not in [lang["language"] for lang in languages]

        skills = filtered_github_data.get("skills", {})
        assert "React" in skills.get("technical_skills", [])
        assert "Flask" not in skills.get("technical_skills", [])

        commit_analysis = filtered_github_data.get("commit_analysis", {})
        assert commit_analysis.get("total_commits") == 20  # Repository-specific
        assert commit_analysis.get("excellence_areas", {}).get("primary_strength") == "code_quality"

        # Verify the result structure
        assert "options" in result
        assert len(result["options"]) > 0
        assert result["generation_parameters"]["model"] is not None
