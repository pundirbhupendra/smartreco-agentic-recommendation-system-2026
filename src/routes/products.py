"""Product API routes (CRUD, browse, search)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models.user import User
from src.services.product_service import ProductService
from src.services.auth_service import AuthService
from src.logging_config.config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/products", tags=["products"])


# Pydantic models
class ProductCreate(BaseModel):
    """Product creation request."""
    name: str
    description: str
    category: Optional[str] = None
    price: float

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Advanced LangGraph Patterns",
                "description": "Master multi-node agentic workflows...",
                "category": "AI/ML",
                "price": 99.99
            }
        }


class ProductUpdate(BaseModel):
    """Product update request."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None


class ProductResponse(BaseModel):
    """Product response."""
    id: int
    name: str
    description: str
    category: Optional[str]
    price: float
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# Dependency: verify admin user
async def verify_admin(
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> User:
    """Verify that user is admin."""
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required"
        )
    
    auth_service = AuthService(db)
    user = auth_service.get_current_user(auth_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Check admin role (for now, simple hardcoded check - can be enhanced)
    # In production, add is_admin field to User model
    if user.id not in [1]:  # Only user ID 1 is admin for now
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


@router.get("", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all products with pagination."""
    try:
        product_service = ProductService(db)
        products = product_service.get_all_products(skip, limit)
        return products
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )


@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    q: str = Query(..., min_length=1, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Search products by name or description."""
    try:
        product_service = ProductService(db)
        products = product_service.search_products(q, skip, limit)
        return products
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.get("/category/{category}", response_model=List[ProductResponse])
async def get_products_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get products by category."""
    try:
        product_service = ProductService(db)
        products = product_service.get_products_by_category(category, skip, limit)
        return products
    except Exception as e:
        logger.error(f"Error fetching products by category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )


@router.get("/top", response_model=List[ProductResponse])
async def get_top_products(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get top/trending products (for cold-start recommendations)."""
    try:
        product_service = ProductService(db)
        products = product_service.get_top_products(limit)
        return products
    except Exception as e:
        logger.error(f"Error fetching top products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get a single product by ID."""
    try:
        product_service = ProductService(db)
        product = product_service.get_product(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product"
        )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Create a new product (admin only, dual-write to SQL + Vector DB)."""
    try:
        product_service = ProductService(db)
        
        product_data = product.dict()
        created_product = product_service.create_product(product_data)
        
        logger.info(f"Product created: {created_product.name} (ID: {created_product.id})")
        return created_product
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Update a product (admin only, syncs to Vector DB)."""
    try:
        product_service = ProductService(db)
        
        # Check if product exists
        existing = product_service.get_product(product_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Update product
        update_data = product.dict(exclude_unset=True)
        updated_product = product_service.update_product(product_id, update_data)
        
        logger.info(f"Product updated: {product_id}")
        return updated_product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Delete a product (admin only, removes from SQL and Vector DB)."""
    try:
        product_service = ProductService(db)
        
        # Check if product exists
        existing = product_service.get_product(product_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Delete product
        product_service.delete_product(product_id)
        logger.info(f"Product deleted: {product_id}")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )
