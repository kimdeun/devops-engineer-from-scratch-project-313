from httpx import request


def test_get_ping_pong():
    response = request(method="get", url="http://localhost:8080/ping")
    assert response.status_code == 200
    assert response.text == '"pong"'
