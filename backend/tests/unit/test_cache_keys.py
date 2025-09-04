#!/usr/bin/env python3
"""
Test script to demonstrate cache key differences for different analysis contexts.
"""
from typing import Optional

def generate_github_profile_cache_key(username: str, analysis_context_type: str = "profile", repository_url: Optional[str] = None) -> str:
    """Generate GitHub profile cache key with context awareness."""
    context_suffix = ""
    if analysis_context_type != "profile":
        context_suffix = f":{analysis_context_type}"
        if repository_url:
            # Extract repo name from URL for cache key
            repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
            context_suffix += f":{repo_path}"

    return f"github_profile:{username}{context_suffix}"

def generate_repository_cache_key(repository_full_name: str, analysis_context_type: str = "profile", repository_url: Optional[str] = None) -> str:
    """Generate repository cache key with context awareness."""
    context_suffix = ""
    if analysis_context_type != "profile":
        context_suffix = f":{analysis_context_type}"
        if repository_url:
            # Use the provided repository URL for consistency
            repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
            context_suffix += f":{repo_path}"

    return f"repository:{repository_full_name}{context_suffix}"

def generate_ai_recommendation_cache_key(prompt_hash: str, analysis_context_type: str = "profile", repository_url: Optional[str] = None) -> str:
    """Generate AI recommendation cache key with context awareness."""
    context_suffix = ""
    if analysis_context_type != "profile":
        context_suffix = f":{analysis_context_type}"
        if repository_url:
            repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
            context_suffix += f":{repo_path}"

    return f"ai_recommendation_v3:{prompt_hash}{context_suffix}"

if __name__ == "__main__":
    print("🧪 Testing Cache Key Generation for Different Contexts\n")

    username = "testuser"
    repo_url = "https://github.com/testuser/smart-gym"
    repo_name = "testuser/smart-gym"
    prompt_hash = "abc123"

    print("📊 GitHub Profile Cache Keys:")
    print(f"  • Profile context:     {generate_github_profile_cache_key(username)}")
    print(f"  • Repo-only context:   {generate_github_profile_cache_key(username, 'repo_only', repo_url)}")
    print(f"  • Repo-contributor:    {generate_github_profile_cache_key(username, 'repository_contributor', repo_url)}")
    print()

    print("📁 Repository Cache Keys:")
    print(f"  • Profile context:     {generate_repository_cache_key(repo_name)}")
    print(f"  • Repo-only context:   {generate_repository_cache_key(repo_name, 'repo_only', repo_url)}")
    print(f"  • Repo-contributor:    {generate_repository_cache_key(repo_name, 'repository_contributor', repo_url)}")
    print()

    print("🤖 AI Recommendation Cache Keys:")
    print(f"  • Profile context:     {generate_ai_recommendation_cache_key(prompt_hash)}")
    print(f"  • Repo-only context:   {generate_ai_recommendation_cache_key(prompt_hash, 'repo_only', repo_url)}")
    print(f"  • Repo-contributor:    {generate_ai_recommendation_cache_key(prompt_hash, 'repository_contributor', repo_url)}")
    print()

    print("✅ Key Differences Demonstrated:")
    print("   • Each context type generates a unique cache key")
    print("   • Repository URL is included in non-profile contexts")
    print("   • This prevents cache pollution between different analysis types")
