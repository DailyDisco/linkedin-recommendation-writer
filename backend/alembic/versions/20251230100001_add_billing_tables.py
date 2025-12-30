"""add billing tables for monetization

Revision ID: 20251230100001
Revises: 20251010122401
Create Date: 2025-12-30 10:00:01.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20251230100001'
down_revision: Union[str, None] = '20251010122401'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create billing tables and add subscription fields to users."""

    # 1. Add Stripe-related fields to users table
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('subscription_tier', sa.String(50),
                                      nullable=False, server_default='free'))
    op.add_column('users', sa.Column('subscription_status', sa.String(50),
                                      nullable=False, server_default='active'))

    # Create indexes for user subscription fields
    op.create_index('idx_users_stripe_customer_id', 'users', ['stripe_customer_id'], unique=True)
    op.create_index('idx_users_subscription_tier', 'users', ['subscription_tier'])

    # 2. Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),

        # Stripe IDs
        sa.Column('stripe_customer_id', sa.String(255), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('stripe_price_id', sa.String(255), nullable=True),

        # Status
        sa.Column('tier', sa.String(50), nullable=False, server_default='free'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),

        # Billing period
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),

        # Trial
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),

        # Cancellation
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default='false'),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for subscriptions
    op.create_index('idx_subscriptions_user_id', 'subscriptions', ['user_id'], unique=True)
    op.create_index('idx_subscriptions_stripe_customer_id', 'subscriptions',
                    ['stripe_customer_id'], unique=True)
    op.create_index('idx_subscriptions_stripe_subscription_id', 'subscriptions',
                    ['stripe_subscription_id'], unique=True)
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])

    # 3. Create usage_records table for historical usage tracking
    op.create_table(
        'usage_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),

        # Usage data
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('generation_count', sa.Integer(), server_default='0'),

        # Metadata
        sa.Column('tier', sa.String(50), nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create composite unique index for user + date
    op.create_index('idx_usage_records_user_date', 'usage_records',
                    ['user_id', 'date'], unique=True)

    # 4. Create api_keys table for Team tier API access
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),

        # Key data
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(10), nullable=False),

        # Permissions
        sa.Column('scopes', sa.ARRAY(sa.Text()), server_default='{}'),

        # Usage tracking
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), server_default='0'),

        # Status
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )

    # Create indexes for api_keys
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('idx_api_keys_key_prefix', 'api_keys', ['key_prefix'])

    # 5. Create stripe_webhook_events table for idempotency and debugging
    op.create_table(
        'stripe_webhook_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('stripe_event_id', sa.String(255), nullable=False, unique=True),
        sa.Column('event_type', sa.String(255), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )

    # Create indexes for webhook events
    op.create_index('idx_webhook_events_stripe_id', 'stripe_webhook_events',
                    ['stripe_event_id'], unique=True)
    op.create_index('idx_webhook_events_type', 'stripe_webhook_events', ['event_type'])


def downgrade() -> None:
    """Remove billing tables and subscription fields from users."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('stripe_webhook_events')
    op.drop_table('api_keys')
    op.drop_table('usage_records')
    op.drop_table('subscriptions')

    # Remove user subscription fields
    op.drop_index('idx_users_subscription_tier', table_name='users')
    op.drop_index('idx_users_stripe_customer_id', table_name='users')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'subscription_tier')
    op.drop_column('users', 'stripe_customer_id')
