#!/usr/bin/env python3
"""
Test script to validate repository data extraction for smart-gym repository.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai.prompt_service import PromptService

def test_smart_gym_repo_only():
    """Test repo_only prompt generation with smart-gym repository data."""

    prompt_service = PromptService()

    # Mock GitHub data for smart-gym repository (based on actual GitHub data)
    smart_gym_data = {
        "user_data": {
            "github_username": "diego",
            "full_name": "Diego",
            "bio": "Full-stack developer with experience in various technologies",
            "company": "Tech Corp",
            "location": "San Francisco",
            "starred_technologies": {
                "total_starred": 100,
                "languages": {"javascript": 30, "typescript": 25, "python": 20, "go": 15},
                "technology_focus": {"web-development": 40, "backend": 20, "data-science": 15}
            },
            "organizations": [
                {"name": "OpenSourceOrg", "login": "opensourceorg"}
            ]
        },
        "languages": [
            {"language": "TypeScript", "bytes": 50000},
            {"language": "JavaScript", "bytes": 10000},
            {"language": "Go", "bytes": 20000},  # This should NOT be included in repo_only
            {"language": "Python", "bytes": 15000}  # This should NOT be included in repo_only
        ],
        "skills": {
            "technical_skills": ["TypeScript", "JavaScript", "Go", "Python", "React"],  # Go/Python should NOT be included
            "frameworks": ["React", "Express", "Fiber", "Django"],  # Fiber/Django should NOT be included
            "domains": ["Web Development", "Backend Development"]
        },
        "repository_info": {
            "name": "smart-gym",
            "description": "A comprehensive gym management system built with modern web technologies",
            "language": "TypeScript",
            "owner": {"login": "rajakrishna"},
            "url": "https://github.com/rajakrishna/smart-gym"
        },
        "repository_languages": [
            {"language": "TypeScript", "bytes": 50000, "percentage": 98.7},
            {"language": "CSS", "bytes": 600, "percentage": 1.2},
            {"language": "JavaScript", "bytes": 100, "percentage": 0.1}
        ],
        "repository_skills": {
            "technical_skills": ["TypeScript", "JavaScript", "CSS"],
            "frameworks": ["React", "Next.js"],  # Only React and Next.js for this repo
            "domains": ["Web Development", "Frontend Development"]
        },
        "repository_commits": [
            {"message": "Add user authentication component", "date": "2024-01-01T00:00:00Z"},
            {"message": "Implement gym class booking system", "date": "2024-01-02T00:00:00Z"},
            {"message": "Fix responsive design issues", "date": "2024-01-03T00:00:00Z"}
        ],
        "repository_commit_analysis": {
            "total_commits": 15,
            "excellence_areas": {
                "primary_strength": "frontend_development"
            }
        },
        "contributor_info": {
            "contributions": 15,
            "full_name": "Diego"
        }
    }

    # Generate repo_only prompt
    print("🧪 TESTING SMART-GYM REPO_ONLY PROMPT")
    print("=" * 60)

    repo_only_prompt = prompt_service.build_prompt(
        github_data=smart_gym_data,
        recommendation_type="professional",
        tone="professional",
        length="medium",
        analysis_context_type="repo_only",
        repository_url="https://github.com/rajakrishna/smart-gym"
    )

    print("REPO_ONLY PROMPT FOR SMART-GYM:")
    print("=" * 60)
    print(repo_only_prompt)
    print("=" * 60)

    # Validate that only smart-gym technologies are mentioned
    validation_results = {
        "contains_typescript": "TypeScript" in repo_only_prompt,
        "contains_javascript": "JavaScript" in repo_only_prompt,
        "contains_css": "CSS" in repo_only_prompt,
        "contains_react": "React" in repo_only_prompt,
        "contains_nextjs": "Next.js" in repo_only_prompt,
        "excludes_go": "Go" not in repo_only_prompt and "Golang" not in repo_only_prompt.lower(),
        "excludes_python": "Python" not in repo_only_prompt,
        "excludes_fiber": "Fiber" not in repo_only_prompt,
        "excludes_django": "Django" not in repo_only_prompt,
        "excludes_general_starred_tech": "python" not in repo_only_prompt.lower() and "data-science" not in repo_only_prompt.lower() and "backend" not in repo_only_prompt.lower(),
        "contains_repo_name": "smart-gym" in repo_only_prompt,
        "contains_correct_owner": "rajakrishna" in repo_only_prompt,
        "excludes_company": "Tech Corp" not in repo_only_prompt,
        "excludes_location": "San Francisco" not in repo_only_prompt
    }

    print("\nVALIDATION RESULTS FOR SMART-GYM:")
    print("-" * 50)
    for test_name, result in validation_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    # Summary
    passed_tests = sum(validation_results.values())
    total_tests = len(validation_results)
    success_rate = (passed_tests / total_tests) * 100

    print(f"\n📊 SMART-GYM TEST SUMMARY: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

    if success_rate >= 90:
        print("🎉 SMART-GYM REPO_ONLY ISOLATION: SUCCESS!")
        return True
    else:
        print("⚠️  SMART-GYM REPO_ONLY ISOLATION: ISSUES DETECTED")
        return False

if __name__ == "__main__":
    success = test_smart_gym_repo_only()
    sys.exit(0 if success else 1)
