"""GitHub Profile model."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class GitHubProfile(Base):
    """GitHub profile model for storing analyzed GitHub data."""

    __tablename__ = "github_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # GitHub user information
    github_username = Column(String, unique=True, index=True, nullable=False)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    email = Column(String, nullable=True)
    blog = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    # GitHub statistics
    public_repos = Column(Integer, default=0)
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    public_gists = Column(Integer, default=0)

    # Analyzed data (stored as JSON)
    repositories_data = Column(JSON, nullable=True)  # Repository analysis
    languages_data = Column(JSON, nullable=True)  # Programming languages
    contribution_data = Column(JSON, nullable=True)  # Contribution patterns
    skills_analysis = Column(JSON, nullable=True)  # Extracted skills

    # Metadata
    last_analyzed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="github_profiles")
    recommendations = relationship(
        "Recommendation", back_populates="github_profile"
    )

    def __repr__(self):
        return (
            f"<GitHubProfile(id={self.id}, username={self.github_username})>"
        )
