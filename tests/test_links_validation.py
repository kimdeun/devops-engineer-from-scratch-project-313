import pytest
from fastapi.testclient import TestClient


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
    client.post("/api/links", json=link1_data)
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
