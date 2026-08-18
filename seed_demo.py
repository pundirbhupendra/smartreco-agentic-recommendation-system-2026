"""Seed SmartReco with a course catalog and distinct demo user behavior.

The script is safe to rerun: existing products and users are reused, and a
persona receives behavioral events only on its first run.

Usage:
    python seed_demo.py
"""

from datetime import datetime, timedelta, timezone
import random

from src.database.db import SessionLocal, init_db
from src.database.models.product import Product
from src.database.models.user import User
from src.database.models.user_event import UserEvent
from src.services.auth_service import AuthService


DEMO_PASSWORD = "demo1234"

COURSES = [
    {
        "name": "LangGraph Agent Workflows",
        "description": "Build reliable multi-step AI agents with LangGraph state and tools.",
        "category": "agentic-ai",
        "price": 89.99,
    },
    {
        "name": "RAG Systems with Vector Search",
        "description": "Create retrieval augmented generation applications with embeddings and vector stores.",
        "category": "agentic-ai",
        "price": 79.99,
    },
    {
        "name": "Deep Learning with PyTorch",
        "description": "Train neural networks, transformers, and image models with PyTorch.",
        "category": "machine-learning",
        "price": 99.99,
    },
    {
        "name": "MLOps in Production",
        "description": "Deploy, monitor, and improve machine learning services in production.",
        "category": "machine-learning",
        "price": 84.99,
    },
    {
        "name": "Python for Data Analysis",
        "description": "Use Python, pandas, and notebooks for practical data analysis.",
        "category": "python",
        "price": 49.99,
    },
    {
        "name": "FastAPI Production APIs",
        "description": "Build secure, tested, and maintainable APIs with FastAPI.",
        "category": "python",
        "price": 59.99,
    },
    {
        "name": "React for Product Builders",
        "description": "Create responsive web applications with React components and hooks.",
        "category": "web-dev",
        "price": 64.99,
    },
    {
        "name": "Modern Web Application Design",
        "description": "Plan and build polished frontend experiences for web products.",
        "category": "web-dev",
        "price": 54.99,
    },
    {
        "name": "LLM Prompt Engineering",
        "description": "Design clear prompts and evaluation workflows for language model applications.",
        "category": "llm",
        "price": 44.99,
    },
    {
        "name": "System Design Interview Practice",
        "description": "Prepare for software engineering interviews with scalable system design exercises.",
        "category": "career",
        "price": 39.99,
    },
    {
        "name": "Kubernetes for Developers",
        "description": "Deploy and operate cloud-native applications with Kubernetes.",
        "category": "cloud-devops",
        "price": 69.99,
    },
    {
        "name": "Cloud Deployment Fundamentals",
        "description": "Learn containers, cloud hosting, CI/CD, and dependable application deployment.",
        "category": "cloud-devops",
        "price": 64.99,
    },
]

PERSONAS = [
    {
        "username": "maya",
        "email": "maya@demo.dev",
        "story": "Agent builder focused on LangGraph and RAG.",
        "categories": ["agentic-ai"],
    },
    {
        "username": "raj",
        "email": "raj@demo.dev",
        "story": "ML engineer exploring deep learning and MLOps.",
        "categories": ["machine-learning"],
    },
    {
        "username": "sofia",
        "email": "sofia@demo.dev",
        "story": "Full-stack developer learning Python and web development.",
        "categories": ["python", "web-dev"],
    },
    {
        "username": "kai",
        "email": "kai@demo.dev",
        "story": "Explorer interested in LLMs, career growth, and cloud operations.",
        "categories": ["llm", "career", "cloud-devops"],
    },
]


def seed_products(db) -> list[Product]:
    """Create the course catalog only when a named course is missing."""
    products = []
    for course in COURSES:
        product = db.query(Product).filter(Product.name == course["name"]).first()
        if product is None:
            product = Product(**course)
            db.add(product)
            db.flush()
        products.append(product)
    db.commit()
    return products


def seed_persona(db, persona: dict[str, object], products: list[Product]) -> bool:
    """Create a demo user and a realistic, category-focused event history."""
    user = db.query(User).filter(User.email == persona["email"]).first()
    if user is not None:
        print(f"  {persona['email']} already exists, skipping")
        return False

    auth_service = AuthService(db)
    user = User(
        username=persona["username"],
        email=persona["email"],
        hashed_password=auth_service.hash_password(DEMO_PASSWORD),
    )
    db.add(user)
    db.flush()

    products_by_category: dict[str, list[Product]] = {}
    for product in products:
        products_by_category.setdefault(product.category or "uncategorized", []).append(product)

    randomizer = random.Random(persona["email"])
    event_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3)
    events = []
    target_categories = persona["categories"]

    for category in target_categories:
        category_products = products_by_category.get(category, [])
        for product in randomizer.sample(category_products, min(2, len(category_products))):
            for _ in range(randomizer.randint(4, 6)):
                event_time += timedelta(minutes=randomizer.randint(3, 12))
                events.append(
                    UserEvent(
                        user_id=user.id,
                        product_id=product.id,
                        score=round(randomizer.uniform(0.75, 0.98), 2),
                        created_at=event_time,
                    )
                )

    other_products = [
        product
        for product in products
        if product.category not in target_categories
    ]
    if other_products:
        product = randomizer.choice(other_products)
        event_time += timedelta(minutes=randomizer.randint(5, 15))
        events.append(
            UserEvent(
                user_id=user.id,
                product_id=product.id,
                score=round(randomizer.uniform(0.15, 0.35), 2),
                created_at=event_time,
            )
        )

    db.add_all(events)
    db.commit()
    print(
        f"  {persona['email']} - {len(events)} events, "
        f"focus: {', '.join(target_categories)}"
    )
    return True


def main() -> None:
    init_db()
    with SessionLocal() as db:
        products = seed_products(db)
        print(f"Catalog ready: {len(products)} courses")

        created = sum(seed_persona(db, persona, products) for persona in PERSONAS)

    print(f"\nCreated {created} demo personas. Password: {DEMO_PASSWORD}")
    print("Personas:")
    for persona in PERSONAS:
        print(f"  {persona['email']:20s} - {persona['story']}")


if __name__ == "__main__":
    main()
