import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    if os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("FLY_APP_NAME"):
        raise RuntimeError(
            "DATABASE_URL is required in deployed environments. "
            "Use the public/internal PostgreSQL connection string from your hosting provider."
        )

    # Local default. Docker Compose overrides this with db:5432.
    DATABASE_URL = "postgresql://postgres:sys449420@localhost:5432/salesmitra"

# SQLite needs connect_args; other DBs do not
connect_args = {}
if DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["engine", "SessionLocal", "DATABASE_URL"]
