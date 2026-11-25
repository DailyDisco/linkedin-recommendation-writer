"""Recommendation model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.github_profile import GitHubProfile
    from app.models.user import User


class Recommendation(Base):
    """Recommendation model for storing generated LinkedIn recommendations."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    github_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("github_profiles.id"), nullable=False)

    # Recommendation content
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Generation parameters
    # professional, technical, leadership, etc.
    recommendation_type: Mapped[str] = mapped_column(String, default="professional", index=True)
    # professional, friendly, formal, casual
    tone: Mapped[str] = mapped_column(String, default="professional", index=True)
    length: Mapped[str] = mapped_column(String, default="medium", index=True)  # short, medium, long

    # AI generation metadata
    ai_model: Mapped[str] = mapped_column(String, nullable=False)  # gemini-2.5-flash-lite, etc.
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_parameters: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Quality metrics
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    # Selected option information (for when created from multiple options)
    selected_option_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    selected_option_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    selected_option_focus: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    generated_options: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # Store all generated options for reference

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    github_profile: Mapped["GitHubProfile"] = relationship("GitHubProfile", back_populates="recommendations")
    versions: Mapped[list["RecommendationVersion"]] = relationship("RecommendationVersion", back_populates="recommendation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, title={self.title[:50]}...)>"


class RecommendationVersion(Base):
    """Version history for recommendations to track changes over time."""

    __tablename__ = "recommendation_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recommendation_id: Mapped[int] = mapped_column(Integer, ForeignKey("recommendations.id"), nullable=False)

    # Version information
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1, 2, 3, etc.
    change_type: Mapped[str] = mapped_column(String, nullable=False, index=True)  # 'created', 'refined', 'keyword_refinement', 'manual_edit'
    change_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Description of what changed

    # Keyword refinement specific metadata
    include_keywords_used: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # List of keywords successfully included
    exclude_keywords_avoided: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # List of keywords successfully avoided

    # Content at this version
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Generation parameters at this version
    generation_parameters: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Quality metrics at this version
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # 'system', 'user', etc.

    # Relationships
    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="versions")

    def __repr__(self) -> str:
        return f"<RecommendationVersion(id={self.id}, recommendation_id={self.recommendation_id}, version={self.version_number})>"
