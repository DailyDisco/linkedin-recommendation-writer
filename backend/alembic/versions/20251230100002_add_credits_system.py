"""add credits system for pay-as-you-go billing

Revision ID: 20251230100002
Revises: 20251230100001
Create Date: 2025-12-30 10:00:02.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251230100002"
down_revision: Union[str, None] = "20251230100001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add credits fields to users table."""

    # Add credits fields to users table
    op.add_column("users", sa.Column("credits", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("users", sa.Column("lifetime_credits_purchased", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("last_credit_pack", sa.String(50), nullable=True))

    # Create credit_purchases table for transaction history
    op.create_table(
        "credit_purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        # Purchase details
        sa.Column("pack_type", sa.String(50), nullable=False),  # starter, pro
        sa.Column("credits_amount", sa.Integer(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        # Stripe
        sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True),
        sa.Column("stripe_checkout_session_id", sa.String(255), nullable=True),
        # Status
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index("idx_credit_purchases_user_id", "credit_purchases", ["user_id"])
    op.create_index("idx_credit_purchases_stripe_session", "credit_purchases", ["stripe_checkout_session_id"], unique=True)
    op.create_index("idx_credit_purchases_status", "credit_purchases", ["status"])


def downgrade() -> None:
    """Remove credits fields and credit_purchases table."""

    # Drop credit_purchases table
    op.drop_table("credit_purchases")

    # Remove credits fields from users table
    op.drop_column("users", "last_credit_pack")
    op.drop_column("users", "lifetime_credits_purchased")
    op.drop_column("users", "credits")
