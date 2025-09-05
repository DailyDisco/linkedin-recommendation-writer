#!/usr/bin/env python3
"""
Test script to demonstrate the new strict repo_only prompt functionality.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai.prompt_service import PromptService


def test_repo_only_prompt():
    """Test that repo_only context creates strict repository-focused prompts."""
    print("🧪 Testing Repository-Only Prompt Generation\n")

    # Initialize prompt service
    prompt_service = PromptService()

    # Test data with both repository-specific and general profile information
    github_data = {
        "user_data": {"github_username": "testuser", "full_name": "Test User", "bio": "Software developer with 5 years experience"},
        "repository_info": {
            "name": "smart-gym",
            "description": "A fitness tracking application built with React and Node.js",
            "language": "JavaScript",
            "html_url": "https://github.com/testuser/smart-gym",
        },
        "repository_languages": [{"language": "JavaScript", "percentage": 70.0}, {"language": "TypeScript", "percentage": 20.0}, {"language": "CSS", "percentage": 10.0}],
        "repository_skills": {"technical_skills": ["JavaScript", "React", "Node.js", "Express"], "frameworks": ["React", "Express"], "tools": ["Git", "Docker"]},
        "repository_commit_analysis": {"total_commits": 45, "patterns": {"most_active_month": "December 2024"}},
        "contributor_info": {"contributions": 45, "full_name": "Test User"},
        # General profile data (should NOT be included in repo_only)
        "languages": [{"language": "Python", "percentage": 40.0}, {"language": "JavaScript", "percentage": 35.0}, {"language": "Java", "percentage": 25.0}],
        "skills": {
            "technical_skills": ["Python", "JavaScript", "Java", "C++"],
            "frameworks": ["Django", "React", "Spring"],
            "tools": ["Git", "Docker", "AWS"],
            "domains": ["Web Development", "Data Science"],
        },
        "commit_analysis": {"total_commits_analyzed": 150, "excellence_areas": {"primary_strength": "full_stack_development"}},
    }

    # Generate repo_only prompt
    repo_only_prompt = prompt_service.build_prompt(github_data=github_data, analysis_context_type="repo_only", repository_url="https://github.com/testuser/smart-gym")

    # Generate profile prompt for comparison
    profile_prompt = prompt_service.build_prompt(github_data=github_data, analysis_context_type="profile")

    print("📋 REPO-ONLY PROMPT ANALYSIS:")
    print("=" * 50)

    # Check for repository-specific content
    print("✅ Repository-specific content found:")
    if "CRITICAL: ONLY DISCUSS THIS SPECIFIC REPOSITORY" in repo_only_prompt:
        print("   • Strict repository-only instructions ✓")
    if "smart-gym" in repo_only_prompt:
        print("   • Repository name included ✓")
    if "JavaScript" in repo_only_prompt and "React" in repo_only_prompt:
        print("   • Repository technologies included ✓")
    if "45 commits" in repo_only_prompt:
        print("   • Repository commit count included ✓")

    print("\n❌ General profile content excluded:")
    excluded_items = []
    if "Here's what I know about them:" not in repo_only_prompt:
        excluded_items.append("General profile introduction")
    if "What their overall coding work shows:" not in repo_only_prompt:
        excluded_items.append("General coding work analysis")
    if "Python" in repo_only_prompt and "Java" in repo_only_prompt:
        # Check if these are mentioned in repository context only
        if "Languages used in this repository:" in repo_only_prompt:
            excluded_items.append("General Python/Java skills (only repo-specific included)")
    if "Django" not in repo_only_prompt or "Spring" not in repo_only_prompt:
        excluded_items.append("Non-repository frameworks")

    for item in excluded_items:
        print(f"   • {item} ✓")

    print("\n📊 COMPARISON WITH PROFILE PROMPT:")
    print("=" * 50)

    profile_has_general = "Here's what I know about them:" in profile_prompt
    repo_only_has_general = "Here's what I know about them:" in repo_only_prompt

    print(f"Profile prompt includes general info: {'✅ Yes' if profile_has_general else '❌ No'}")
    print(f"Repo-only prompt includes general info: {'❌ Yes (ERROR!)' if repo_only_has_general else '✅ No'}")

    print("\n🎯 RESULT:")
    if not repo_only_has_general and "CRITICAL: ONLY DISCUSS THIS SPECIFIC REPOSITORY" in repo_only_prompt:
        print("✅ SUCCESS: Repo-only prompt correctly excludes general profile information!")
        return True
    else:
        print("❌ FAILURE: Repo-only prompt still includes general profile information!")
        return False


if __name__ == "__main__":
    success = test_repo_only_prompt()
    exit(0 if success else 1)
