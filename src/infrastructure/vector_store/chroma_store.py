"""Local Chroma vector store for semantic product retrieval."""

from pathlib import Path
from typing import Any, Iterable
import os

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from src.services.product_service import ProductService


class ChromaProductStore:
    """Persist and semantically search product descriptions with Chroma."""

    def __init__(
        self,
        path: str | None = None,
        collection_name: str = "smartreco-products",
        embedding_model: str | None = None,
    ) -> None:
        storage_path = path or os.getenv("CHROMA_PATH", "./Data/chroma")
        Path(storage_path).expanduser().mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=storage_path)
        model_name = embedding_model or os.getenv(
            "EMBEDDING_MODEL", "all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=SentenceTransformerEmbeddingFunction(
                model_name=model_name
            ),
        )

    def upsert_product(self, product: Any) -> None:
        """Insert or update one SQL product in Chroma."""
        self.collection.upsert(
            ids=[str(product.id)],
            documents=[ProductService.get_product_embedding_context(product)],
            metadatas=[
                {
                    "name": product.name,
                    "category": product.category or "uncategorized",
                    "price": float(product.price),
                }
            ],
        )

    def upsert_products(self, products: Iterable[Any]) -> int:
        """Insert or update products in one Chroma request."""
        products = list(products)
        if not products:
            return 0

        self.collection.upsert(
            ids=[str(product.id) for product in products],
            documents=[
                ProductService.get_product_embedding_context(product)
                for product in products
            ],
            metadatas=[
                {
                    "name": product.name,
                    "category": product.category or "uncategorized",
                    "price": float(product.price),
                }
                for product in products
            ],
        )
        return len(products)

    def delete_product(self, product_id: int) -> None:
        """Remove one product vector by SQL product ID."""
        self.collection.delete(ids=[str(product_id)])

    def query(self, text: str, limit: int = 5) -> list[dict[str, Any]]:
        """Return products nearest to a natural-language query."""
        result = self.collection.query(
            query_texts=[text],
            n_results=max(1, min(limit, 20)),
            include=["metadatas", "distances", "documents"],
        )
        ids = result.get("ids", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        documents = result.get("documents", [[]])[0]
        return [
            {
                "id": int(product_id),
                "metadata": metadata or {},
                "distance": distance,
                "document": document,
            }
            for product_id, metadata, distance, document in zip(
                ids, metadatas, distances, documents
            )
        ]

    def count(self) -> int:
        """Return the number of vectors currently stored."""
        return self.collection.count()
