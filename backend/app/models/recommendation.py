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

    def __repr__(self):
        return f"<Recommendation(id={self.id}, title={self.title[:50]}...)>"
