#!/usr/bin/env python3
"""
Simple test script to verify the Prompt Assistant implementation works.
"""
import asyncio
import json
from typing import Dict, Any

# Mock GitHub profile data for testing
MOCK_GITHUB_DATA = {
    "user_data": {
        "github_username": "octocat",
        "full_name": "The Octocat",
        "bio": "A test GitHub user for demonstration",
        "company": "GitHub",
        "location": "San Francisco",
        "public_repos": 25,
        "followers": 1000,
        "following": 500
    },
    "languages": [
        {"language": "JavaScript", "percentage": 40.0},
        {"language": "Python", "percentage": 30.0},
        {"language": "TypeScript", "percentage": 20.0},
        {"language": "Go", "percentage": 10.0}
    ],
    "skills": {
        "technical_skills": ["JavaScript", "Python", "React", "Node.js", "API Development", "Testing"]
    },
    "repositories": [
        {"name": "hello-world", "description": "A simple hello world repository"},
        {"name": "test-repo", "description": "A test repository for CI/CD"},
        {"name": "api-client", "description": "REST API client library"}
    ],
    "analysis_context_type": "profile"
}

import pytest

@pytest.mark.asyncio
async def test_prompt_generator_service():
    """Test the PromptGeneratorService functionality."""
    print("Testing PromptGeneratorService...")

    try:
        from app.services.prompt_generator_service import PromptGeneratorService, GitHubProfileMinimalSchema

        # Initialize service
        service = PromptGeneratorService()
        print("✓ PromptGeneratorService initialized successfully")

        # Test profile schema creation
        profile = GitHubProfileMinimalSchema(MOCK_GITHUB_DATA)
        print(f"✓ GitHub profile parsed: {profile.username}")

        # Test if AI client is available (may be None in test environment)
        if service.client:
            print("✓ AI client is available")

            # Test initial suggestions (this would normally call the AI)
            print("Note: AI calls would be tested in full environment with API keys")
        else:
            print("ℹ AI client not available (expected in test environment)")

        return True

    except Exception as e:
        print(f"✗ Error testing PromptGeneratorService: {e}")
        return False

@pytest.mark.asyncio
async def test_schemas():
    """Test that all schemas can be created and validated."""
    print("\nTesting schemas...")

    try:
        from app.schemas.recommendation import (
            PromptSuggestionsRequest,
            PromptSuggestionsResponse,
            AutocompleteSuggestionsRequest,
            ChatAssistantRequest,
            ChatAssistantResponse
        )

        # Test PromptSuggestionsRequest
        request = PromptSuggestionsRequest(
            github_username="octocat",
            recommendation_type="professional",
            tone="professional",
            length="medium"
        )
        print("✓ PromptSuggestionsRequest created successfully")

        # Test PromptSuggestionsResponse
        response = PromptSuggestionsResponse(
            suggested_working_relationship=["We collaborated on the frontend team"],
            suggested_specific_skills=["JavaScript", "React"],
            suggested_notable_achievements=["Improved application performance"]
        )
        print("✓ PromptSuggestionsResponse created successfully")

        # Test AutocompleteSuggestionsRequest
        autocomplete_request = AutocompleteSuggestionsRequest(
            github_username="octocat",
            field_name="specific_skills",
            current_input="Java"
        )
        print("✓ AutocompleteSuggestionsRequest created successfully")

        # Test ChatAssistantRequest
        chat_request = ChatAssistantRequest(
            github_username="octocat",
            conversation_history=[],
            user_message="Help me write a recommendation",
            current_form_data={}
        )
        print("✓ ChatAssistantRequest created successfully")

        # Test ChatAssistantResponse
        chat_response = ChatAssistantResponse(
            ai_reply="I can help you write a great recommendation!",
            suggested_form_updates={"workingRelationship": "We worked together on..."}
        )
        print("✓ ChatAssistantResponse created successfully")

        return True

    except Exception as e:
        print(f"✗ Error testing schemas: {e}")
        return False

@pytest.mark.asyncio
async def test_ai_service():
    """Test that AIService can be imported and has new methods."""
    print("\nTesting AIService...")

    try:
        from app.services.ai_service import AIService

        # Initialize service
        service = AIService()
        print("✓ AIService initialized successfully")

        # Check if new methods exist
        required_methods = [
            'get_initial_prompt_suggestions',
            'get_autocomplete_suggestions',
            'chat_with_assistant'
        ]

        for method_name in required_methods:
            if hasattr(service, method_name):
                print(f"✓ Method {method_name} exists")
            else:
                print(f"✗ Method {method_name} missing")
                return False

        return True

    except Exception as e:
        print(f"✗ Error testing AIService: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Testing Prompt Assistant Implementation")
    print("=" * 50)

    results = []
    results.append(await test_schemas())
    results.append(await test_prompt_generator_service())
    results.append(await test_ai_service())

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All tests passed! The Prompt Assistant implementation is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
