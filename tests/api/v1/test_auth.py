from fastapi.testclient import TestClient


def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_register_and_login(client: TestClient):
    client.post(
        "/api/v1/users",
        json={"email": "authtest@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "authtest@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
