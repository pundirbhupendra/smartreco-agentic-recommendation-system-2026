"""Product API tests."""

from src.services.auth_service import AuthService
from src.database.models.user import User


def admin_token(db_session):
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=AuthService(db_session).hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    return AuthService(db_session).create_access_token(user.id)


def test_product_crud_and_search(client, db_session):
    token = admin_token(db_session)
    payload = {
        "name": "Testing FastAPI",
        "description": "Learn API testing with pytest and FastAPI.",
        "category": "python",
        "price": 49.99,
    }

    created = client.post("/api/products", params={"auth_token": token}, json=payload)
    assert created.status_code == 201
    product_id = created.json()["id"]

    listed = client.get("/api/products")
    assert listed.status_code == 200
    assert any(item["id"] == product_id for item in listed.json())

    searched = client.get("/api/products/search", params={"q": "pytest"})
    assert searched.status_code == 200
    assert searched.json()[0]["id"] == product_id

    updated = client.put(
        f"/api/products/{product_id}",
        params={"auth_token": token},
        json={"price": 59.99},
    )
    assert updated.status_code == 200
    assert updated.json()["price"] == 59.99

    deleted = client.delete(
        f"/api/products/{product_id}",
        params={"auth_token": token},
    )
    assert deleted.status_code == 204
