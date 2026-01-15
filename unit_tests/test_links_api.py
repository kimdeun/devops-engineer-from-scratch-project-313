import os
import re
import pytest

# Устанавливаем DATABASE_URL ДО импорта модулей, которые используют database.py
# Это нужно, чтобы модуль ping_pong.database не падал при импорте
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from typing import Optional
from fastapi.testclient import TestClient
from fastapi import Query, Response
from sqlmodel import SQLModel, create_engine, Session, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from fastapi import APIRouter, HTTPException, status
from ping_pong.models import Link, LinkCreate, LinkResponse
from ping_pong.routes import link_to_response


@pytest.fixture(scope="function")
def test_db():
    """Создает тестовую базу данных в памяти"""
    # Импортируем модели ПЕРЕД созданием engine, чтобы они зарегистрировались в metadata
    from ping_pong.models import Link  # noqa: F401

    # Используем StaticPool для SQLite в памяти, чтобы все соединения использовали одну БД
    test_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # Создаем таблицы - используем metadata из SQLModel
    SQLModel.metadata.create_all(test_engine)

    yield test_engine

    # Очищаем после теста
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(scope="function")
def test_app(test_db):
    """Создает тестовое приложение с тестовой БД"""
    from fastapi import FastAPI

    app = FastAPI()
    router = APIRouter()

    @router.get("/api/links", response_model=list[LinkResponse])
    def get_links(range_param: Optional[str] = Query(None, alias="range"), response: Response = None):
        """Возвращает список всех ссылок с поддержкой пагинации"""
        with Session(test_db) as session:
            # Получаем общее количество записей
            total_count = session.exec(select(func.count(Link.id))).one()

            # Если range не указан, возвращаем все записи
            if range_param is None:
                links = session.exec(select(Link)).all()
                result = [link_to_response(link) for link in links]
                if response:
                    response.headers["Content-Range"] = f"links 0-{len(result)-1}/{total_count}"
                return result

            # Парсим range параметр в формате [start, end]
            range_match = re.match(r'\[(\d+),\s*(\d+)\]', range_param)
            if not range_match:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid range format. Expected format: [start, end]"
                )

            start = int(range_match.group(1))
            end = int(range_match.group(2))

            # Валидация диапазона
            if start < 0 or end < start:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid range: start must be >= 0 and end must be >= start"
                )

            # Вычисляем limit (количество записей для возврата)
            # range [0, 10] означает записи с индексами 0-10 включительно, т.е. 11 записей
            limit = end - start + 1
            offset = start

            # Получаем записи с пагинацией
            links = session.exec(select(Link).offset(offset).limit(limit)).all()
            result = [link_to_response(link) for link in links]

            # Устанавливаем заголовок Content-Range
            # Формат: links start-end/total
            # Если записей нет, end = start - 1 (или 0 если start = 0)
            if len(result) > 0:
                actual_end = start + len(result) - 1
            else:
                # Для пустого результата: если start > 0, то end = start - 1, иначе 0
                actual_end = max(0, start - 1)

            if response:
                response.headers["Content-Range"] = f"links {start}-{actual_end}/{total_count}"

            return result

    @router.post("/api/links", status_code=status.HTTP_201_CREATED, response_model=LinkResponse)
    def create_link(link_data: LinkCreate):
        with Session(test_db) as session:
            existing_link = session.exec(
                select(Link).where(Link.short_name == link_data.short_name)
            ).first()
            if existing_link:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Short name already exists"
                )
            link = Link(
                original_url=link_data.original_url,
                short_name=link_data.short_name
            )
            session.add(link)
            try:
                session.commit()
                session.refresh(link)
                return link_to_response(link)
            except IntegrityError:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Short name already exists"
                )

    @router.get("/api/links/{link_id}", response_model=LinkResponse)
    def get_link(link_id: int):
        with Session(test_db) as session:
            link = session.get(Link, link_id)
            if not link:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Link not found"
                )
            return link_to_response(link)

    @router.put("/api/links/{link_id}", response_model=LinkResponse)
    def update_link(link_id: int, link_update: LinkCreate):
        with Session(test_db) as session:
            link = session.get(Link, link_id)
            if not link:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Link not found"
                )
            if link.short_name != link_update.short_name:
                existing_link = session.exec(
                    select(Link).where(Link.short_name == link_update.short_name)
                ).first()
                if existing_link:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Short name already exists"
                    )
            link.original_url = link_update.original_url
            link.short_name = link_update.short_name
            session.add(link)
            try:
                session.commit()
                session.refresh(link)
                return link_to_response(link)
            except IntegrityError:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Short name already exists"
                )

    @router.delete("/api/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_link(link_id: int):
        with Session(test_db) as session:
            link = session.get(Link, link_id)
            if not link:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Link not found"
                )
            session.delete(link)
            session.commit()
            return None

    app.include_router(router)
    return app


