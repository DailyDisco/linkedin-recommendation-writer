"""Update recommendations schema and create recommendation_versions.

Revision ID: 20251231000003
Revises: 20251230100002
Create Date: 2025-12-31 00:00:03.000000

This migration:
- Adds missing columns to recommendations table
- Adds github_profile_id FK to link recommendations to profiles
- Migrates existing data from github_username to github_profile_id
- Creates recommendation_versions table for version history
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251231000003"
down_revision: Union[str, None] = "20251230100002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade recommendations table and create recommendation_versions."""

    # ==========================================
    # RECOMMENDATIONS - Add new columns
    # ==========================================

    # Add github_profile_id FK (nullable initially for data migration)
    op.add_column("recommendations", sa.Column("github_profile_id", sa.Integer(), nullable=True))

    # Add missing columns from model
    op.add_column("recommendations", sa.Column("title", sa.String(), nullable=True))
    op.add_column("recommendations", sa.Column("ai_model", sa.String(), nullable=True))
    op.add_column("recommendations", sa.Column("generation_prompt", sa.Text(), nullable=True))
    op.add_column("recommendations", sa.Column("generation_parameters", sa.JSON(), nullable=True))
    op.add_column("recommendations", sa.Column("word_count", sa.Integer(), server_default="0"))
    op.add_column("recommendations", sa.Column("selected_option_id", sa.Integer(), nullable=True))
    op.add_column("recommendations", sa.Column("selected_option_name", sa.String(), nullable=True))
    op.add_column("recommendations", sa.Column("selected_option_focus", sa.String(), nullable=True))
    op.add_column("recommendations", sa.Column("generated_options", sa.JSON(), nullable=True))

    # Create indexes on commonly queried columns
    op.create_index("ix_recommendations_recommendation_type", "recommendations", ["recommendation_type"])
    op.create_index("ix_recommendations_tone", "recommendations", ["tone"])
    op.create_index("ix_recommendations_length", "recommendations", ["length"])

    # ==========================================
    # DATA MIGRATION
    # ==========================================

    # First, ensure all github_usernames have corresponding github_profiles
    # Create github_profiles for any missing usernames
    op.execute(
        """
        INSERT INTO github_profiles (github_username, github_id, created_at, updated_at, last_analyzed)
        SELECT DISTINCT r.github_username,
               ABS(('x' || SUBSTR(MD5(r.github_username), 1, 7))::bit(28)::int),
               NOW(), NOW(), NOW()
        FROM recommendations r
        WHERE r.github_username IS NOT NULL
          AND r.github_username != ''
          AND NOT EXISTS (
              SELECT 1 FROM github_profiles gp
              WHERE gp.github_username = r.github_username
          )
    """
    )

    # Link recommendations to github_profiles via username
    op.execute(
        """
        UPDATE recommendations r
        SET github_profile_id = gp.id,
            title = COALESCE(r.recommendation_type, 'Professional') || ' Recommendation',
            ai_model = 'gemini-2.5-flash-lite',
            word_count = COALESCE(ARRAY_LENGTH(STRING_TO_ARRAY(TRIM(r.content), ' '), 1), 0)
        FROM github_profiles gp
        WHERE r.github_username = gp.github_username
          AND r.github_profile_id IS NULL
    """
    )

    # For any orphaned recommendations, create a placeholder profile
    op.execute(
        """
        INSERT INTO github_profiles (github_username, github_id, created_at, updated_at, last_analyzed)
        SELECT 'unknown_' || r.id::text,
               1000000 + r.id,
               NOW(), NOW(), NOW()
        FROM recommendations r
        WHERE r.github_profile_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM github_profiles gp
              WHERE gp.github_username = 'unknown_' || r.id::text
          )
    """
    )

    # Link orphaned recommendations to their placeholder profiles
    op.execute(
        """
        UPDATE recommendations r
        SET github_profile_id = gp.id,
            title = COALESCE(r.recommendation_type, 'Professional') || ' Recommendation',
            ai_model = 'gemini-2.5-flash-lite',
            word_count = COALESCE(ARRAY_LENGTH(STRING_TO_ARRAY(TRIM(r.content), ' '), 1), 0)
        FROM github_profiles gp
        WHERE r.github_profile_id IS NULL
          AND gp.github_username = 'unknown_' || r.id::text
    """
    )

    # ==========================================
    # RECOMMENDATIONS - Cleanup
    # ==========================================

    # Create FK constraint
    op.create_foreign_key("recommendations_github_profile_id_fkey", "recommendations", "github_profiles", ["github_profile_id"], ["id"])

    # Drop old columns and their indexes
    op.drop_index("ix_recommendations_github_username", table_name="recommendations", if_exists=True)
    op.drop_column("recommendations", "github_username")
    op.drop_column("recommendations", "metadata")

    # Make title and ai_model NOT NULL now that data is migrated
    op.alter_column("recommendations", "title", nullable=False, server_default="Recommendation")
    op.alter_column("recommendations", "ai_model", nullable=False, server_default="gemini-2.5-flash-lite")
    op.alter_column("recommendations", "github_profile_id", nullable=False)

    # ==========================================
    # RECOMMENDATION VERSIONS - Create table
    # ==========================================

    op.create_table(
        "recommendation_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False),
        # Version information
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("change_description", sa.Text(), nullable=True),
        # Keyword refinement metadata
        sa.Column("include_keywords_used", sa.JSON(), nullable=True),
        sa.Column("exclude_keywords_avoided", sa.JSON(), nullable=True),
        # Content at this version
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        # Generation parameters
        sa.Column("generation_parameters", sa.JSON(), nullable=True),
        # Quality metrics
        sa.Column("word_count", sa.Integer(), server_default="0"),
        # Metadata
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(), nullable=True),
    )

    # Create indexes for recommendation_versions
    op.create_index("ix_recommendation_versions_recommendation_id", "recommendation_versions", ["recommendation_id"])
    op.create_index("ix_recommendation_versions_version_number", "recommendation_versions", ["version_number"])
    op.create_index("ix_recommendation_versions_change_type", "recommendation_versions", ["change_type"])
    op.create_index("ix_recommendation_versions_created_at", "recommendation_versions", ["created_at"])


