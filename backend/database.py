import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use DATABASE_URL env var if provided, otherwise fallback to PostgreSQL
# In Docker: db:5432 (service name)
# Locally: localhost:5432
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:sys449420@db:5432/salesmitra')#not localhost because csv service runs in a separate container

# SQLite needs connect_args; other DBs do not
connect_args = {}
if DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["engine", "SessionLocal", "DATABASE_URL"]