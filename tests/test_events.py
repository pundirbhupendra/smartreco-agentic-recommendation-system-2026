"""Behavioral event API tests."""

from src.database.models.user import User
from src.services.auth_service import AuthService


def create_user(db_session, username="learner"):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=AuthService(db_session).hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_batch_events_accept_bearer_token_and_summary_accepts_cookie(client, db_session):
    user = create_user(db_session)
    token = AuthService(db_session).create_access_token(user.id)

    response = client.post(
        "/api/events/batch",
        headers={"Authorization": f"Bearer {token}"},
        json={"events": [{"user_id": user.id, "product_id": 7, "score": 0.9}]},
    )
    assert response.status_code == 202
    assert response.json()["events_count"] == 1

    client.cookies.set("access_token", token)
    summary = client.get("/api/events/summary")
    assert summary.status_code == 200
    assert summary.json()["total_events"] == 1
    assert summary.json()["avg_score"] == 0.9


def test_user_cannot_submit_events_for_another_user(client, db_session):
    user = create_user(db_session)
    other = create_user(db_session, username="other")
    token = AuthService(db_session).create_access_token(user.id)

    response = client.post(
        "/api/events/batch",
        headers={"Authorization": f"Bearer {token}"},
        json={"events": [{"user_id": other.id, "product_id": 7, "score": 0.9}]},
    )
    assert response.status_code == 403
