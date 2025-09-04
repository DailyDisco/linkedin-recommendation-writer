#!/usr/bin/env python3
"""
Test script to validate repo_only prompt generation and ensure no general profile data leakage.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai.prompt_service import PromptService

def test_repo_only_prompt_generation():
    """Test that repo_only prompts exclude general profile data."""

    prompt_service = PromptService()

    # Mock GitHub data with general profile information
    github_data_with_general_profile = {
        "user_data": {
            "github_username": "johndoe",
            "full_name": "John Doe",
            "bio": "Full-stack developer with 5 years of experience",
            "company": "Tech Corp",
            "location": "San Francisco",
            "starred_technologies": {
                "total_starred": 50,
                "languages": {"javascript": 20, "python": 15},
                "technology_focus": {"web-development": 25, "machine-learning": 10}
            },
            "organizations": [
                {"name": "OpenSourceOrg", "login": "opensourceorg"},
                {"name": "TechCommunity", "login": "techcommunity"}
            ]
        },
        "languages": [
            {"language": "JavaScript", "bytes": 10000},
            {"language": "Python", "bytes": 8000},
            {"language": "TypeScript", "bytes": 5000}
        ],
        "skills": {
            "technical_skills": ["JavaScript", "React", "Node.js", "Python", "Django"],
            "frameworks": ["React", "Django", "Express"],
            "domains": ["Web Development", "API Development"]
        },
        "commit_analysis": {
            "total_commits": 150,
            "excellence_areas": {
                "primary_strength": "full_stack_development",
                "patterns": {
                    "feature_development": {"percentage": 35},
                    "bug_fixing": {"percentage": 25}
                }
            }
        },
        "repository_info": {
            "name": "awesome-project",
            "description": "A cool web application",
            "language": "JavaScript",
            "owner": {"login": "repoowner"},
            "url": "https://github.com/repoowner/awesome-project"
        },
        "repository_languages": [
            {"language": "JavaScript", "bytes": 5000},
            {"language": "HTML", "bytes": 2000}
        ],
        "repository_skills": {
            "technical_skills": ["JavaScript", "React", "CSS"],
            "frameworks": ["React"],
            "domains": ["Frontend Development"]
        },
        "repository_commits": [
            {"message": "Add user authentication feature", "date": "2024-01-01T00:00:00Z"},
            {"message": "Fix login bug", "date": "2024-01-02T00:00:00Z"}
        ],
        "repository_commit_analysis": {
            "total_commits": 25,
            "excellence_areas": {
                "primary_strength": "frontend_development"
            }
        },
        "contributor_info": {
            "contributions": 25,
            "full_name": "John Doe"
        }
    }

    # Test 1: Generate repo_only prompt
    print("🧪 TEST 1: Generating repo_only prompt...")
    repo_only_prompt = prompt_service.build_prompt(
        github_data=github_data_with_general_profile,
        recommendation_type="professional",
        tone="professional",
        length="medium",
        analysis_context_type="repo_only",
        repository_url="https://github.com/repoowner/awesome-project"
    )

    print("✅ REPO_ONLY PROMPT GENERATED")
    print("=" * 60)
    print(repo_only_prompt)
    print("=" * 60)

    # Test 2: Generate profile prompt for comparison
    print("\n🧪 TEST 2: Generating profile prompt for comparison...")
    profile_prompt = prompt_service.build_prompt(
        github_data=github_data_with_general_profile,
        recommendation_type="professional",
        tone="professional",
        length="medium",
        analysis_context_type="profile"
    )

    print("✅ PROFILE PROMPT GENERATED")
    print("=" * 60)
    print(profile_prompt[:500] + "..." if len(profile_prompt) > 500 else profile_prompt)
    print("=" * 60)

    # Test 3: Validate repo_only prompt exclusions
    print("\n🧪 TEST 3: Validating repo_only prompt exclusions...")

    validation_results = {
        "contains_repository_name": "awesome-project" in repo_only_prompt,
        "contains_repo_url": "https://github.com/repoowner/awesome-project" in repo_only_prompt,
        "contains_repo_skills": "JavaScript" in repo_only_prompt and "React" in repo_only_prompt,
        "includes_person_username": "johndoe" in repo_only_prompt,
        "excludes_general_bio": "Full-stack developer" not in repo_only_prompt,
        "excludes_company": "Tech Corp" not in repo_only_prompt,
        "excludes_location": "San Francisco" not in repo_only_prompt,
        "excludes_general_profile_tech": not any(tech in repo_only_prompt.lower() for tech in ["python", "web-development", "machine-learning"]) and "django" not in repo_only_prompt.lower(),
        "excludes_organizations": "OpenSourceOrg" not in repo_only_prompt,
        "excludes_general_languages": "Python" not in repo_only_prompt or "Django" not in repo_only_prompt,
        "contains_repo_only_instructions": "ONLY DISCUSS THIS SPECIFIC REPOSITORY" in repo_only_prompt,
        "contains_strict_warnings": "DO NOT mention any work outside" in repo_only_prompt or "DO NOT reference any other projects" in repo_only_prompt,
        "uses_person_username": "johndoe" in repo_only_prompt
    }

    print("VALIDATION RESULTS:")
    print("-" * 40)
    for test_name, result in validation_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    # Summary
    passed_tests = sum(validation_results.values())
    total_tests = len(validation_results)
    success_rate = (passed_tests / total_tests) * 100

    print(f"\n📊 TEST SUMMARY: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

    if success_rate >= 90:
        print("🎉 REPO_ONLY IMPLEMENTATION: SUCCESS!")
        return True
    else:
        print("⚠️  REPO_ONLY IMPLEMENTATION: ISSUES DETECTED")
        return False

if __name__ == "__main__":
    success = test_repo_only_prompt_generation()
    sys.exit(0 if success else 1)
