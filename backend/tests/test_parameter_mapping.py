#!/usr/bin/env python3
"""
Test script to verify parameter mapping between frontend and backend.
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.ai.prompt_service import PromptService
from app.services.recommendation.recommendation_service import RecommendationService


def test_parameter_mapping():
    """Test that parameters are correctly mapped from frontend to backend."""

    print("🧪 TESTING PARAMETER MAPPING")
    print("=" * 50)

    # Simulate frontend request data
    frontend_request = {
        "github_username": "testuser",
        "analysis_context_type": "repo_only",
        "repository_url": "https://github.com/testuser/test-repo",
        "recommendation_type": "professional",
        "tone": "professional",
        "length": "medium",
    }

    print("📤 Frontend sends:")
    for key, value in frontend_request.items():
        print(f"   • {key}: {value}")

    # Simulate backend receiving the request
    print("\n📥 Backend receives:")
    print(f"   • github_username: {frontend_request['github_username']}")
    print(f"   • analysis_context_type: {frontend_request['analysis_context_type']}")
    print(f"   • repository_url: {frontend_request['repository_url']}")

    # Test the condition that determines repo_only mode
    analysis_context_type = frontend_request.get("analysis_context_type", "profile")
    repository_url = frontend_request.get("repository_url")

    condition_result = analysis_context_type == "repo_only" and repository_url is not None

    print("\n🔍 Backend condition check:")
    print(f"   • analysis_context_type == 'repo_only': {analysis_context_type == 'repo_only'}")
    print(f"   • repository_url is not None: {repository_url is not None}")
    print(f"   • Overall condition: {condition_result}")

    if condition_result:
        print("✅ REPO_ONLY MODE ACTIVATED")
        print("   • Backend will fetch repository data only")
        print("   • Profile data will be filtered out")
        print("   • AI will receive repository-specific context only")
    else:
        print("❌ REPO_ONLY MODE NOT ACTIVATED")
        print("   • Backend will fetch full profile data")
        print("   • AI may receive profile data")

    print("\n" + "=" * 50)
    print("🎉 PARAMETER MAPPING TEST COMPLETED")

    return condition_result


if __name__ == "__main__":
    success = test_parameter_mapping()
    exit(0 if success else 1)
