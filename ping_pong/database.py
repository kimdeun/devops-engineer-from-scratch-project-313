import os
from sqlmodel import SQLModel, create_engine
from ping_pong.models import Link

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Создает все таблицы в базе данных"""
    SQLModel.metadata.create_all(engine)