@pytest.fixture(scope="function")
def client(test_app):
    """Создает тестовый клиент"""
    return TestClient(test_app)


@pytest.fixture
def base_url_env(monkeypatch):
    """Устанавливает BASE_URL для тестов"""
    monkeypatch.setenv("BASE_URL", "https://test-short.io")


def test_get_links_empty(client):
    """Тест получения пустого списка ссылок"""
    response = client.get("/api/links")
    assert response.status_code == 200
    assert response.json() == []


def test_get_links_with_data(client, base_url_env):
    """Тест получения списка ссылок с данными"""
    # Создаем тестовые ссылки через API
    link1_data = {"original_url": "https://example.com/1", "short_name": "test1"}
    link2_data = {"original_url": "https://example.com/2", "short_name": "test2"}
    client.post("/api/links", json=link1_data)
    client.post("/api/links", json=link2_data)

    response = client.get("/api/links")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("id" in item for item in data)
    assert all("original_url" in item for item in data)
    assert all("short_name" in item for item in data)
    assert all("short_url" in item for item in data)
    assert all("created_at" in item for item in data)


def test_create_link_success(client, base_url_env):
    """Тест успешного создания ссылки"""
    link_data = {
        "original_url": "https://example.com/long-url",
        "short_name": "exmpl"
    }
    response = client.post("/api/links", json=link_data)
    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == "https://example.com/long-url"
    assert data["short_name"] == "exmpl"
    assert data["short_url"] == "https://test-short.io/r/exmpl"
    assert "id" in data
    assert "created_at" in data


def test_create_link_duplicate_short_name(client, base_url_env):
    """Тест создания ссылки с дублирующимся short_name"""
    link_data = {
        "original_url": "https://example.com/long-url",
        "short_name": "exmpl"
    }
    # Создаем первую ссылку
    response1 = client.post("/api/links", json=link_data)
    assert response1.status_code == 201

    # Пытаемся создать вторую с тем же short_name
    response2 = client.post("/api/links", json=link_data)
    assert response2.status_code == 400
    assert "Short name already exists" in response2.json()["detail"]


def test_create_link_default_base_url(client, monkeypatch):
    """Тест создания ссылки с дефолтным BASE_URL"""
    # Удаляем BASE_URL из окружения
    monkeypatch.delenv("BASE_URL", raising=False)

    link_data = {
        "original_url": "https://example.com/long-url",
        "short_name": "exmpl"
    }
    response = client.post("/api/links", json=link_data)
    assert response.status_code == 201
    data = response.json()
    assert data["short_url"] == "https://short.io/r/exmpl"


