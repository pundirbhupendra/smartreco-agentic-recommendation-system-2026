"""Qdrant vector store configured entirely through `.env`."""

from typing import Any, Iterable

import httpx
from qdrant_client import QdrantClient, models

from src.config.settings import settings


class QdrantProductStore:
    """Store and retrieve products in the configured Qdrant instance."""

    vector_size = 1536

    def __init__(self) -> None:
        if not settings.QDRANT_URL:
            raise ValueError("QDRANT_URL is required in .env")
        if not settings.QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY is required in .env")
        if not settings.MESH_API_KEY:
            raise ValueError("MESH_API_KEY is required for product embeddings")

        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=30,
        )
        self.collection_name = settings.QDRANT_COLLECTION
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        if any(item.name == self.collection_name for item in collections):
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    @staticmethod
    def _embed_texts(texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{settings.MESH_BASE_URL.rstrip('/')}/embeddings",
            headers={
                "Authorization": f"Bearer {settings.MESH_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": settings.MESH_EMBEDDING_MODEL, "input": texts},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        embeddings = payload.get("data")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise RuntimeError("Mesh returned an invalid embedding response")
        vectors = [item.get("embedding") for item in embeddings]
        if any(not isinstance(vector, list) for vector in vectors):
            raise RuntimeError("Mesh returned a malformed embedding vector")
        if any(len(vector) != QdrantProductStore.vector_size for vector in vectors):
            raise RuntimeError("Embedding size does not match Qdrant collection")
        return vectors

    @staticmethod
    def _document(product: Any) -> str:
        return (
            f"Product: {product.name}\n"
            f"Description: {product.description}\n"
            f"Category: {product.category}\n"
            f"Price: ${product.price}"
        )

    @staticmethod
    def _payload(product: Any) -> dict[str, Any]:
        return {
            "name": product.name,
            "description": product.description,
            "category": product.category or "uncategorized",
            "price": float(product.price),
        }

    def upsert_product(self, product: Any) -> int:
        return self.upsert_products([product])

    def upsert_products(self, products: Iterable[Any]) -> int:
        products = list(products)
        if not products:
            return 0
        vectors = self._embed_texts([
            self._document(product)
            for product in products
        ])
        points = [
            models.PointStruct(
                id=int(product.id),
                vector=vector,
                payload=self._payload(product),
            )
            for product, vector in zip(products, vectors)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def delete_product(self, product_id: int) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[int(product_id)]),
        )

    def query(self, text: str, limit: int = 5) -> list[dict[str, Any]]:
        vector = self._embed_texts([text])[0]
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=max(1, min(limit, 20)),
            with_payload=True,
        ).points
        return [
            {"id": int(result.id), "score": float(result.score), "metadata": result.payload or {}}
            for result in results
        ]

    def count(self) -> int:
        return self.client.count(collection_name=self.collection_name, exact=True).count
