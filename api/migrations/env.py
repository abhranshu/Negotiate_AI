import os, sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Resolve the real project root so env.py can find both alembic.ini and the api package.
_DIRNAME = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_DIRNAME, '..', '..'))
_ALEMBIC_INI = os.path.join(_PROJECT_ROOT, 'alembic.ini')
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Interpret the config file for Python logging.
_cfg_file = config.config_file_name
if _cfg_file is None or not os.path.exists(_cfg_file):
    _cfg_file = _ALEMBIC_INI
if _cfg_file is not None and os.path.exists(_cfg_file):
    fileConfig(_cfg_file)

# ── Import project models so Alembic can autogenerate migrations ────────────
from api.database import Base
from api.models import *   # noqa: F401,F403 — register all models before metadata is read

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
    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        url = os.environ.get('DATABASE_URL', 'sqlite:///default.db')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _get_database_url():
    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        url = os.environ.get('DATABASE_URL', 'sqlite:///default.db')
    return url.strip()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Reads the database URL from the Alembic config (which may be overridden
    via cfg.set_main_option), falling back to the project's settings.
    """
    database_url = _get_database_url()

    # Build a connectable from the URL. Use engine_from_config so Alembic
    # respects settings like poolclass.
    connectable = engine_from_config(
        {"sqlalchemy.url": database_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,   # required for SQLite ALTER TABLE support
        )
        with context.begin_transaction():
            context.run_migrations()




if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
