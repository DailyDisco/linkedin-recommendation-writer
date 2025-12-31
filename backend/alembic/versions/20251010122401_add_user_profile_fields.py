"""add user profile fields

Revision ID: 20251010122401
Revises: 6bdfb470e813
Create Date: 2025-10-10 12:24:01.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251010122401"
down_revision: Union[str, None] = "6bdfb470e813"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing user profile columns."""
    # Add bio column (nullable text field)
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))

    # Add email_notifications_enabled column (boolean with default True)
    op.add_column("users", sa.Column("email_notifications_enabled", sa.Boolean(), nullable=False, server_default="true"))

    # Add default_tone column (varchar with default 'professional')
    op.add_column("users", sa.Column("default_tone", sa.String(), nullable=False, server_default="professional"))

    # Add language column (varchar with default 'en')
    op.add_column("users", sa.Column("language", sa.String(), nullable=False, server_default="en"))


def downgrade() -> None:
    """Remove user profile columns."""
    # Remove columns in reverse order
    op.drop_column("users", "language")
    op.drop_column("users", "default_tone")
    op.drop_column("users", "email_notifications_enabled")
    op.drop_column("users", "bio")
