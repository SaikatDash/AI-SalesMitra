'''import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import urllib.parse

# Use DATABASE_URL env var if provided, otherwise fallback to MySQL.
#DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:sys449420@localhost:/salesmitra')
#DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:sys449420@localhost:3306/salesmitra')
DATABASE_URL = os.getenv('DATABASE_URL', 'mssql+pyodbc://root:sys449420@(localdb)\\MSSQLLocalDB/salesmitra?driver=ODBC+Driver+17+for+SQL+Server')

# Use DATABASE_URL env var if provided; otherwise default to LocalDB using
# a trusted Windows connection (no UID/PWD) which works for (localdb)\\MSSQLLocalDB.
# If you prefer SQL authentication or a different server, set the DATABASE_URL
# environment variable to a valid SQLAlchemy URL.

# Build an ODBC connection string for LocalDB using Windows authentication
default_odbc = (
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=(localdb)\MSSQLLocalDB;"
    r"DATABASE=salesmitra;"
    r"Trusted_Connection=yes;"
)

DATABASE_URL = os.getenv('DATABASE_URL', f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(default_odbc)}")

# SQLite needs connect_args; other DBs do not
connect_args = {}
if DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}
elif DATABASE_URL.startswith('mssql+pyodbc'):
    connect_args = {"timeout": 5}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["engine", "SessionLocal", "DATABASE_URL"]
'''
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use DATABASE_URL env var if provided, otherwise fallback to PostgreSQL
# Default to the `salesmitra` database so API sales endpoints return loaded data.
# If you need to run auth against `EmployeeDatabase`, set the env var `DATABASE_URL`
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:sys449420@localhost:5432/salesmitra')


# SQLite needs connect_args; other DBs do not
connect_args = {}
if DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["engine", "SessionLocal", "DATABASE_URL"]






