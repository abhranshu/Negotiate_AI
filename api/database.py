# Listen for DB url from .env

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from api.config import settings

# Determine DB type
database_url = settings.DATABASE_URL.strip()

if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL (Supabase, Neon, etc.)
    connect_args = {}

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=2,
    pool_recycle=300,
    pool_pre_ping=True,  # verify each pooled connection is alive before use —
                         # Supabase's pooler closes idle connections, which
                         # otherwise cause "server closed the connection
                         # unexpectedly" errors on the next request.
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_engine_url() -> str:
    """Return the raw database URL string for tools like Alembic that need
    a plain DBAPI URL (not an Engine object)."""
    return settings.DATABASE_URL.strip()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
