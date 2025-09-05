#!/usr/bin/env python3
"""Test script to verify that the AI recommendation service correctly filters data based on analysis context."""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.prompt_service import PromptService


def test_repo_only_context():
    """Test that repo_only context doesn't include profile data."""
    print("🧪 Testing repo_only context...")

    prompt_service = PromptService()

    # Simulate filtered data for repo_only context (user_data and skills are empty)
    github_data = {
        "user_data": {},  # Empty for repo_only
        "languages": [
            {"language": "Python", "percentage": 60.0, "lines_of_code": 1500, "repository_count": 1},
            {"language": "JavaScript", "percentage": 40.0, "lines_of_code": 1000, "repository_count": 1},
        ],
        "skills": {},  # Empty for repo_only
        "commit_analysis": {"total_commits": 25, "excellence_areas": {"primary_strength": "problem_solving"}},
        "repository_info": {
            "name": "my-awesome-project",
            "description": "A great project for testing",
            "language": "Python",
            "owner": {"login": "testuser", "avatar_url": "https://example.com/avatar"},
        },
        "analysis_context_type": "repo_only",
    }

    try:
        prompt = prompt_service.build_prompt(
            github_data=github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium",
            analysis_context_type="repo_only",
            repository_url="https://github.com/testuser/my-awesome-project",
        )

        # Check that the prompt contains repository-specific content
        assert "CRITICAL: ONLY DISCUSS THIS SPECIFIC REPOSITORY" in prompt
        assert "my-awesome-project" in prompt
        assert "testuser" in prompt

        # Check that profile-specific content is NOT included
        assert "starred" not in prompt.lower()  # No starred repos
        assert "organizations" not in prompt.lower()  # No organizations
        assert "overall coding work" not in prompt.lower()  # No general profile insights

        print("✅ repo_only context test PASSED - no profile data found in prompt")
        return True

    except Exception as e:
        print(f"❌ repo_only context test FAILED: {e}")
        return False


def test_profile_context():
    """Test that profile context includes all profile data."""
    print("🧪 Testing profile context...")

    prompt_service = PromptService()

    # Simulate full profile data
    github_data = {
        "user_data": {
            "github_username": "testuser",
            "full_name": "Test User",
            "starred_technologies": {"total_starred": 150, "languages": {"Python": 50, "JavaScript": 30}, "technology_focus": {"web-development": 40}},
            "organizations": [{"name": "Tech Corp", "login": "techcorp"}, {"name": "Open Source Org", "login": "opensource"}],
        },
        "languages": [{"language": "Python", "percentage": 60.0}, {"language": "JavaScript", "percentage": 40.0}],
        "skills": {"technical_skills": ["Python", "JavaScript", "React", "Django"], "frameworks": ["Django", "React", "FastAPI"], "domains": ["Web Development", "API Design"]},
        "commit_analysis": {"total_commits": 150, "excellence_areas": {"primary_strength": "problem_solving"}},
        "analysis_context_type": "profile",
    }

    try:
        prompt = prompt_service.build_prompt(github_data=github_data, recommendation_type="professional", tone="professional", length="medium", analysis_context_type="profile")

        # Check that the prompt contains profile-specific content
        assert "testuser" in prompt
        assert "Test User" in prompt
        assert "shown interest in" in prompt.lower()
        assert "organizations" in prompt.lower()
        assert "programming languages they work with" in prompt.lower()

        # Check that repository-specific restrictions are NOT included
        assert "CRITICAL: ONLY DISCUSS THIS SPECIFIC REPOSITORY" not in prompt

        print("✅ profile context test PASSED - profile data found in prompt")
        return True

    except Exception as e:
        import traceback

        print(f"❌ profile context test FAILED: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False


def test_repository_contributor_context():
    """Test that repository_contributor context blends both profile and repo data."""
    print("🧪 Testing repository_contributor context...")

    prompt_service = PromptService()

    # Simulate blended data for repository_contributor
    github_data = {
        "user_data": {"github_username": "testuser", "full_name": "Test User"},
        "languages": [{"language": "Python", "percentage": 60.0}, {"language": "JavaScript", "percentage": 40.0}],
        "skills": {"technical_skills": ["Python", "JavaScript", "React"], "frameworks": ["Django", "React"], "domains": ["Web Development"]},
        "commit_analysis": {"total_commits": 25, "excellence_areas": {"primary_strength": "problem_solving"}},
        "repository_info": {"name": "my-awesome-project", "description": "A great project", "language": "Python", "owner": {"login": "testuser"}},
        "analysis_context_type": "repository_contributor",
    }

    try:
        prompt = prompt_service.build_prompt(
            github_data=github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium",
            analysis_context_type="repository_contributor",
            repository_url="https://github.com/testuser/my-awesome-project",
        )

        # Check that the prompt contains both profile and repository content
        assert "testuser" in prompt
        assert "my-awesome-project" in prompt
        assert "Balance their specific contributions" in prompt
        assert "demonstrates their broader skills" in prompt

        # Check that extreme repo_only restrictions are NOT included
        assert "CRITICAL: ONLY DISCUSS THIS SPECIFIC REPOSITORY" not in prompt

        print("✅ repository_contributor context test PASSED - blended data found in prompt")
        return True

    except Exception as e:
        print(f"❌ repository_contributor context test FAILED: {e}")
        return False


def test_refinement_prompt_repo_only():
    """Test that refinement prompt handles repo_only context."""
    print("🧪 Testing refinement prompt with repo_only context...")

    prompt_service = PromptService()

    # Simulate filtered data for repo_only context
    github_data = {"user_data": {}, "repository_info": {"owner": {"login": "testuser"}}, "analysis_context_type": "repo_only"}  # Empty for repo_only

    original_content = "This is a test recommendation."
    refinement_instructions = "Make it more professional."

    try:
        prompt = prompt_service.build_refinement_prompt_for_regeneration(
            original_content=original_content,
            refinement_instructions=refinement_instructions,
            github_data=github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium",
            analysis_context_type="repo_only",
            repository_url="https://github.com/testuser/my-awesome-project",
        )

        # Check that the prompt contains the correct username from repository owner
        assert "testuser" in prompt
        assert "the developer" not in prompt  # Should not fall back to generic

        print("✅ refinement prompt repo_only test PASSED")
        return True

    except Exception as e:
        print(f"❌ refinement prompt repo_only test FAILED: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting context filtering tests...\n")

    tests = [test_repo_only_context, test_profile_context, test_repository_contributor_context, test_refinement_prompt_repo_only]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Context filtering is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
