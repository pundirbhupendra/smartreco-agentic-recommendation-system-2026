"""Recommendations API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models.user import User
from src.services.recommendation_service import RecommendationService
from src.services.auth_service import AuthService
from src.logging_config.config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# Pydantic models
class ProductRecommendation(BaseModel):
    """Product in recommendation."""
    id: int
    name: str
    description: str
    price: float

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Recommendation response."""
    id: int
    user_id: int
    product: ProductRecommendation
    score: float
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class RecommendationFeedResponse(BaseModel):
    """Recommendation feed response."""
    user_id: int
    recommendations: List[RecommendationResponse]
    total_count: int
    last_updated: Optional[str]


# Dependency: verify authenticated user
async def get_auth_user(
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> User:
    """Get authenticated user from token."""
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
    
    return user


@router.get("/{user_id}", response_model=List[RecommendationResponse])
async def get_recommendations(
    user_id: int,
    limit: int = Query(5, ge=1, le=20),
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_auth_user)
):
    """Get personalized recommendations for a user."""
    try:
        # Verify user can only access their own recommendations
        if user_id != user.id and user.id not in [1]:  # Allow admin to see any user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access recommendations for other users"
            )
        
        recommendation_service = RecommendationService(db)
        recommendations = recommendation_service.get_user_recommendations(user_id, limit)
        
        return recommendations
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recommendations"
        )


@router.get("/{user_id}/feed", response_model=RecommendationFeedResponse)
async def get_recommendation_feed(
    user_id: int,
    limit: int = Query(5, ge=1, le=20),
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_auth_user)
):
    """Get recommendation feed for a user."""
    try:
        # Verify user can only access their own recommendations
        if user_id != user.id and user.id not in [1]:  # Allow admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access recommendations for other users"
            )
        
        recommendation_service = RecommendationService(db)
        feed = recommendation_service.get_recommendation_feed(user_id, limit)
        
        return feed
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommendation feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recommendation feed"
        )


@router.post("/{user_id}/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_recommendations(
    user_id: int,
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_auth_user)
):
    """Generate fresh recommendations for a user (async-like)."""
    try:
        # Verify user can only generate for themselves
        if user_id != user.id and user.id not in [1]:  # Allow admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot generate recommendations for other users"
            )
        
        recommendation_service = RecommendationService(db)
        recommendations = recommendation_service.get_or_generate_recommendation(user_id)
        
        if not recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or no recommendations could be generated"
            )
        
        logger.info(f"Generated recommendations for user {user_id}")
        
        return {
            "status": "accepted",
            "user_id": user_id,
            "message": "Recommendations are being generated"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@router.get("/health/status", response_model=dict)
async def recommendation_status(
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_auth_user)
):
    """Check recommendation service health and status."""
    try:
        # This is a simple health check
        return {
            "status": "healthy",
            "service": "recommendation_engine",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )
