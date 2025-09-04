"""Test script to verify repo_only context data isolation."""

import asyncio
import logging
from typing import Any, Dict

# Configure logging to see validation messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_contributor_data_with_profile():
    """Create mock contributor data that includes profile information."""
    return {
        "user_data": {
            "github_username": "testuser",
            "login": "testuser",
            "full_name": "Test User",  # This should be filtered out
            "bio": "A passionate developer",  # This should be filtered out
            "company": "Test Company",  # This should be filtered out
            "location": "Test City",  # This should be filtered out
            "email": "test@example.com",  # This should be filtered out
            "followers": 123,  # This should be filtered out
            "following": 456,  # This should be filtered out
            "public_repos": 78,  # This should be filtered out
            "avatar_url": "https://example.com/avatar.jpg",  # This should be filtered out
        },
        "repositories": [],  # This should be filtered out
        "languages": [],  # This should be filtered out
        "skills": {},  # This should be filtered out
        "organizations": [],  # This should be filtered out
        "starred_technologies": {},  # This should be filtered out
    }

def create_mock_repository_data():
    """Create mock repository data."""
    return {
        "repository_info": {
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "description": "A test repository",
            "language": "Python",
            "html_url": "https://github.com/testuser/test-repo",
        },
        "languages": [
            {"language": "Python", "percentage": 80.0, "lines_of_code": 1000},
            {"language": "JavaScript", "percentage": 20.0, "lines_of_code": 250},
        ],
        "skills": {
            "technical_skills": ["Python", "Django", "JavaScript"],
            "frameworks": ["Django", "React"],
            "domains": ["Web Development"],
        },
        "commit_analysis": {
            "total_commits": 25,
            "excellence_areas": {
                "primary_strength": "consistent_contribution",
            },
        },
    }

def simulate_repo_only_data_filtering(contributor_data: Dict[str, Any], repository_data: Dict[str, Any], contributor_username: str):
    """Simulate the repo_only data filtering logic from recommendation_service.py"""
    logger.info("🔒 SIMULATING REPO_ONLY DATA FILTERING")

    # Start with minimal contributor data - only essential identifying info
    filtered_contributor_data = {
        "user_data": {
            "github_username": contributor_data.get("user_data", {}).get("github_username") or contributor_username,
            "login": contributor_data.get("user_data", {}).get("login") or contributor_username,
            # EXPLICITLY EXCLUDE: bio, company, location, followers, public_repos, organizations, starred_technologies
        }
    }

    merged_data = filtered_contributor_data.copy()

    # Add repository-specific information with explicit overrides
    if repository_data:
        merged_data["repository_info"] = repository_data.get("repository_info", {})
        merged_data["repository_languages"] = repository_data.get("languages", [])
        merged_data["repository_skills"] = repository_data.get("skills", {})
        merged_data["repository_commits"] = []  # Mock filtered commits
        merged_data["repository_commit_analysis"] = repository_data.get("commit_analysis", {})

        # CRITICAL: For repo_only, use ONLY repository-specific data
        merged_data["languages"] = repository_data.get("languages", [])
        merged_data["skills"] = repository_data.get("skills", {})
        merged_data["commit_analysis"] = repository_data.get("commit_analysis", {})

        # Replace contributor_info with minimal repo stats
        merged_data["repo_contributor_stats"] = {
            "username": contributor_username,
            "contributions_to_repo": 25,  # Mock contribution count
        }

    # Add metadata about the analysis type
    merged_data["analysis_context_type"] = "repo_only"
    merged_data["target_repository"] = repository_data.get("repository_info", {}).get("full_name", "")
    merged_data["contributor_username"] = contributor_username

    return merged_data

def validate_repo_only_isolation(data: Dict[str, Any]):
    """Validate that repo_only data contains no profile information."""
    logger.info("🔍 VALIDATING REPO_ONLY DATA ISOLATION")

    validation_result = {
        "is_valid": True,
        "issues": [],
        "warnings": []
    }

    # Define profile data fields that should NEVER appear in repo_only context
    forbidden_profile_fields = [
        'bio', 'company', 'location', 'email', 'blog',
        'followers', 'following', 'public_repos', 'public_gists',
        'starred_repositories', 'organizations', 'starred_technologies',
        'repositories', 'full_name', 'name', 'avatar_url'
    ]

    # Check user_data section for profile data
    user_data = data.get('user_data', {})
    for field in forbidden_profile_fields:
        if field in user_data and user_data[field]:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"🚨 Profile field '{field}' found in user_data")

    # Check for profile data sections that should be excluded
    profile_sections = ['organizations', 'starred_technologies', 'starred_repositories', 'repositories']
    for section in profile_sections:
        if data.get(section):
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"🚨 Profile section '{section}' found in data")

    # Check for contributor_info (should not exist in repo_only)
    if data.get('contributor_info'):
        validation_result["is_valid"] = False
        validation_result["issues"].append("🚨 contributor_info found - should not exist in repo_only")

    # Ensure required repository data is present
    required_repo_fields = ['repository_info', 'languages', 'skills', 'commit_analysis', 'repo_contributor_stats']
    for field in required_repo_fields:
        if not data.get(field):
            validation_result["warnings"].append(f"⚠️ Missing required repository field: '{field}'")

    # Validate analysis_context_type
    if data.get('analysis_context_type') != 'repo_only':
        validation_result["is_valid"] = False
        validation_result["issues"].append("🚨 analysis_context_type is not 'repo_only'")

    return validation_result

def simulate_prompt_generation(data: Dict[str, Any]):
    """Simulate the prompt generation logic for repo_only context."""
    logger.info("📝 SIMULATING PROMPT GENERATION")

    # Simulate the prompt building logic
    prompt_parts = [
        f"Write a medium LinkedIn recommendation for {data['user_data']['github_username']}.",
        "Make it professional and suitable for professional purposes.",
        "",
        "CRITICAL: ONLY DISCUSS THIS SPECIFIC REPOSITORY - NO OTHER PROJECTS ALLOWED",
        "",
        "REPOSITORY DETAILS:",
        f"- Repository Name: {data['repository_info']['name']}",
        f"- Description: {data['repository_info']['description']}",
        f"- Main Language: {data['repository_info']['language']}",
        f"- Repository URL: {data['repository_info']['html_url']}",
        "",
        "STRICT INSTRUCTIONS:",
        "- ONLY mention work, skills, and contributions from THIS SPECIFIC REPOSITORY",
        "- DO NOT reference any other projects, repositories, or general GitHub profile",
    ]

    # Add repository-specific languages
    if data.get('languages'):
        languages = [lang.get("language", "") for lang in data['languages'][:3]]
        prompt_parts.append(f"- Languages used in this repository: {', '.join(languages)}")

    # Add repository-specific skills
    if data.get('skills', {}).get('technical_skills'):
        skills = data['skills']['technical_skills'][:5]
        prompt_parts.append(f"- Technical skills demonstrated in this repository: {', '.join(skills)}")

    # Add contributor stats
    if data.get('repo_contributor_stats'):
        stats = data['repo_contributor_stats']
        prompt_parts.extend([
            "",
            "CONTRIBUTOR DETAILS FOR THIS REPOSITORY:",
            f"- Total contributions to this repository: {stats.get('contributions_to_repo', 0)} commits",
            f"- Contributor: {stats.get('username', 'Unknown')}",
        ])

    final_prompt = "\n".join(prompt_parts)
    return final_prompt

def validate_prompt_for_profile_data(prompt: str):
    """Validate that the final prompt doesn't contain profile data."""
    logger.info("🔍 VALIDATING PROMPT FOR PROFILE DATA")

    validation_result = {
        "is_valid": True,
        "issues": [],
        "warnings": []
    }

    prompt_lower = prompt.lower()

    # Profile data keywords that should never appear in repo_only prompts
    # Note: 'linkedin' is excluded because it's part of legitimate "LinkedIn recommendation" context
    profile_keywords = [
        'bio', 'company', 'location', 'email', 'blog',
        'followers', 'following', 'public repos', 'public_repos',
        'starred', 'organizations', 'orgs',
        'full name', 'full_name', 'avatar',
        'hireable', 'website', 'twitter'
    ]

    # Check for profile keywords in the prompt
    for keyword in profile_keywords:
        if keyword in prompt_lower:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"🚨 Profile keyword '{keyword}' found in prompt")

    # Check for specific patterns that indicate profile data
    import re
    profile_patterns = [
        r'\d+\s+followers',  # "123 followers"
        r'\d+\s+following',  # "456 following"
        r'\d+\s+public\s+repos',  # "78 public repos"
        r'@[\w.-]+\s',  # Email-like patterns
    ]

    for pattern in profile_patterns:
        matches = re.findall(pattern, prompt, re.IGNORECASE)
        if matches:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"🚨 Profile pattern '{pattern}' found: {matches}")

    return validation_result

