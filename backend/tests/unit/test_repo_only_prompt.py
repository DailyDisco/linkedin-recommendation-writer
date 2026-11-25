#!/usr/bin/env python3
"""Tests for the strict repo_only prompt behaviour.

The prompt service guards repo_only requests with fail-fast contamination
checks: general profile data must never reach a repository-only prompt. Data
that still carries profile fields is rejected outright (the caller is expected
to hand over the payload produced by the repo_only data merge), while clean,
repository-specific data produces a strict repository-focused prompt.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pytest

from app.services.ai.prompt_service import PromptService

# Repository-specific payload as produced by the repo_only data merge: identity
# fields only plus repository-derived data.
REPO_ONLY_DATA = {
    "user_data": {"github_username": "testuser", "full_name": "Test User"},
    "repository_info": {
        "name": "smart-gym",
        "description": "A fitness tracking application built with React and Node.js",
        "language": "JavaScript",
        "html_url": "https://github.com/testuser/smart-gym",
    },
    "languages": [{"language": "JavaScript", "percentage": 70.0}, {"language": "TypeScript", "percentage": 20.0}, {"language": "CSS", "percentage": 10.0}],
    "skills": {"technical_skills": ["JavaScript", "React", "Node.js", "Express"], "frameworks": ["React", "Express"], "tools": ["Git", "Docker"]},
    "commit_analysis": {"total_commits": 45, "patterns": {"most_active_month": "December 2024"}},
}

# Same payload with general profile data mixed in - must be rejected.
CONTAMINATED_DATA = {
    **REPO_ONLY_DATA,
    "user_data": {
        "github_username": "testuser",
        "full_name": "Test User",
        "bio": "Software developer with 5 years experience",
        "company": "Acme",
        "location": "Berlin",
    },
}

PROFILE_ONLY_DATA = {
    "user_data": {"github_username": "testuser", "full_name": "Test User"},
    "repositories": [{"name": "smart-gym"}],
    "languages": [{"language": "Python", "percentage": 40.0}, {"language": "JavaScript", "percentage": 35.0}],
    "skills": {
        "technical_skills": ["Python", "JavaScript", "Java", "C++"],
        "frameworks": ["Django", "React", "Spring"],
        "tools": ["Git", "Docker", "AWS"],
        "domains": ["Web Development", "Data Science"],
    },
}


def test_repo_only_prompt():
    """repo_only prompts focus on the repository and exclude general profile sections."""
    prompt_service = PromptService()

    repo_only_prompt = prompt_service.build_prompt(
        github_data=REPO_ONLY_DATA,
        analysis_context_type="repo_only",
        repository_url="https://github.com/testuser/smart-gym",
    )

    # Repository-specific instructions and content are present
    assert "CRITICAL: ONLY DISCUSS THIS SPECIFIC REPOSITORY" in repo_only_prompt
    assert "smart-gym" in repo_only_prompt
    assert "https://github.com/testuser/smart-gym" in repo_only_prompt
    assert "ONLY mention work, skills, and contributions from THIS SPECIFIC REPOSITORY" in repo_only_prompt

    # Repository technologies and commit count are rendered (language dicts are
    # expanded to language names, not stringified)
    assert "JavaScript" in repo_only_prompt
    assert "React" in repo_only_prompt
    assert "Number of commits to this repository: 45" in repo_only_prompt
    assert "{'language': 'JavaScript'}" not in repo_only_prompt

    # General profile sections are absent
    assert "Here's what I know about them:" not in repo_only_prompt
    assert "What their overall coding work shows:" not in repo_only_prompt


def test_repo_only_prompt_rejects_profile_data():
    """repo_only prompts refuse to build when general profile data leaks in."""
    prompt_service = PromptService()

    with pytest.raises(ValueError, match="[Pp]rofile data contamination"):
        prompt_service.build_prompt(
            github_data=CONTAMINATED_DATA,
            analysis_context_type="repo_only",
            repository_url="https://github.com/testuser/smart-gym",
        )


def test_profile_prompt_keeps_general_info():
    """profile prompts keep the general sections that repo_only prompts exclude."""
    prompt_service = PromptService()

    profile_prompt = prompt_service.build_prompt(
        github_data=PROFILE_ONLY_DATA,
        analysis_context_type="profile",
    )

    assert "Here's what I know about them:" in profile_prompt
    assert "Test User" in profile_prompt


if __name__ == "__main__":
    test_repo_only_prompt()
    test_repo_only_prompt_rejects_profile_data()
    test_profile_prompt_keeps_general_info()
    print("✅ repo_only prompt tests passed")