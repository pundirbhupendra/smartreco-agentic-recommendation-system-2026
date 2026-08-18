"""Product service for product management with dual-write to SQL and Vector DB."""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import os

from src.repositories.product_repository import ProductRepository
from src.database.models.product import Product
from src.infrastructure.vector_store.qdrant_store import QdrantProductStore


class ProductService:
    """Service for managing products with SQL and Vector DB sync."""

    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.vector_db_enabled = os.getenv("ENABLE_VECTOR_DB", "true").lower() == "true"
        self._vector_store = None

    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create a new product (dual-write to SQL + Vector DB)."""
        # Create in SQL database
        product = self.product_repo.create(product_data)
        
        # Sync to Vector DB if enabled
        if self.vector_db_enabled:
            self._sync_to_vector_db(product, operation="create")
        
        return product

    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Product]:
        """Update a product (dual-write to SQL + Vector DB)."""
        # Update in SQL database
        product = self.product_repo.update(product_id, product_data)
        
        # Sync to Vector DB if enabled
        if product and self.vector_db_enabled:
            self._sync_to_vector_db(product, operation="update")
        
        return product

    def delete_product(self, product_id: int) -> bool:
        """Delete a product (remove from SQL + Vector DB)."""
        product = self.product_repo.get_by_id(product_id)
        
        # Delete from Vector DB first if enabled
        if product and self.vector_db_enabled:
            self._sync_to_vector_db(product, operation="delete")
        
        # Delete from SQL database
        return self.product_repo.delete(product_id)

    def get_product(self, product_id: int) -> Optional[Product]:
        """Get a single product by ID."""
        return self.product_repo.get_by_id(product_id)

    def get_all_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """Get all products with pagination."""
        return self.product_repo.get_all(skip, limit)

    def search_products(self, query: str, skip: int = 0, limit: int = 100) -> List[Product]:
        """Search products by name or description."""
        return self.product_repo.search_products(query, skip, limit)

    def get_products_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Product]:
        """Get products filtered by category."""
        return self.product_repo.get_by_category(category, skip, limit)

    def get_top_products(self, limit: int = 10) -> List[Product]:
        """Get top/trending products (for cold-start users)."""
        return self.product_repo.get_top_products(limit)

    def get_products_by_ids(self, product_ids: List[int]) -> List[Product]:
        """Get multiple products by their IDs."""
        return self.product_repo.get_products_by_ids(product_ids)

    def sync_all_products_to_vector_db(self) -> int:
        """Sync all products to Vector DB (bulk operation)."""
        if not self.vector_db_enabled:
            return 0
        
        products = self.product_repo.get_all(skip=0, limit=10000)
        return self._get_vector_store().upsert_products(products)

    def _get_vector_store(self) -> QdrantProductStore:
        if self._vector_store is None:
            self._vector_store = QdrantProductStore()
        return self._vector_store

    def _sync_to_vector_db(self, product: Product, operation: str = "create") -> bool:
        """Synchronize one product with the configured remote Qdrant store."""
        store = self._get_vector_store()
        if operation in {"create", "update"}:
            store.upsert_product(product)
        elif operation == "delete":
            store.delete_product(product.id)
        else:
            raise ValueError(f"Unsupported vector operation: {operation}")
        return True

    @staticmethod
    def get_product_embedding_context(product: Product) -> str:
        """Generate text context for embedding a product."""
        context = f"""
Product: {product.name}
Description: {product.description}
Category: {product.category}
Price: ${product.price}
        """
        return context.strip()