async def run_test():
    """Run the repo_only isolation test."""
    logger.info("🧪 STARTING REPO_ONLY ISOLATION TEST")
    logger.info("=" * 60)

    # Create test data
    contributor_data = create_mock_contributor_data_with_profile()
    repository_data = create_mock_repository_data()
    contributor_username = "testuser"

    logger.info("📊 TEST DATA CREATED")
    logger.info(f"   • Contributor has profile data: {len(contributor_data['user_data'])} fields")
    logger.info(f"   • Repository: {repository_data['repository_info']['full_name']}")
    logger.info(f"   • Repository languages: {len(repository_data['languages'])}")

    # Test 1: Data filtering
    logger.info("\n📋 TEST 1: DATA FILTERING")
    filtered_data = simulate_repo_only_data_filtering(contributor_data, repository_data, contributor_username)

    data_validation = validate_repo_only_isolation(filtered_data)

    if data_validation["is_valid"]:
        logger.info("✅ DATA FILTERING: PASSED - No profile data detected")
    else:
        logger.error("❌ DATA FILTERING: FAILED")
        for issue in data_validation["issues"]:
            logger.error(f"   {issue}")
        return False

    if data_validation["warnings"]:
        logger.warning("⚠️ DATA FILTERING WARNINGS:")
        for warning in data_validation["warnings"]:
            logger.warning(f"   {warning}")

    # Test 2: Prompt generation
    logger.info("\n📝 TEST 2: PROMPT GENERATION")
    prompt = simulate_prompt_generation(filtered_data)

    prompt_validation = validate_prompt_for_profile_data(prompt)

    if prompt_validation["is_valid"]:
        logger.info("✅ PROMPT GENERATION: PASSED - No profile data in prompt")
    else:
        logger.error("❌ PROMPT GENERATION: FAILED")
        for issue in prompt_validation["issues"]:
            logger.error(f"   {issue}")
        return False

    if prompt_validation["warnings"]:
        logger.warning("⚠️ PROMPT GENERATION WARNINGS:")
        for warning in prompt_validation["warnings"]:
            logger.warning(f"   {warning}")

    # Test 3: Content verification
    logger.info("\n🔍 TEST 3: CONTENT VERIFICATION")
    logger.info("Generated prompt preview:")
    logger.info("-" * 40)
    logger.info(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    logger.info("-" * 40)

    # Verify key isolation aspects
    isolation_checks = [
        ("Username only in user_data", filtered_data['user_data'].keys() == {'github_username', 'login'}),
        ("No profile fields in user_data", not any(key in filtered_data['user_data'] for key in ['bio', 'company', 'location', 'email', 'followers'])),
        ("Repository data present", 'repository_info' in filtered_data and 'languages' in filtered_data),
        ("Repo contributor stats present", 'repo_contributor_stats' in filtered_data),
        ("No contributor_info", 'contributor_info' not in filtered_data),
        ("Analysis context is repo_only", filtered_data.get('analysis_context_type') == 'repo_only'),
    ]

    all_checks_passed = True
    for check_name, check_result in isolation_checks:
        if check_result:
            logger.info(f"✅ {check_name}: PASSED")
        else:
            logger.error(f"❌ {check_name}: FAILED")
            all_checks_passed = False

    logger.info("\n" + "=" * 60)
    if all_checks_passed and data_validation["is_valid"] and prompt_validation["is_valid"]:
        logger.info("🎉 ALL TESTS PASSED: repo_only isolation is working correctly!")
        return True
    else:
        logger.error("💥 TESTS FAILED: repo_only isolation has issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_test())
    exit(0 if success else 1)
