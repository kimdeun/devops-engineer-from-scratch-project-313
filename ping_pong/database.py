import os
from sqlmodel import SQLModel, create_engine
from ping_pong.models import Link  # noqa: F401 - импорт необходим для регистрации модели

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./links.db")
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Создает все таблицы в базе данных"""
    SQLModel.metadata.create_all(engine)
