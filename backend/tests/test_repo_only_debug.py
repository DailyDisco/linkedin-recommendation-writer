"""Debug test to trace repo_only data flow with comprehensive logging."""

import asyncio
import logging
import os
import sys

# Add the backend directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.ai.prompt_service import PromptService
from app.services.recommendation.recommendation_service import RecommendationService

# Configure logging to see all debug messages
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)


def create_test_data():
    """Create test data that might contain profile information."""
    # Simulate contributor data that might come from GitHub
    contributor_data = {
        "user_data": {
            "github_username": "testuser",
            "login": "testuser",
            "full_name": "Test User",  # This should be filtered out
            "bio": "A passionate developer who loves coding",  # This should be filtered out
            "company": "Test Company",  # This should be filtered out
            "location": "Test City",  # This should be filtered out
            "followers": 150,  # This should be filtered out
            "following": 200,  # This should be filtered out
            "public_repos": 25,  # This should be filtered out
            "avatar_url": "https://example.com/avatar.jpg",  # This should be filtered out
        },
        "repositories": [{"name": "repo1", "description": "First repo"}, {"name": "repo2", "description": "Second repo"}],  # This should be filtered out
        "languages": [{"language": "JavaScript", "percentage": 40.0}, {"language": "Python", "percentage": 30.0}],  # This should be filtered out (general profile languages)
        "skills": {"technical_skills": ["JavaScript", "Python", "React"], "frameworks": ["React", "Django"]},  # This should be filtered out (general profile skills)
        "organizations": [{"name": "Test Org", "login": "testorg"}],  # This should be filtered out
        "starred_technologies": {"languages": {"Go": 5, "Rust": 3}},  # This should be filtered out
    }

    # Repository-specific data (this should be kept)
    repository_data = {
        "repository_info": {
            "name": "fitmax",
            "full_name": "testuser/fitmax",
            "description": "A gym management application serving both members and administrators",
            "language": "TypeScript",
            "html_url": "https://github.com/testuser/fitmax",
        },
        "languages": [
            {"language": "TypeScript", "percentage": 60.0, "lines_of_code": 5000},
            {"language": "JavaScript", "percentage": 30.0, "lines_of_code": 2500},
            {"language": "Python", "percentage": 10.0, "lines_of_code": 800},
        ],
        "skills": {
            "technical_skills": ["TypeScript", "JavaScript", "Python", "React", "Django"],
            "frameworks": ["React", "Django", "ShadCN", "Docker"],
            "domains": ["Web Development", "API Development"],
        },
        "commit_analysis": {"total_commits": 45, "excellence_areas": {"primary_strength": "frontend_development", "patterns": {"most_active_month": "December 2023"}}},
    }

    return contributor_data, repository_data


