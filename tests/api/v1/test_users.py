from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, email: str, password: str) -> dict:
    r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_read_me_unauthenticated(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_create_and_read_me(client: TestClient):
    client.post(
        "/api/v1/users",
        json={"email": "metest@example.com", "password": "pass1234"},
    )
    headers = _auth_headers(client, "metest@example.com", "pass1234")
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "metest@example.com"


def test_duplicate_email(client: TestClient):
    client.post("/api/v1/users", json={"email": "dup@example.com", "password": "pass1234"})
    response = client.post(
        "/api/v1/users", json={"email": "dup@example.com", "password": "pass1234"}
    )
    assert response.status_code == 400
