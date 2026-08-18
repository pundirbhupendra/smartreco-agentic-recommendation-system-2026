"""Seed SmartReco with a 50-course catalog.

The script is safe to rerun. It creates missing courses and updates existing
courses with the same name. It does not delete products or seed a vector store.

Usage:
    python seed.py

After this catalog exists, seed demo behavior with:
    python seed_demo.py
"""

from collections import Counter

from src.database.db import SessionLocal, init_db
from src.database.models.product import Product


COURSES = [
    # agentic-ai
    ("Agentic AI Systems with LangGraph", "Build stateful multi-agent workflows with nodes, edges, routing, and human review.", "agentic-ai", 129.00),
    ("Designing Autonomous AI Agents", "Learn planning agents, tools, memory, reflection, and evaluation loops.", "agentic-ai", 149.00),
    ("RAG Engineering in Production", "Build grounded retrieval systems with chunking, embeddings, reranking, and hybrid search.", "agentic-ai", 119.00),
    ("Multi-Agent Collaboration Patterns", "Coordinate specialized agents using supervisor, swarm, and debate architectures.", "agentic-ai", 139.00),
    ("Building MCP Servers", "Expose tools and data to LLM applications with the Model Context Protocol.", "agentic-ai", 99.00),
    ("Tool Calling and Function Agents", "Use structured outputs, schema validation, and reliable tool orchestration.", "agentic-ai", 89.00),
    ("Agent Evaluation and Observability", "Trace, score, and debug AI agent runs with practical evaluation harnesses.", "agentic-ai", 109.00),
    # machine-learning
    ("Machine Learning Foundations", "Learn supervised learning, regularization, bias-variance, and model selection.", "machine-learning", 79.00),
    ("Deep Learning with PyTorch", "Build neural networks, CNNs, and practical training loops using PyTorch.", "machine-learning", 119.00),
    ("Transformers from Scratch", "Understand attention, positional encoding, and build a mini transformer model.", "machine-learning", 139.00),
    ("Feature Engineering Masterclass", "Create reliable features, prevent leakage, and build reusable model pipelines.", "machine-learning", 69.00),
    ("MLOps: Ship Models to Production", "Learn experiment tracking, model registries, CI/CD, and drift monitoring.", "machine-learning", 129.00),
    ("Recommendation Systems", "Build collaborative filtering, embeddings, and two-tower recommendation models.", "machine-learning", 99.00),
    ("Computer Vision Basics", "Learn convolutions, augmentation, and transfer learning for image models.", "machine-learning", 99.00),
    ("NLP with Transformers", "Use tokenization, embeddings, and transformer fine-tuning for text tasks.", "machine-learning", 119.00),
    ("Reinforcement Learning Introduction", "Understand MDPs, Q-learning, and policy gradients with practical intuition.", "machine-learning", 129.00),
    ("Time Series Forecasting", "Explore stationarity, ARIMA, and modern forecasting techniques.", "machine-learning", 89.00),
    ("Graph Machine Learning", "Learn message passing, graph neural networks, and knowledge graph embeddings.", "machine-learning", 139.00),
    # llm
    ("Prompt Engineering Deep Dive", "Design systematic prompts, few-shot examples, and structured output contracts.", "llm", 59.00),
    ("Fine-Tuning LLMs with LoRA", "Use parameter-efficient fine-tuning, datasets, adapters, and evaluation.", "llm", 149.00),
    ("LLM Application Architecture", "Build streaming, caching, guardrails, and cost control into LLM products.", "llm", 109.00),
    ("Vector Databases in Depth", "Learn HNSW, similarity metrics, metadata filters, and hybrid search tradeoffs.", "llm", 89.00),
    ("Streaming LLM Interfaces", "Build token streaming, optimistic UI, and responsive AI application panels.", "llm", 69.00),
    ("Cost Optimization for AI Apps", "Reduce AI spend with caching, batching, routing, and model tiering.", "llm", 79.00),
    # python
    ("Python for Data Professionals", "Write idiomatic Python with typing, dataclasses, and clean project structure.", "python", 49.00),
    ("Async Python Mastery", "Use asyncio, concurrency patterns, and high-throughput I/O services.", "python", 79.00),
    ("FastAPI: Production APIs", "Build secure, tested, and maintainable APIs with FastAPI.", "python", 89.00),
    ("Testing and Quality in Python", "Use pytest, fixtures, property-based testing, and meaningful coverage.", "python", 59.00),
    # web-dev
    ("Modern Web Frontends", "Learn semantic HTML, responsive layout, and component thinking.", "web-dev", 49.00),
    ("React from Zero to Hooks", "Build React components with state, effects, and data fetching patterns.", "web-dev", 89.00),
    ("Full-Stack with FastAPI and React", "Connect a typed backend to a responsive React frontend.", "web-dev", 129.00),
    ("Designing REST and Realtime APIs", "Learn resource design, pagination, websockets, and versioning.", "web-dev", 79.00),
    # data-engineering
    ("Data Engineering Fundamentals", "Compare batch and streaming systems, warehouses, and analytics models.", "data-engineering", 89.00),
    ("Apache Kafka in Practice", "Learn topics, partitions, consumer groups, and reliable stream processing.", "data-engineering", 119.00),
    ("Building ETL Pipelines", "Create observable, idempotent data pipelines and orchestration workflows.", "data-engineering", 99.00),
    ("SQL for Analytics", "Use CTEs, window functions, and query tuning for analytics work.", "data-engineering", 59.00),
    # cloud-devops
    ("Cloud Native on Azure", "Use App Service, Functions, managed identity, and secure configuration.", "cloud-devops", 109.00),
    ("Docker and Containers", "Build images, use layers, and create slim production containers.", "cloud-devops", 69.00),
    ("Kubernetes Essentials", "Learn pods, services, deployments, and workload scaling.", "cloud-devops", 129.00),
    ("CI/CD with GitHub Actions", "Create pipelines, manage secrets, and deploy applications safely.", "cloud-devops", 59.00),
    ("Observability and Tracing", "Use metrics, logs, distributed tracing, and service-level objectives.", "cloud-devops", 99.00),
    # security
    ("Web Application Security", "Understand OWASP Top 10, authentication flaws, and secure design.", "security", 99.00),
    ("Secrets and Identity Management", "Learn OAuth2, JWT, and safe credential management.", "security", 89.00),
    # product-design
    ("UX for Engineers", "Apply usability heuristics, information hierarchy, and practical UI design.", "product-design", 49.00),
    ("Data Visualization Craft", "Choose effective charts, color, and visual encodings for decisions.", "product-design", 59.00),
    # career
    ("System Design Interviews", "Practice scalable architectures, tradeoffs, and structured interview answers.", "career", 99.00),
    ("Tech Lead Playbook", "Learn technical direction, reviews, communication, and mentoring.", "career", 79.00),
    ("Negotiation for Engineers", "Develop offer negotiation, scope management, and influence skills.", "career", 49.00),
    # recommendation-specific course to complete the catalog
    ("Building AI-Powered Recommendations", "Combine behavioral signals, embeddings, retrieval, and personalized narratives.", "agentic-ai", 119.00),
    ("Evaluating Generative AI Systems", "Measure faithfulness, relevance, and quality with trustworthy evaluation sets.", "agentic-ai", 109.00),
]


def main() -> None:
    init_db()
    created = 0
    updated = 0

    with SessionLocal() as db:
        for name, description, category, price in COURSES:
            product = db.query(Product).filter(Product.name == name).first()
            if product is None:
                db.add(
                    Product(
                        name=name,
                        description=description,
                        category=category,
                        price=price,
                    )
                )
                created += 1
            else:
                product.description = description
                product.category = category
                product.price = price
                updated += 1
        db.commit()

        category_counts = Counter(
            product.category for product in db.query(Product).all()
        )

    print(f"Catalog ready: {len(COURSES)} seeded courses ({created} created, {updated} updated).")
    print("Courses by category:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}")
    print("Vector synchronization is not configured yet; SQL catalog seeding is complete.")


if __name__ == "__main__":
    main()