def test_get_link_by_id_success(client, base_url_env):
    """Тест успешного получения ссылки по ID"""
    # Создаем ссылку
    link_data = {
        "original_url": "https://example.com/long-url",
        "short_name": "exmpl"
    }
    create_response = client.post("/api/links", json=link_data)
    link_id = create_response.json()["id"]

    # Получаем ссылку по ID
    response = client.get(f"/api/links/{link_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == link_id
    assert data["original_url"] == "https://example.com/long-url"
    assert data["short_name"] == "exmpl"
    assert data["short_url"] == "https://test-short.io/r/exmpl"
    assert "created_at" in data


def test_get_link_by_id_not_found(client):
    """Тест получения несуществующей ссылки"""
    response = client.get("/api/links/999")
    assert response.status_code == 404
    assert "Link not found" in response.json()["detail"]


def test_update_link_success(client, base_url_env):
    """Тест успешного обновления ссылки"""
    # Создаем ссылку
    link_data = {
        "original_url": "https://example.com/long-url",
        "short_name": "exmpl"
    }
    create_response = client.post("/api/links", json=link_data)
    link_id = create_response.json()["id"]

    # Обновляем ссылку
    update_data = {
        "original_url": "https://example.com/new-url",
        "short_name": "newshort"
    }
    response = client.put(f"/api/links/{link_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == link_id
    assert data["original_url"] == "https://example.com/new-url"
    assert data["short_name"] == "newshort"
    assert data["short_url"] == "https://test-short.io/r/newshort"


def test_update_link_not_found(client):
    """Тест обновления несуществующей ссылки"""
    update_data = {
        "original_url": "https://example.com/new-url",
        "short_name": "newshort"
    }
    response = client.put("/api/links/999", json=update_data)
    assert response.status_code == 404
    assert "Link not found" in response.json()["detail"]


def test_update_link_duplicate_short_name(client, base_url_env):
    """Тест обновления ссылки с дублирующимся short_name"""
    # Создаем две ссылки
    link1_data = {
        "original_url": "https://example.com/1",
        "short_name": "link1"
    }
    link2_data = {
        "original_url": "https://example.com/2",
        "short_name": "link2"
    }
    create1_response = client.post("/api/links", json=link1_data)
    create2_response = client.post("/api/links", json=link2_data)

    # Пытаемся обновить link2 с short_name от link1
    update_data = {
        "original_url": "https://example.com/2",
        "short_name": "link1"
    }
    link2_id = create2_response.json()["id"]
    response = client.put(f"/api/links/{link2_id}", json=update_data)
    assert response.status_code == 400
    assert "Short name already exists" in response.json()["detail"]


def test_update_link_same_short_name(client, base_url_env):
    """Тест обновления ссылки с тем же short_name (должно работать)"""
    # Создаем ссылку
    link_data = {
        "original_url": "https://example.com/long-url",
        "short_name": "exmpl"
    }
    create_response = client.post("/api/links", json=link_data)
    link_id = create_response.json()["id"]

    # Обновляем только original_url, оставляя тот же short_name
    update_data = {
        "original_url": "https://example.com/new-url",
        "short_name": "exmpl"
    }
    response = client.put(f"/api/links/{link_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["short_name"] == "exmpl"
    assert data["original_url"] == "https://example.com/new-url"


def test_delete_link_success(client, base_url_env):
    """Тест успешного удаления ссылки"""
    # Создаем ссылку
    link_data = {
        "original_url": "https://example.com/long-url",
        "short_name": "exmpl"
    }
    create_response = client.post("/api/links", json=link_data)
    link_id = create_response.json()["id"]

    # Удаляем ссылку
    response = client.delete(f"/api/links/{link_id}")
    assert response.status_code == 204
    assert response.content == b""

    # Проверяем, что ссылка удалена
    get_response = client.get(f"/api/links/{link_id}")
    assert get_response.status_code == 404


def test_delete_link_not_found(client):
    """Тест удаления несуществующей ссылки"""
    response = client.delete("/api/links/999")
    assert response.status_code == 404
    assert "Link not found" in response.json()["detail"]


def test_created_at_auto_generated(client, base_url_env):
    """Тест автоматического создания поля created_at"""
    from datetime import datetime
    link_data = {
        "original_url": "https://example.com/long-url",
        "short_name": "exmpl"
    }
    response = client.post("/api/links", json=link_data)
    assert response.status_code == 201
    data = response.json()
    assert "created_at" in data
    # Проверяем, что created_at это валидная дата
    datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))


def test_short_url_format(client, base_url_env):
    """Тест формата short_url"""
    link_data = {
        "original_url": "https://example.com/long-url",
        "short_name": "test123"
    }
    response = client.post("/api/links", json=link_data)
    assert response.status_code == 201
    data = response.json()
    assert data["short_url"] == "https://test-short.io/r/test123"
    assert data["short_url"].startswith("https://test-short.io/r/")


def test_get_links_pagination_first_10(client, base_url_env):
    """Тест пагинации: получение первых 10 записей"""
    # Создаем 15 ссылок
    for i in range(15):
        link_data = {
            "original_url": f"https://example.com/{i}",
            "short_name": f"test{i}"
        }
        client.post("/api/links", json=link_data)

    # Получаем первые 10 записей (range [0, 10] = 11 записей: 0-10)
    response = client.get("/api/links?range=[0,10]")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 11  # [0, 10] включает обе границы
    assert data[0]["id"] == 1
    assert data[10]["id"] == 11

    # Проверяем заголовок Content-Range
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "links 0-10/15"


def test_get_links_pagination_skip_5(client, base_url_env):
    """Тест пагинации: пропуск первых 5 записей, получение следующих 5"""
    # Создаем 11 ссылок
    for i in range(11):
        link_data = {
            "original_url": f"https://example.com/{i}",
            "short_name": f"test{i}"
        }
        client.post("/api/links", json=link_data)

    # Получаем записи с 5 по 10 (range [5, 10] = 6 записей: 5-10)
    response = client.get("/api/links?range=[5,10]")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6  # [5, 10] включает обе границы
    assert data[0]["id"] == 6  # Первая запись имеет id=6 (индекс 5)
    assert data[5]["id"] == 11  # Последняя запись имеет id=11 (индекс 10)

    # Проверяем заголовок Content-Range
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "links 5-10/11"


def test_get_links_pagination_empty_result(client):
    """Тест пагинации: пустой результат при выходе за границы"""
    # Создаем 5 ссылок
    for i in range(5):
        link_data = {
            "original_url": f"https://example.com/{i}",
            "short_name": f"test{i}"
        }
        client.post("/api/links", json=link_data)

    # Запрашиваем записи за пределами существующих
    response = client.get("/api/links?range=[10,15]")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    # Проверяем заголовок Content-Range для пустого результата
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "links 10-9/5"  # start-1 если start > 0


def test_get_links_pagination_without_range(client, base_url_env):
    """Тест получения всех ссылок без параметра range"""
    # Создаем 5 ссылок
    for i in range(5):
        link_data = {
            "original_url": f"https://example.com/{i}",
            "short_name": f"test{i}"
        }
        client.post("/api/links", json=link_data)

    # Получаем все записи без range
    response = client.get("/api/links")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

    # Проверяем заголовок Content-Range
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "links 0-4/5"


def test_get_links_pagination_invalid_range_format(client):
    """Тест пагинации: неверный формат range"""
    response = client.get("/api/links?range=invalid")
    assert response.status_code == 400
    assert "Invalid range format" in response.json()["detail"]


def test_get_links_pagination_invalid_range_values(client):
    """Тест пагинации: неверные значения range (start > end)"""
    response = client.get("/api/links?range=[10,5]")
    assert response.status_code == 400
    assert "Invalid range" in response.json()["detail"]


def test_get_links_pagination_negative_start(client):
    """Тест пагинации: отрицательный start"""
    response = client.get("/api/links?range=[-1,10]")
    assert response.status_code == 400
    assert "Invalid range" in response.json()["detail"]
