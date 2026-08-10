"""Product repository for database operations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database.models.product import Product
from src.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for Product model operations."""

    def __init__(self, db: Session):
        super().__init__(db, Product)

    def get_by_name(self, name: str) -> Optional[Product]:
        """Get product by name."""
        return self.db.query(Product).filter(Product.name == name).first()

    def get_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Product]:
        """Get products by category."""
        return self.db.query(Product).filter(
            Product.category == category
        ).offset(skip).limit(limit).all()

    def get_top_products(self, limit: int = 10) -> List[Product]:
        """Get top-rated or trending products."""
        return self.db.query(Product).order_by(
            Product.created_at.desc()
        ).limit(limit).all()

    def search_products(self, query: str, skip: int = 0, limit: int = 100) -> List[Product]:
        """Search products by name or description (full-text search alternative)."""
        return self.db.query(Product).filter(
            (Product.name.ilike(f"%{query}%")) | 
            (Product.description.ilike(f"%{query}%"))
        ).offset(skip).limit(limit).all()

    def get_products_by_ids(self, product_ids: List[int]) -> List[Product]:
        """Get multiple products by IDs."""
        return self.db.query(Product).filter(Product.id.in_(product_ids)).all()
