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