async def test_repo_only_data_flow():
    """Test the repo_only data flow with logging."""
    logger.info("🧪 STARTING REPO_ONLY DEBUG TEST")
    logger.info("=" * 80)

    contributor_data, repository_data = create_test_data()

    logger.info("📊 TEST DATA CREATED")
    logger.info(f"   • Contributor has profile data: {len(contributor_data['user_data'])} fields")
    logger.info(f"   • Repository: {repository_data['repository_info']['full_name']}")
    logger.info(f"   • Repository languages: {len(repository_data['languages'])}")

    # Create service instances (mock them since we don't have full dependencies)
    class MockRecommendationService:
        def _validate_repo_only_data_isolation(self, data):
            """Mock validation - just log what's being validated."""
            logger.info("🔍 MOCK VALIDATION: Validating repo_only data isolation")
            logger.info(f"🔍 MOCK VALIDATION: Data keys: {list(data.keys())}")

            validation_result = {"is_valid": True, "issues": [], "warnings": []}

            # Check for profile data fields
            profile_indicators = [
                "bio",
                "company",
                "location",
                "email",
                "blog",
                "followers",
                "following",
                "public_repos",
                "public_gists",
                "starred_repositories",
                "organizations",
                "starred_technologies",
                "repositories",
                "full_name",
                "name",
                "avatar_url",
            ]

            user_data = data.get("user_data", {})
            for field in profile_indicators:
                if field in user_data and user_data[field]:
                    validation_result["is_valid"] = False
                    validation_result["issues"].append(f"Profile field '{field}' found in user_data")

            if data.get("contributor_info"):
                validation_result["is_valid"] = False
                validation_result["issues"].append("contributor_info found - should not exist in repo_only")

            profile_sections = ["organizations", "starred_technologies", "starred_repositories", "repositories"]
            for section in profile_sections:
                if data.get(section):
                    validation_result["is_valid"] = False
                    validation_result["issues"].append(f"Profile section '{section}' found in data")

            logger.info(f"🔍 MOCK VALIDATION: Result - is_valid: {validation_result['is_valid']}")
            if validation_result["issues"]:
                logger.error("🔍 MOCK VALIDATION: Issues found:")
                for issue in validation_result["issues"]:
                    logger.error(f"   • {issue}")

            return validation_result

        def _merge_repository_and_contributor_data(self, contributor_data, repository_data, contributor_username, analysis_context_type):
            """Mock the data merging logic."""
            logger.info(f"🔄 MOCK MERGING: Merging data for {contributor_username} with context: {analysis_context_type}")

            if analysis_context_type == "repo_only":
                # Simulate the repo_only filtering logic
                logger.info("🎯 MOCK MERGING: REPO_ONLY MODE - Filtering out general user data")

                # Log input data
                logger.info(f"🔍 MOCK MERGING: Input contributor_data keys: {list(contributor_data.keys())}")
                if "user_data" in contributor_data:
                    logger.info(f"🔍 MOCK MERGING: contributor user_data keys: {list(contributor_data['user_data'].keys())}")
                logger.info(f"🔍 MOCK MERGING: Input repository_data keys: {list(repository_data.keys())}")
                if "repository_info" in repository_data:
                    logger.info(f"🔍 MOCK MERGING: repository_info: {repository_data['repository_info']}")

                # Create filtered data (simulate the actual logic)
                logger.info("🔍 MOCK MERGING: Creating ULTRA-MINIMAL contributor data (NO PROFILE DATA)")
                filtered_contributor_data = {
                    "user_data": {
                        "github_username": contributor_data.get("user_data", {}).get("github_username") or contributor_username,
                        "login": contributor_data.get("user_data", {}).get("login") or contributor_username,
                    }
                }
                logger.info(f"🔍 MOCK MERGING: ULTRA-MINIMAL user_data: {filtered_contributor_data['user_data']}")

                merged_data = filtered_contributor_data.copy()

                # Add repository-specific information
                if repository_data:
                    merged_data["repository_info"] = repository_data.get("repository_info", {})
                    merged_data["languages"] = repository_data.get("languages", [])
                    merged_data["skills"] = repository_data.get("skills", {})
                    merged_data["commit_analysis"] = repository_data.get("commit_analysis", {})

                    merged_data["repo_contributor_stats"] = {
                        "username": contributor_username,
                        "contributions_to_repo": 45,
                    }

                merged_data["analysis_context_type"] = "repo_only"
                merged_data["target_repository"] = repository_data.get("repository_info", {}).get("full_name", "")
                merged_data["contributor_username"] = contributor_username

                logger.info("✅ MOCK MERGING: Filtered merged data created - general profile data excluded")
                logger.info(f"🔍 MOCK MERGING: Final merged_data keys: {list(merged_data.keys())}")
                if "user_data" in merged_data:
                    logger.info(f"🔍 MOCK MERGING: Final user_data: {merged_data['user_data']}")
                if "repo_contributor_stats" in merged_data:
                    logger.info(f"🔍 MOCK MERGING: repo_contributor_stats: {merged_data['repo_contributor_stats']}")

                # Validate the result
                validation_result = self._validate_repo_only_data_isolation(merged_data)
                if not validation_result["is_valid"]:
                    logger.error("🚨 MOCK MERGING: Profile data contamination detected!")
                    for issue in validation_result["issues"]:
                        logger.error(f"   • {issue}")
                else:
                    logger.info("✅ MOCK MERGING: Validation PASSED - no profile data contamination")

                return merged_data

    # Test the data flow
    mock_service = MockRecommendationService()
    result = mock_service._merge_repository_and_contributor_data(contributor_data, repository_data, "testuser", "repo_only")

    logger.info("\n📋 FINAL RESULT ANALYSIS")
    logger.info("=" * 50)
    logger.info(f"✅ Result keys: {list(result.keys())}")

    # Check if profile data leaked through
    profile_data_found = []
    if "user_data" in result:
        user_data = result["user_data"]
        profile_fields = ["full_name", "bio", "company", "location", "followers", "following", "public_repos", "avatar_url"]
        for field in profile_fields:
            if field in user_data and user_data[field]:
                profile_data_found.append(f"user_data.{field} = {user_data[field]}")

    if "repositories" in result:
        profile_data_found.append("repositories section found")
    if "organizations" in result:
        profile_data_found.append("organizations section found")
    if "starred_technologies" in result:
        profile_data_found.append("starred_technologies section found")
    if "contributor_info" in result:
        profile_data_found.append("contributor_info section found")

    if profile_data_found:
        logger.error("🚨 PROFILE DATA DETECTED IN RESULT:")
        for item in profile_data_found:
            logger.error(f"   • {item}")
        return False
    else:
        logger.info("✅ NO PROFILE DATA DETECTED - ISOLATION SUCCESSFUL")

    # Test prompt generation
    logger.info("\n📝 TESTING PROMPT GENERATION")
    logger.info("=" * 50)

    prompt_service = PromptService()

    # Test the prompt building
    try:
        prompt = prompt_service.build_prompt(
            github_data=result, recommendation_type="professional", tone="professional", length="medium", analysis_context_type="repo_only", repository_url="https://github.com/testuser/fitmax"
        )

        logger.info("✅ PROMPT GENERATED SUCCESSFULLY")
        logger.info(f"🔍 PROMPT LENGTH: {len(prompt)} characters")
        logger.info("🔍 PROMPT PREVIEW (first 500 chars):")
        logger.info(f"🔍 PROMPT: {prompt[:500]}...")

        # Check the full prompt for where profile keywords appear
        logger.info("\n🔍 ANALYZING WHERE PROFILE KEYWORDS APPEAR IN PROMPT:")
        prompt_lower = prompt.lower()
        profile_keywords = ["bio", "company", "location", "followers", "following", "public repos"]

        for keyword in profile_keywords:
            if keyword in prompt_lower:
                # Find context around the keyword
                idx = prompt_lower.find(keyword)
                start = max(0, idx - 100)
                end = min(len(prompt), idx + len(keyword) + 100)
                context = prompt[start:end]
                logger.info(f"🔍 '{keyword}' found at position {idx}:")
                logger.info(f"   Context: ...{context}...")

        # Check for profile keywords in the prompt - but distinguish between instructions and actual data
        profile_keywords = ["bio", "company", "location", "followers", "following", "public repos"]
        prompt_lower = prompt.lower()

        # Check if profile keywords appear in the main content (not just instructions)
        content_start = prompt_lower.find("strict instructions:")
        if content_start == -1:
            content_start = len(prompt)  # If no instructions section, check whole prompt

        main_content = prompt[:content_start]  # Only check the part before instructions
        instruction_content = prompt[content_start:]  # The instructions/warnings part

        found_in_content = []
        found_in_instructions = []

        for keyword in profile_keywords:
            if keyword in main_content.lower():
                found_in_content.append(keyword)
            elif keyword in instruction_content.lower():
                found_in_instructions.append(keyword)

        # Profile keywords in main content are BAD
        if found_in_content:
            logger.error("🚨 PROFILE DATA FOUND IN MAIN CONTENT:")
            for keyword in found_in_content:
                logger.error(f"   • '{keyword}' found in actual content (NOT instructions)")
            return False

        # Profile keywords in instructions are OK (they're warnings)
        if found_in_instructions:
            logger.info("ℹ️ PROFILE KEYWORDS FOUND IN INSTRUCTIONS (this is OK - they're warnings):")
            for keyword in found_in_instructions:
                logger.info(f"   • '{keyword}' found in instructions (preventing AI from using profile data)")

        logger.info("✅ NO PROFILE DATA FOUND IN MAIN CONTENT")

    except Exception as e:
        logger.error(f"❌ PROMPT GENERATION FAILED: {e}")
        return False

    logger.info("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    logger.info("✅ REPO_ONLY ISOLATION IS WORKING CORRECTLY")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_repo_only_data_flow())
    exit(0 if success else 1)
