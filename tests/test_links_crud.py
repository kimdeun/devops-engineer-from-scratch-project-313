import pytest
from fastapi.testclient import TestClient


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
