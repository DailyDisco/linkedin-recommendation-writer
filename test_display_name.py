#!/usr/bin/env python3
"""Test script to verify display_name functionality in recommendation generation."""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai.prompt_service import PromptService


async def test_display_name_extraction():
    """Test the display name extraction functionality."""
    print("🧪 Testing Display Name Extraction")
    print("=" * 50)

    prompt_service = PromptService()

    # Test cases with different user data scenarios
    test_cases = [
        {
            "name": "Full name with first name",
            "user_data": {
                "full_name": "John Smith",
                "github_username": "johnsmith123"
            },
            "expected": "John"
        },
        {
            "name": "Full name with middle name",
            "user_data": {
                "full_name": "Jane Mary Doe",
                "github_username": "janedoe"
            },
            "expected": "Jane"
        },
        {
            "name": "Only username (no full name)",
            "user_data": {
                "github_username": "alexdev"
            },
            "expected": "alexdev"  # Should fallback to username
        },
        {
            "name": "Empty user data",
            "user_data": {},
            "expected": "the developer"
        },
        {
            "name": "Name with special characters",
            "user_data": {
                "full_name": "José María González",
                "github_username": "josegonzalez"
            },
            "expected": "José"
        }
    ]

    print("Testing _extract_display_name method:")
    print("-" * 30)

    for test_case in test_cases:
        result = prompt_service._extract_display_name(test_case["user_data"])
        status = "✅ PASS" if result == test_case["expected"] else "❌ FAIL"
        print(f"{status} {test_case['name']}")
        print(f"   Input: {test_case['user_data']}")
        print(f"   Expected: {test_case['expected']}")
        print(f"   Got: {result}")
        print()

    print("Testing _extract_first_name method:")
    print("-" * 30)

    first_name_tests = [
        ("John Smith", "John"),
        ("Jane Mary Doe", "Jane"),
        ("José María González", "José"),
        ("", ""),
        ("SingleName", "SingleName"),
    ]

    for full_name, expected in first_name_tests:
        result = prompt_service._extract_first_name(full_name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} '{full_name}' -> '{result}' (expected: '{expected}')")

    print("\n🎉 Display Name Extraction Test Complete!")


async def test_prompt_generation():
    """Test that prompts use display_name correctly."""
    print("\n🧪 Testing Prompt Generation with Display Name")
    print("=" * 50)

    prompt_service = PromptService()

    # Sample GitHub data
    github_data = {
        "user_data": {
            "full_name": "Sarah Johnson",
            "github_username": "sarahjdev",
            "bio": "Full-stack developer passionate about React and Node.js"
        },
        "languages": [
            {"language": "JavaScript", "percentage": 60},
            {"language": "Python", "percentage": 30},
            {"language": "TypeScript", "percentage": 10}
        ],
        "skills": {
            "technical_skills": ["React", "Node.js", "Python", "Django"],
            "frameworks": ["React", "Express", "Django"],
        }
    }

    print("Generating prompt with display_name='Sarah':")
    print("-" * 40)

    try:
        prompt = prompt_service.build_prompt(
            github_data=github_data,
            recommendation_type="professional",
            tone="professional",
            length="medium",
            display_name="Sarah"
        )

        # Check if "Sarah" appears in the prompt
        sarah_count = prompt.count("Sarah")
        print(f"✅ 'Sarah' appears {sarah_count} times in the prompt")

        # Check for any instances of the full name or username
        full_name_count = prompt.count("Sarah Johnson")
        username_count = prompt.count("sarahjdev")

        print(f"   • Full name 'Sarah Johnson': {full_name_count} occurrences")
        print(f"   • Username 'sarahjdev': {username_count} occurrences")

        if full_name_count == 0 and username_count == 0:
            print("✅ SUCCESS: Only first name is used, no full name or username found!")
        else:
            print("⚠️  WARNING: Full name or username still present in prompt")

        print(f"\n📝 Prompt preview (first 500 chars):\n{prompt[:500]}...")

    except Exception as e:
        print(f"❌ ERROR generating prompt: {e}")

    print("\n🎉 Prompt Generation Test Complete!")


if __name__ == "__main__":
    print("🚀 Starting Display Name Implementation Tests")
    print("=" * 60)

    asyncio.run(test_display_name_extraction())
    asyncio.run(test_prompt_generation())

    print("\n🎊 All Tests Completed!")
    print("=" * 60)
