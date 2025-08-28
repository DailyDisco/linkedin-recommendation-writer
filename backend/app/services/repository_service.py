"""Repository service for fetching repository contributors and details."""

import logging
from typing import Any, Dict, Optional

from github import Github
from github.GithubException import GithubException

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache

logger = logging.getLogger(__name__)


class RepositoryService:
    """Service for repository-related operations."""

    def __init__(self):
        """Initialize repository service."""
        self.github_client = None
        if settings.GITHUB_TOKEN:
            self.github_client = Github(settings.GITHUB_TOKEN)

    async def get_repository_contributors(
        self,
        repo_name: str,
        max_contributors: int = 50,
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Get contributors from a repository with their real names."""

        cache_key = f"repo_contributors:{repo_name}:{max_contributors}"

        # Check cache first
        if not force_refresh:
            cached_data = await get_cache(cache_key)
            if cached_data:
                logger.info(f"Returning cached contributors for repository: " f"{repo_name}")
                return cached_data

        try:
            if not self.github_client:
                raise ValueError("GitHub token not configured")

            # Get repository
            repo = self.github_client.get_repo(repo_name)

            # Get repository details
            repo_info = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "url": repo.html_url,
                "topics": list(repo.get_topics()),
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            }

            # Get contributors
            contributors_list = []
            contributors = repo.get_contributors()

            count = 0
            for contributor in contributors:
                if count >= max_contributors:
                    break

                try:
                    # Get detailed user info to get real name
                    user = self.github_client.get_user(contributor.login)

                    contributor_info = {
                        "username": contributor.login,
                        "full_name": user.name if user.name else contributor.login,
                        "first_name": (self._extract_first_name(user.name) if user.name else ""),
                        "last_name": (self._extract_last_name(user.name) if user.name else ""),
                        "email": user.email,
                        "bio": user.bio,
                        "company": user.company,
                        "location": user.location,
                        "avatar_url": user.avatar_url,
                        "contributions": contributor.contributions,
                        "profile_url": user.html_url,
                        "followers": user.followers,
                        "public_repos": user.public_repos,
                    }

                    contributors_list.append(contributor_info)
                    count += 1

                except Exception as e:
                    logger.warning(f"Could not get details for contributor " f"{contributor.login}: {e}")
                    # Add basic info even if detailed lookup fails
                    contributors_list.append(
                        {
                            "username": contributor.login,
                            "full_name": contributor.login,
                            "first_name": "",
                            "last_name": "",
                            "email": None,
                            "bio": None,
                            "company": None,
                            "location": None,
                            "avatar_url": contributor.avatar_url,
                            "contributions": contributor.contributions,
                            "profile_url": (f"https://github.com/{contributor.login}"),
                            "followers": 0,
                            "public_repos": 0,
                        }
                    )
                    count += 1

            result = {
                "repository": repo_info,
                "contributors": contributors_list,
                "total_contributors": len(contributors_list),
                "fetched_at": "now",
            }

            # Cache for 1 hour
            await set_cache(cache_key, result, ttl=3600)

            return result

        except GithubException as e:
            if e.status == 404:
                logger.error(f"Repository not found: {repo_name}")
                return None
            else:
                logger.error(f"GitHub API error for repository {repo_name}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error fetching contributors for repository {repo_name}: {e}")
            return None

    def _extract_first_name(self, full_name: str) -> str:
        """Extract first name from full name."""
        if not full_name:
            return ""
        parts = full_name.strip().split()
        return parts[0] if parts else ""

    def _extract_last_name(self, full_name: str) -> str:
        """Extract last name from full name."""
        if not full_name:
            return ""
        parts = full_name.strip().split()
        return parts[-1] if len(parts) > 1 else ""
