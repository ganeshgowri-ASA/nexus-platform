<<<<<<< HEAD
<<<<<<< HEAD
"""
Alembic migration environment for NEXUS Platform.

This module configures Alembic for database migrations.
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database and models
from backend.core.config import get_settings
from backend.database import Base, import_models

# Import all models to ensure they're registered
import_models()

# Import all models explicitly
from backend.models.user import User  # noqa: F401
from backend.models.document import (  # noqa: F401
    AccessLevel,
    Document,
    DocumentAuditLog,
    DocumentComment,
    DocumentMetadata,
    DocumentPermission,
    DocumentStatus,
    DocumentTag,
    DocumentVersion,
    DocumentWorkflow,
    Folder,
    FolderPermission,
    ShareLink,
    ShareType,
    Tag,
    WorkflowStatus,
    WorkflowStep,
)

# This is the Alembic Config object
=======
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.database.base import Base
from modules.etl.models import *
from modules.integration_hub.models import *

# this is the Alembic Config object
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

<<<<<<< HEAD
# Set the SQLAlchemy URL from environment
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
=======
# Set sqlalchemy.url from environment variable
database_url = os.getenv("DATABASE_URL", "postgresql://nexus:nexus_password@localhost:5432/nexus_db")
config.set_main_option("sqlalchemy.url", database_url)
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
<<<<<<< HEAD
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
=======
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.scheduler.models.database import Base
from modules.scheduler.models.schemas import *
from modules.scheduler.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
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
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
<<<<<<< HEAD
    """
=======
    """Run migrations in 'offline' mode."""
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
    url = config.get_main_option("sqlalchemy.url")
=======

    """
    url = settings.DATABASE_URL_SYNC
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
<<<<<<< HEAD
<<<<<<< HEAD
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
=======
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
=======
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
<<<<<<< HEAD
<<<<<<< HEAD
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Override configuration with environment-specific settings
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
=======
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
=======
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL_SYNC

    connectable = engine_from_config(
        configuration,
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
<<<<<<< HEAD
<<<<<<< HEAD
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            # Include object names in autogenerate
            include_object=lambda object, name, type_, reflected, compare_to: True,
            # Render item for autogenerate
            render_item=None,
        )
=======
        context.configure(connection=connection, target_metadata=target_metadata)
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
=======
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U

        with context.begin_transaction():
            context.run_migrations()


<<<<<<< HEAD
<<<<<<< HEAD
# Run migrations based on context
=======
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
=======
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
