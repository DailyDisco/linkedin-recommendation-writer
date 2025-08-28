"""Repository-related Pydantic schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class RepositoryContributorsRequest(BaseModel):
    """Request schema for getting repository contributors."""

    repository_name: str = Field(..., description="Repository name in format 'owner/repo'")
    max_contributors: int = Field(50, ge=1, le=100, description="Maximum contributors to fetch")
    force_refresh: bool = Field(False, description="Force refresh of cached data")


class ContributorInfo(BaseModel):
    """Individual contributor information schema."""

    username: str
    full_name: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    avatar_url: str
    contributions: int
    profile_url: str
    followers: int
    public_repos: int


class RepositoryInfo(BaseModel):
    """Repository information schema."""

    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int
    forks: int
    url: str
    topics: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RepositoryContributorsResponse(BaseModel):
    """Response schema for repository contributors."""

    repository: RepositoryInfo
    contributors: List[ContributorInfo]
    total_contributors: int
    fetched_at: str

    class Config:
        from_attributes = True
