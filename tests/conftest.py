import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.models import Link  # noqa: F401


if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    test_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    SQLModel.metadata.create_all(test_engine)

    yield test_engine

    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(scope="function")
def test_app(test_db, monkeypatch):
    from fastapi import FastAPI
    from app import database
    from app.routes import router

    monkeypatch.setattr(database, "engine", test_db)

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture(scope="function")
def client(test_app):
    return TestClient(test_app)


@pytest.fixture
def base_url_env(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://test-short.io")
