"""Alembic environment configuration.

Reads the database URL from the application's environment-backed settings
so that no credentials are stored in alembic.ini or source code.
"""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

from app.core.config import get_settings
from app.core.database import Base

# Alembic Config object — provides access to alembic.ini values.
config = context.config

# Set up Python logging from the config file.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at the application's model metadata so that autogenerate
# can detect future domain model additions.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with the database URL from application settings
    so that SQL can be emitted to the script output without connecting.
    """
    url = get_settings().database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an engine from the application settings and associates it
    with the migration context.
    """
    connectable = create_engine(
        get_settings().database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

