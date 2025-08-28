"""Recommendation model."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recommendation(Base):
    """Recommendation model for storing generated LinkedIn recommendations."""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    github_profile_id = Column(Integer, ForeignKey("github_profiles.id"), nullable=False)

    # Recommendation content
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    # Generation parameters
    # professional, technical, leadership, etc.
    recommendation_type = Column(String, default="professional")
    # professional, friendly, formal, casual
    tone = Column(String, default="professional")
    length = Column(String, default="medium")  # short, medium, long

    # AI generation metadata
    ai_model = Column(String, nullable=False)  # gemini-2.5-flash-lite, etc.
    generation_prompt = Column(Text, nullable=True)
    generation_parameters = Column(JSON, nullable=True)

    # Quality metrics
    confidence_score = Column(Integer, default=0)  # 0-100
    word_count = Column(Integer, default=0)

    # Selected option information (for when created from multiple options)
    selected_option_id = Column(Integer, nullable=True)
    selected_option_name = Column(String, nullable=True)
    selected_option_focus = Column(String, nullable=True)
    generated_options = Column(JSON, nullable=True)  # Store all generated options for reference

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recommendations")
    github_profile = relationship("GitHubProfile", back_populates="recommendations")
    versions = relationship("RecommendationVersion", back_populates="recommendation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, title={self.title[:50]}...)>"


class RecommendationVersion(Base):
    """Version history for recommendations to track changes over time."""

    __tablename__ = "recommendation_versions"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False)

    # Version information
    version_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    change_type = Column(String, nullable=False)  # 'created', 'refined', 'keyword_refinement', 'manual_edit'
    change_description = Column(Text, nullable=True)  # Description of what changed

    # Content at this version
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    # Generation parameters at this version
    generation_parameters = Column(JSON, nullable=True)

    # Quality metrics at this version
    confidence_score = Column(Integer, default=0)
    word_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)  # 'system', 'user', etc.

    # Relationships
    recommendation = relationship("Recommendation", back_populates="versions")

    def __repr__(self) -> str:
        return f"<RecommendationVersion(id={self.id}, recommendation_id={self.recommendation_id}, version={self.version_number})>"
