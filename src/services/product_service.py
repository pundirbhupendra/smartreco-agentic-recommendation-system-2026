"""Product service for product management with dual-write to SQL and Vector DB."""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import os

from src.repositories.product_repository import ProductRepository
from src.database.models.product import Product


class ProductService:
    """Service for managing products with SQL and Vector DB sync."""

    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        # Vector DB integration will be injected or loaded on demand
        self.vector_db_enabled = os.getenv("ENABLE_VECTOR_DB", "true").lower() == "true"

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
        count = 0
        
        for product in products:
            try:
                self._sync_to_vector_db(product, operation="create")
                count += 1
            except Exception as e:
                # Log error but continue with other products
                print(f"Error syncing product {product.id} to Vector DB: {e}")
        
        return count

    def _sync_to_vector_db(self, product: Product, operation: str = "create") -> bool:
        """Internal method to sync a product with Vector DB (Pinecone)."""
        # This will be implemented when we set up Pinecone integration
        # For now, this is a placeholder that will be called by product operations
        try:
            # Import here to avoid circular dependencies
            from src.infrastructure.vector_store.pinecone_client import PineconeClient
            
            client = PineconeClient()
            
            if operation == "create" or operation == "update":
                client.upsert_product(product)
            elif operation == "delete":
                client.delete_product(product.id)
            
            return True
        except ImportError:
            # Vector DB not configured, skip silently
            return False
        except Exception as e:
            # Log but don't fail - products are still in SQL DB
            print(f"Warning: Failed to sync to Vector DB: {e}")
            return False

    def get_product_embedding_context(self, product: Product) -> str:
        """Generate text context for embedding a product."""
        context = f"""
Product: {product.name}
Description: {product.description}
Category: {product.category}
Price: ${product.price}
        """
        return context.strip()
