"""HTTP client for direct GitHub REST API calls using httpx."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubHTTPClient:
    """HTTP client wrapper for GitHub REST API v3."""

    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub HTTP client."""
        self.token = token or settings.GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "LinkedIn-Recommendation-Writer",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make GET request to GitHub API."""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params or {}, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API HTTP error {e.response.status_code}: {e}")
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            logger.error(f"GitHub API request error: {e}")
            return None
    
    async def get_paginated(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_pages: int = 10) -> List[Dict[str, Any]]:
        """Make paginated GET request to GitHub API."""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        params = params or {}
        params.setdefault("per_page", 100)
        
        results = []
        page = 1
        
        try:
            async with httpx.AsyncClient() as client:
                while page <= max_pages:
                    params["page"] = page
                    response = await client.get(url, headers=self.headers, params=params, timeout=30.0)
                    response.raise_for_status()
                    
                    data = response.json()
                    if not data:
                        break
                    
                    if isinstance(data, list):
                        results.extend(data)
                        if len(data) < params["per_page"]:
                            break
                    else:
                        results.append(data)
                        break
                    
                    page += 1
                    
                return results
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API HTTP error {e.response.status_code}: {e}")
            return results
        except Exception as e:
            logger.error(f"GitHub API pagination error: {e}")
            return results
    
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user data from GitHub API."""
        return await self.get(f"users/{username}")
    
    async def get_user_repos(self, username: str, sort: str = "updated", direction: str = "desc", max_pages: int = 3) -> List[Dict[str, Any]]:
        """Get user's repositories."""
        params = {
            "sort": sort,
            "direction": direction,
            "type": "owner",
        }
        return await self.get_paginated(f"users/{username}/repos", params=params, max_pages=max_pages)
    
    async def get_repo(self, repo_full_name: str) -> Optional[Dict[str, Any]]:
        """Get repository data."""
        return await self.get(f"repos/{repo_full_name}")
    
    async def get_repo_topics(self, repo_full_name: str) -> List[str]:
        """Get repository topics."""
        headers = {**self.headers, "Accept": "application/vnd.github.mercy-preview+json"}
        url = f"{self.BASE_URL}/repos/{repo_full_name}/topics"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                return data.get("names", [])
        except Exception as e:
            logger.debug(f"Error fetching topics for {repo_full_name}: {e}")
            return []
    
    async def get_repo_contributors(self, repo_full_name: str, max_pages: int = 2) -> List[Dict[str, Any]]:
        """Get repository contributors."""
        return await self.get_paginated(f"repos/{repo_full_name}/contributors", max_pages=max_pages)
    
    async def get_repo_commits(self, repo_full_name: str, author: Optional[str] = None, max_pages: int = 3) -> List[Dict[str, Any]]:
        """Get repository commits."""
        params = {}
        if author:
            params["author"] = author
        return await self.get_paginated(f"repos/{repo_full_name}/commits", params=params, max_pages=max_pages)
    
    async def get_user_orgs(self, username: str) -> List[Dict[str, Any]]:
        """Get user's organizations."""
        return await self.get_paginated(f"users/{username}/orgs", max_pages=2)
    
    async def get_user_starred(self, username: str, max_pages: int = 1) -> List[Dict[str, Any]]:
        """Get user's starred repositories."""
        return await self.get_paginated(f"users/{username}/starred", max_pages=max_pages)
    
    async def get_repo_pulls(self, repo_full_name: str, state: str = "all", max_pages: int = 2) -> List[Dict[str, Any]]:
        """Get repository pull requests."""
        params = {"state": state}
        return await self.get_paginated(f"repos/{repo_full_name}/pulls", params=params, max_pages=max_pages)
    
    async def get_repo_languages(self, repo_full_name: str) -> Dict[str, int]:
        """Get repository language statistics."""
        result = await self.get(f"repos/{repo_full_name}/languages")
        return result if result else {}
    
    async def get_repo_contents(self, repo_full_name: str, path: str) -> Optional[Dict[str, Any]]:
        """Get repository file contents."""
        return await self.get(f"repos/{repo_full_name}/contents/{path}")

