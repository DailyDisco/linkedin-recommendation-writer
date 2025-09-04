#!/usr/bin/env python3
"""
Test script to directly test repository analysis.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.github.github_repository_service import GitHubRepositoryService
from app.services.github.github_commit_service import GitHubCommitService

async def test_repository_analysis():
    """Test repository analysis directly."""
    print("🧪 TESTING REPOSITORY ANALYSIS")
    print("=" * 50)

    try:
        # Initialize services
        commit_service = GitHubCommitService()
        repo_service = GitHubRepositoryService(commit_service)

        print("🔧 Services initialized successfully")

        # Test repository analysis
        print("📦 Testing repository analysis for rajakrishna/smart-gym...")

        result = await repo_service.analyze_repository("rajakrishna/smart-gym", force_refresh=True)

        if result:
            print("✅ Repository analysis succeeded!")
            print(f"   • Repository: {result.get('repository_info', {}).get('name', 'N/A')}")
            print(f"   • Language: {result.get('repository_info', {}).get('language', 'N/A')}")
            print(f"   • Languages: {len(result.get('languages', []))}")
            print(f"   • Commits: {len(result.get('commits', []))}")
            print(f"   • Skills: {len(result.get('skills', {}).get('technical_skills', []))}")
        else:
            print("❌ Repository analysis failed - returned None")

    except Exception as e:
        print(f"💥 Exception during repository analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_repository_analysis())
