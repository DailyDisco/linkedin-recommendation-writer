from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Import application settings to use the actual DATABASE_URL
from app.core.config import settings


def get_sync_url(async_url: str) -> str:
    """Convert async database URL to sync URL for migrations.

    Alembic migrations need to run with a synchronous driver (psycopg2)
    because they execute in a thread pool context via run_in_executor.
    The asyncpg driver cannot work in this context due to greenlet requirements.
    """
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


# Interpret the config file for Python logging.
# This line sets up loggers basically.
# Disabled: The application already has logging configured, and this causes
# conflicts in containerized environments where alembic.ini may not have
# complete logging handler definitions.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

from app.core.database import Base
from app.models.github_profile import GitHubProfile
from app.models.recommendation import Recommendation

# add your model's MetaData object here
# for 'autogenerate' support
from app.models.user import User

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Override the sqlalchemy.url from alembic.ini with the actual DATABASE_URL
    # from environment variables, converting async URL to sync URL for migrations
    sync_url = get_sync_url(settings.DATABASE_URL)
    config.set_main_option("sqlalchemy.url", sync_url)

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Override the sqlalchemy.url from alembic.ini with the actual DATABASE_URL
    # from environment variables, converting async URL to sync URL for migrations
    sync_url = get_sync_url(settings.DATABASE_URL)
    config.set_main_option("sqlalchemy.url", sync_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
