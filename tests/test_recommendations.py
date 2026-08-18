"""Deterministic recommendation tests."""

from src.database.models.product import Product
from src.database.models.user import User
from src.database.models.user_event import UserEvent
from src.services.auth_service import AuthService
from src.services.recommendation_service import RecommendationService


def create_user(db_session, username="learner"):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=AuthService(db_session).hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    return user


def create_products(db_session):
    products = [
        Product(name="Agent Course", description="Build AI agents", category="agentic-ai", price=10),
        Product(name="RAG Course", description="Build retrieval systems", category="agentic-ai", price=20),
        Product(name="Python Course", description="Learn Python APIs", category="python", price=30),
    ]
    db_session.add_all(products)
    db_session.commit()
    return products


def test_active_user_gets_unseen_products_from_interested_category(db_session, monkeypatch):
    monkeypatch.setenv("ENABLE_VECTOR_DB", "false")
    monkeypatch.setenv("ENABLE_LLM_RECOMMENDATIONS", "false")
    user = create_user(db_session)
    products = create_products(db_session)
    db_session.add_all([
        UserEvent(user_id=user.id, product_id=products[0].id, score=0.95),
        UserEvent(user_id=user.id, product_id=products[0].id, score=0.9),
    ])
    db_session.commit()

    recommendations = RecommendationService(db_session).get_or_generate_recommendation(user.id)
    assert recommendations is not None
    assert recommendations["product"]["id"] == products[1].id
    assert recommendations["score"] > 0.5


def test_cold_start_returns_popular_products(db_session, monkeypatch):
    monkeypatch.setenv("ENABLE_VECTOR_DB", "false")
    monkeypatch.setenv("ENABLE_LLM_RECOMMENDATIONS", "false")
    user = create_user(db_session)
    create_products(db_session)

    recommendations = RecommendationService(db_session).get_or_generate_recommendation(user.id)
    assert recommendations is not None
    assert recommendations["refresh_reason"] == "cold_start_user"
    assert len(recommendations["products"]) == 3
