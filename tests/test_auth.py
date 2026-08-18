"""Authentication API tests."""


def test_register_and_login(client):
    registration = client.post(
        "/api/auth/register",
        json={
            "username": "test-user",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert registration.status_code == 201
    assert registration.json()["email"] == "test@example.com"

    login = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_invalid_login_is_rejected(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "test-user",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
