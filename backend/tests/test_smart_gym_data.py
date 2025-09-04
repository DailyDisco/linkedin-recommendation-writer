#!/usr/bin/env python3
"""
Test script to validate repo_only prompt generation and ensure no general profile data leakage.
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
    # This simulates the FILTERED data that should reach the AI in repo_only mode
    # The RecommendationService._get_or_create_github_profile_data method should filter out general profile data
    smart_gym_data = {
        "user_data": {
            "github_username": "diego",
            "login": "diego",
            "full_name": "Diego",
            # FILTERED OUT: bio, company, location, followers, public_repos, organizations, starred_technologies
        },
        # FILTERED OUT: "repositories", "languages", "skills", "commit_analysis", "commits", "starred_technologies", "organizations"

        # ONLY repository-specific data should be included:
        "repository_info": {
            "name": "smart-gym",
            "full_name": "rajakrishna/smart-gym",
            "description": "A comprehensive gym management system built with modern web technologies",
            "language": "TypeScript",
            "stars": 50,
            "forks": 10,
            "url": "https://github.com/rajakrishna/smart-gym",
            "owner": {"login": "rajakrishna", "avatar_url": "", "html_url": ""}
        },
        "repository_languages": [
            {"language": "TypeScript", "percentage": 98.7},
            {"language": "CSS", "percentage": 1.2},
            {"language": "JavaScript", "percentage": 0.1},
        ],
        "repository_skills": {
            "technical_skills": ["TypeScript", "JavaScript", "CSS", "HTML", "Frontend Development"],
            "frameworks": ["React", "Next.js", "TailwindCSS"],
            "tools": ["Git", "Vercel"]
        },
        "repository_commits": [], # Only contributor's commits to this repo
        "repository_commit_analysis": {
            "total_commits": 15,
            "patterns": {"most_active_month": "October"}
        },
        "contributor_info": {
            "username": "diego",
            "full_name": "Diego",
            "contributions": 0,  # No commits in this test
            "email": "diego@example.com"
        },
        "analyzed_at": "2024-09-01T00:00:00Z",
        "analysis_context_type": "repo_only",
        "repository_url": "https://github.com/rajakrishna/smart-gym",
        "ai_focus_instruction": "Focus ONLY on diego's contributions to rajakrishna/smart-gym repository. Do not mention or reference any other repositories, projects, or general profile information."
    }

    # Generate the prompt
    repo_only_prompt = prompt_service.build_prompt(
        github_data=smart_gym_data,
        recommendation_type="professional",
        tone="professional",
        length="medium",
        analysis_context_type="repo_only",
        repository_url="https://github.com/rajakrishna/smart-gym"
    )

    print("\n🧪 TESTING SMART-GYM REPO_ONLY PROMPT")
    print("=" * 60)
    print("REPO_ONLY PROMPT FOR SMART-GYM:")
    print("=" * 60)
    print(repo_only_prompt)
    print("=" * 60)

    # Debug: Check what's being detected (excluding legitimate terms like names)
    print("\n🔍 DEBUG: Checking for problematic terms...")
    problematic_terms = ["python", "data-science", "machine-learning", "api-design"]  # Excluding "go" since it's in "Diego"
    found_terms = [term for term in problematic_terms if term in repo_only_prompt.lower()]
    if found_terms:
        print(f"   Found problematic terms: {found_terms}")
        for term in found_terms:
            if term in repo_only_prompt.lower():
                print(f"   '{term}' found in prompt")
    else:
        print("   No problematic technology terms found (excluding names)")

    # Validate the generated prompt
    validation_results = {
        "contains_typescript": "TypeScript" in repo_only_prompt,
        "contains_javascript": "JavaScript" in repo_only_prompt,
        "contains_css": "CSS" in repo_only_prompt,
        "contains_react": "React" in repo_only_prompt,
        "contains_nextjs": "Next.js" in repo_only_prompt,
        "excludes_go": "Go" not in repo_only_prompt,
        "excludes_python": "Python" not in repo_only_prompt,
        "excludes_fiber": "Fiber" not in repo_only_prompt,
        "excludes_django": "Django" not in repo_only_prompt,
        # More specific check: only exclude technologies that are NOT in our repository data
        # Exclude "go" from this check since it appears in "Diego" (the contributor's name)
        "excludes_general_starred_tech": not any(tech in repo_only_prompt.lower() for tech in ["python", "data-science", "machine-learning", "api-design"]),
        # Allow "web-development" since it's related to the repository's "web technologies" description
        "contains_repo_name": "smart-gym" in repo_only_prompt,
        "contains_correct_owner": "diego" in repo_only_prompt, # Now refers to the contributor
        "excludes_company": "Tech Corp" not in repo_only_prompt,
        "excludes_location": "San Francisco" not in repo_only_prompt,
        "excludes_organizations": "OpenSourceOrg" not in repo_only_prompt,
    }

    print("\nVALIDATION RESULTS FOR SMART-GYM:")
    print("--------------------------------------------------")
    for check, passed in validation_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")

    overall_passed = all(validation_results.values())
    print("\n📊 SMART-GYM TEST SUMMARY: {}/{} tests passed ({:.1f}%) ".format(
        sum(1 for p in validation_results.values() if p),
        len(validation_results),
        (sum(1 for p in validation_results.values() if p) / len(validation_results)) * 100
    ))

    if overall_passed:
        print("🎉 SMART-GYM REPO_ONLY ISOLATION: SUCCESS!")
        return True
    else:
        print("❌ SMART-GYM REPO_ONLY ISOLATION: FAILED!")
        return False

if __name__ == "__main__":
    test_smart_gym_repo_only()
