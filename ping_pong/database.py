import os
from sqlmodel import SQLModel, create_engine
from ping_pong.models import Link

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    import sys
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

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Создает все таблицы в базе данных"""
    SQLModel.metadata.create_all(engine)
