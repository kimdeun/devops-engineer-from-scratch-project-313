import os
import sys
from sqlmodel import SQLModel, create_engine
from app.models import Link  # noqa: F401

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    is_testing = (
        "pytest" in sys.modules or
        "PYTEST_CURRENT_TEST" in os.environ
    )

    if is_testing:
        DATABASE_URL = "sqlite:///:memory:"
    else:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Set it to your PostgreSQL connection string, e.g.: "
            "postgres://user:password@host:5432/dbname?sslmode=disable"
        )

if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "+psycopg2" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

    if "?" not in DATABASE_URL:
        DATABASE_URL = f"{DATABASE_URL}?sslmode=require"
    elif "sslmode" not in DATABASE_URL:
        DATABASE_URL = f"{DATABASE_URL}&sslmode=require"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        echo=True,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 10,
        }
    )


def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Warning: Failed to create database tables: {e}")
        raise
