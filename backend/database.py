import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker

# Keep local credentials in backend/.env (or the repository-level .env) while
# allowing deployment-provided environment variables to take precedence.
_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env", override=False)
load_dotenv(_BACKEND_DIR.parent / ".env", override=False)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    if os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("FLY_APP_NAME"):
        raise RuntimeError(
            "DATABASE_URL is required in deployed environments. "
            "Use the public/internal PostgreSQL connection string from your hosting provider."
        )

    # Local default. Docker Compose overrides this with db:5432.
    DATABASE_URL = "postgresql://salesmitra_user:SQZe1WzlRsRIPzdof8leFENUuRJGB2Lu@dpg-dbfg3b8ae00c73fvb2e0-a.oregon-postgres.render.com/salesmitra"

# SQLite needs connect_args; other DBs do not
connect_args = {}
if DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database_info() -> dict:
    url = make_url(DATABASE_URL)
    return {
        "driver": url.drivername,
        "host": url.host,
        "port": url.port,
        "database": url.database,
        "username": url.username,
    }

__all__ = ["engine", "SessionLocal", "DATABASE_URL", "get_database_info"]