def downgrade() -> None:
    """Revert table changes."""

    # ==========================================
    # RECOMMENDATION VERSIONS - Drop table
    # ==========================================

    op.drop_table("recommendation_versions")

    # ==========================================
    # RECOMMENDATIONS - Revert
    # ==========================================

    # Add back old columns
    op.add_column("recommendations", sa.Column("github_username", sa.String(), nullable=True))
    op.add_column("recommendations", sa.Column("metadata", sa.JSON(), nullable=True))
    op.create_index("ix_recommendations_github_username", "recommendations", ["github_username"])

    # Migrate data back
    op.execute(
        """
        UPDATE recommendations r
        SET github_username = gp.github_username
        FROM github_profiles gp
        WHERE r.github_profile_id = gp.id
    """
    )

    # Drop new columns and constraints
    op.drop_constraint("recommendations_github_profile_id_fkey", "recommendations", type_="foreignkey")
    op.drop_index("ix_recommendations_recommendation_type", table_name="recommendations")
    op.drop_index("ix_recommendations_tone", table_name="recommendations")
    op.drop_index("ix_recommendations_length", table_name="recommendations")
    op.drop_column("recommendations", "generated_options")
    op.drop_column("recommendations", "selected_option_focus")
    op.drop_column("recommendations", "selected_option_name")
    op.drop_column("recommendations", "selected_option_id")
    op.drop_column("recommendations", "word_count")
    op.drop_column("recommendations", "generation_parameters")
    op.drop_column("recommendations", "generation_prompt")
    op.drop_column("recommendations", "ai_model")
    op.drop_column("recommendations", "title")
    op.drop_column("recommendations", "github_profile_id")
