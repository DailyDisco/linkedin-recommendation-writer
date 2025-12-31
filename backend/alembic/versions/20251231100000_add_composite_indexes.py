"""Add composite indexes for query optimization.

Revision ID: 20251231100000
Revises: 20251231000003
Create Date: 2025-12-31 10:00:00.000000

This migration adds composite indexes to optimize common query patterns:
- recommendations: user_id + created_at for user-specific queries
- github_profiles: last_analyzed for cache invalidation queries
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251231100000"
down_revision: Union[str, None] = "20251231000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for query optimization."""
    # Composite index for user-specific recommendation queries ordered by date
    # Supports: SELECT * FROM recommendations WHERE user_id = ? ORDER BY created_at DESC
    op.create_index(
        "ix_recommendations_user_created",
        "recommendations",
        ["user_id", "created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )

    # Index for cache invalidation queries on github_profiles
    # Supports: SELECT * FROM github_profiles WHERE last_analyzed < ?
    op.create_index(
        "ix_github_profiles_last_analyzed",
        "github_profiles",
        ["last_analyzed"],
        postgresql_using="btree",
        postgresql_ops={"last_analyzed": "DESC"},
    )

    # Composite index for recommendation versions ordered by version number
    # Supports: SELECT * FROM recommendation_versions WHERE recommendation_id = ? ORDER BY version_number DESC
    op.create_index(
        "ix_recommendation_versions_rec_version_desc",
        "recommendation_versions",
        ["recommendation_id", "version_number"],
        postgresql_using="btree",
        postgresql_ops={"version_number": "DESC"},
    )


def downgrade() -> None:
    """Remove composite indexes."""
    op.drop_index("ix_recommendation_versions_rec_version_desc", table_name="recommendation_versions")
    op.drop_index("ix_github_profiles_last_analyzed", table_name="github_profiles")
    op.drop_index("ix_recommendations_user_created", table_name="recommendations")
