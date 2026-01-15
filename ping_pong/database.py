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

# Нормализуем DATABASE_URL для Render PostgreSQL
# Render может предоставлять URL без порта или параметров
if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    # Если URL не содержит параметры подключения, добавляем sslmode=require для Render
    # Render PostgreSQL требует SSL
    if "?" not in DATABASE_URL:
        DATABASE_URL = f"{DATABASE_URL}?sslmode=require"
    elif "sslmode" not in DATABASE_URL:
        DATABASE_URL = f"{DATABASE_URL}&sslmode=require"

# Создаем engine с увеличенными таймаутами для подключения к БД
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  # Проверяем соединение перед использованием
    pool_recycle=300,    # Переиспользуем соединения каждые 5 минут
    connect_args={
        "connect_timeout": 10,  # Таймаут подключения 10 секунд
    }
)


def create_db_and_tables():
    """Создает все таблицы в базе данных"""
    try:
        SQLModel.metadata.create_all(engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Warning: Failed to create database tables: {e}")
        # Не прерываем запуск приложения, если таблицы уже существуют
        # или есть другие проблемы с БД
        import traceback
        traceback.print_exc()
