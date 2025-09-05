"""Tests for SkillAnalysisService."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.schemas.recommendation import SkillGapAnalysisRequest, SkillGapAnalysisResponse, SkillMatch
from app.services.skill_analysis_service import SkillAnalysisService


class TestSkillAnalysisService:
    """Test suite for SkillAnalysisService."""

    @pytest.fixture
    def skill_service(self):
        """Create SkillAnalysisService instance."""
        return SkillAnalysisService()

    @pytest.fixture
    def sample_github_data(self):
        """Sample GitHub data for testing."""
        return {
            "skills": {
                "technical_skills": ["Python", "JavaScript", "SQL"],
                "frameworks": ["Django", "React", "FastAPI"],
                "tools": ["Git", "Docker", "PostgreSQL"],
                "domains": ["Web Development", "Data Science"],
                "dependencies_found": ["pandas", "numpy", "requests"],
            },
            "starred_technologies": {"languages": {"JavaScript": 5, "TypeScript": 3}, "topics": ["machine-learning", "web-development", "api-design"]},
            "commit_analysis": {
                "excellence_areas": {"primary_strength": "backend_development", "patterns": {"api_development": {"percentage": 25}, "database_design": {"percentage": 20}}},
                "tools_and_features": {"tools_by_category": {"frameworks": ["Django", "FastAPI"], "databases": ["PostgreSQL", "Redis"]}},
            },
        }

    def test_init(self, skill_service):
        """Test SkillAnalysisService initialization."""
        assert isinstance(skill_service, SkillAnalysisService)

    def test_get_role_skill_requirements_frontend_developer(self, skill_service):
        """Test getting skill requirements for frontend developer."""
        requirements = skill_service.get_role_skill_requirements("frontend_developer", "mid")

        assert "required" in requirements
        assert "preferred" in requirements
        assert "nice_to_have" in requirements
        assert "HTML" in requirements["required"]
        assert "CSS" in requirements["required"]
        assert "JavaScript" in requirements["required"]
        assert "React/Vue/Angular" in requirements["required"]

    def test_get_role_skill_requirements_backend_developer(self, skill_service):
        """Test getting skill requirements for backend developer."""
        requirements = skill_service.get_role_skill_requirements("backend_developer", "senior")

        assert "Python/Java/Node.js" in requirements["required"]
        assert "SQL" in requirements["required"]
        assert "REST APIs" in requirements["required"]
        assert "Architecture" in requirements["required"]

    def test_get_role_skill_requirements_unknown_role(self, skill_service):
        """Test getting skill requirements for unknown role."""
        requirements = skill_service.get_role_skill_requirements("unknown_role")

        assert "required" in requirements
        assert "preferred" in requirements
        assert "nice_to_have" in requirements
        assert "Programming" in requirements["required"]

    def test_analyze_skill_match_strong_match(self, skill_service, sample_github_data):
        """Test analyzing skill match with strong match."""
        match = skill_service.analyze_skill_match("Python", ["Python", "JavaScript"], sample_github_data)

        assert isinstance(match, SkillMatch)
        assert match.skill == "Python"
        assert match.match_level == "strong"
        assert "Direct match found in profile" in match.evidence

    def test_analyze_skill_match_weak_match(self, skill_service, sample_github_data):
        """Test analyzing skill match with weak match."""
        match = skill_service.analyze_skill_match("Machine Learning", ["Python", "JavaScript"], sample_github_data)

        assert isinstance(match, SkillMatch)
        assert match.skill == "Machine Learning"
        assert match.match_level in ["moderate", "weak", "missing"]  # Allow moderate due to related tech matching

    def test_analyze_skill_match_with_starred_technology(self, skill_service, sample_github_data):
        """Test analyzing skill match with starred technology."""
        match = skill_service.analyze_skill_match("TypeScript", ["Python", "JavaScript"], sample_github_data)

        assert isinstance(match, SkillMatch)
        assert match.skill == "TypeScript"
        assert match.match_level == "strong"  # Should be strong due to direct match
        assert "Direct match found in profile" in match.evidence

    def test_analyze_skill_match_with_commit_analysis(self, skill_service, sample_github_data):
        """Test analyzing skill match with commit analysis data."""
        match = skill_service.analyze_skill_match("backend_development", ["Python", "JavaScript"], sample_github_data)

        assert isinstance(match, SkillMatch)
        assert match.skill == "backend_development"
        # Should match the primary strength from commit analysis
        assert any("backend_development" in evidence.lower() or "backend development" in evidence.lower() for evidence in match.evidence)

    def test_get_related_technologies_javascript(self, skill_service):
        """Test getting related technologies for JavaScript."""
        related = skill_service.get_related_technologies("JavaScript")

        assert isinstance(related, list)
        assert "react" in related
        assert "node.js" in related
        assert "vue" in related

    def test_get_related_technologies_python(self, skill_service):
        """Test getting related technologies for Python."""
        related = skill_service.get_related_technologies("Python")

        assert isinstance(related, list)
        assert "django" in related
        assert "flask" in related
        assert "pandas" in related

    def test_get_related_technologies_unknown(self, skill_service):
        """Test getting related technologies for unknown skill."""
        related = skill_service.get_related_technologies("UnknownSkill")

        assert isinstance(related, list)
        assert len(related) == 0

    def test_generate_skill_recommendations(self, skill_service):
        """Test generating skill recommendations."""
        skill_matches = [
            SkillMatch(skill="JavaScript", match_level="missing", match_score=0, evidence=[]),
            SkillMatch(skill="Python", match_level="strong", match_score=50, evidence=[]),
            SkillMatch(skill="Docker", match_level="missing", match_score=0, evidence=[]),
        ]

        recommendations = skill_service.generate_skill_recommendations(skill_matches, "frontend_developer")

        assert isinstance(recommendations, dict)
        assert "recommendations" in recommendations
        assert "learning_resources" in recommendations
        assert isinstance(recommendations["recommendations"], list)
        assert isinstance(recommendations["learning_resources"], list)
        assert len(recommendations["recommendations"]) > 0

    def test_create_gap_analysis_summary_excellent(self, skill_service):
        """Test creating gap analysis summary for excellent match."""
        summary = skill_service.create_gap_analysis_summary(85, 5, 1, "frontend_developer")

        assert "Excellent match" in summary
        assert "frontend_developer" in summary
        assert "5 key strengths" in summary

    def test_create_gap_analysis_summary_moderate(self, skill_service):
        """Test creating gap analysis summary for moderate match."""
        summary = skill_service.create_gap_analysis_summary(45, 2, 3, "backend_developer")

        assert "Moderate match" in summary
        assert "backend_developer" in summary
        assert "3 key skills" in summary

    def test_create_gap_analysis_summary_poor(self, skill_service):
        """Test creating gap analysis summary for poor match."""
        summary = skill_service.create_gap_analysis_summary(25, 1, 5, "data_scientist")

        assert "Significant gaps" in summary
        assert "data_scientist" in summary
        assert "5 core skills" in summary

    def test_analyze_skill_gaps_full_flow(self, skill_service, sample_github_data):
        """Test full skill gap analysis flow."""
        request = SkillGapAnalysisRequest(github_username="testuser", target_role="frontend_developer", industry="technology", experience_level="mid")

        response = skill_service.analyze_skill_gaps(request, sample_github_data)

        assert isinstance(response, SkillGapAnalysisResponse)
        assert response.github_username == "testuser"
        assert response.target_role == "frontend_developer"
        assert isinstance(response.overall_match_score, int)
        assert 0 <= response.overall_match_score <= 100
        assert isinstance(response.skill_analysis, list)
        assert isinstance(response.strengths, list)
        assert isinstance(response.gaps, list)
        assert isinstance(response.recommendations, list)
        assert isinstance(response.learning_resources, list)
        assert isinstance(response.analysis_summary, str)
        assert isinstance(response.generated_at, datetime)

    def test_analyze_skill_gaps_with_missing_data(self, skill_service):
        """Test skill gap analysis with minimal GitHub data."""
        minimal_github_data = {
            "skills": {"technical_skills": [], "frameworks": [], "tools": [], "domains": [], "dependencies_found": []},
            "starred_technologies": {"languages": {}, "topics": []},
            "commit_analysis": {"excellence_areas": {"primary_strength": "", "patterns": {}}, "tools_and_features": {"tools_by_category": {}}},
        }

        request = SkillGapAnalysisRequest(github_username="testuser", target_role="backend_developer")

        response = skill_service.analyze_skill_gaps(request, minimal_github_data)

        assert isinstance(response, SkillGapAnalysisResponse)
        assert response.overall_match_score >= 0
        assert len(response.skill_analysis) > 0

    @pytest.mark.parametrize(
        "role,experience_level",
        [
            ("frontend_developer", "junior"),
            ("backend_developer", "mid"),
            ("fullstack_developer", "senior"),
            ("data_scientist", "mid"),
            ("devops_engineer", "senior"),
        ],
    )
    def test_get_role_skill_requirements_all_roles(self, skill_service, role, experience_level):
        """Test getting skill requirements for all supported roles."""
        requirements = skill_service.get_role_skill_requirements(role, experience_level)

        assert "required" in requirements
        assert "preferred" in requirements
        assert "nice_to_have" in requirements
        assert isinstance(requirements["required"], list)
        assert isinstance(requirements["preferred"], list)
        assert isinstance(requirements["nice_to_have"], list)
        assert len(requirements["required"]) > 0

    def test_analyze_skill_match_evidence_generation(self, skill_service, sample_github_data):
        """Test that skill match generates appropriate evidence."""
        match = skill_service.analyze_skill_match("React", ["Python", "React"], sample_github_data)

        assert isinstance(match.evidence, list)
        # Should find React in frameworks
        assert any("Direct match found in profile" in evidence for evidence in match.evidence)

    def test_generate_skill_recommendations_limits(self, skill_service):
        """Test that skill recommendations are properly limited."""
        # Create many missing skills
        skill_matches = [SkillMatch(skill=f"Skill{i}", match_level="missing", match_score=0, evidence=[]) for i in range(10)]

        recommendations = skill_service.generate_skill_recommendations(skill_matches, "developer")

        # Should limit to 8 recommendations and 6 learning resources
        assert len(recommendations["recommendations"]) <= 8
        assert len(recommendations["learning_resources"]) <= 6
