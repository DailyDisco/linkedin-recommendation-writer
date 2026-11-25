"""GitHub Profile model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.recommendation import Recommendation
    from app.models.user import User


class GitHubProfile(Base):
    """GitHub profile model for storing analyzed GitHub data."""

    __tablename__ = "github_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # GitHub user information
    github_username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    github_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    blog: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # GitHub statistics
    public_repos: Mapped[int] = mapped_column(Integer, default=0)
    followers: Mapped[int] = mapped_column(Integer, default=0)
    following: Mapped[int] = mapped_column(Integer, default=0)
    public_gists: Mapped[int] = mapped_column(Integer, default=0)

    # Analyzed data (stored as JSON)
    repositories_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # Repository analysis
    languages_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # Programming languages
    contribution_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # Contribution patterns
    skills_analysis: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # Extracted skills

    # Metadata
    last_analyzed: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="github_profiles")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="github_profile")

    def __repr__(self) -> str:
        return f"<GitHubProfile(id={self.id}, username={self.github_username})>"
