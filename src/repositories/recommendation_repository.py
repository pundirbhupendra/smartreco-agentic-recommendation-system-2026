"""Recommendation repository for database operations."""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from src.database.models.recommendation import Recommendation
from src.repositories.base_repository import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """Repository for Recommendation model operations."""

    def __init__(self, db: Session):
        super().__init__(db, Recommendation)

    def get_user_recommendations(self, user_id: int, limit: int = 5) -> List[Recommendation]:
        """Get latest recommendations for a user."""
        return self.db.query(Recommendation).filter(
            Recommendation.user_id == user_id
        ).order_by(desc(Recommendation.created_at)).limit(limit).all()

    def get_latest_recommendation(self, user_id: int) -> Optional[Recommendation]:
        """Get the most recent recommendation for a user."""
        return self.db.query(Recommendation).filter(
            Recommendation.user_id == user_id
        ).order_by(desc(Recommendation.created_at)).first()

    def get_recommendations_since(self, user_id: int, since: datetime) -> List[Recommendation]:
        """Get recommendations created since a specific datetime."""
        return self.db.query(Recommendation).filter(
            and_(Recommendation.user_id == user_id, Recommendation.created_at >= since)
        ).order_by(desc(Recommendation.created_at)).all()

    def get_recommendations_for_product(self, product_id: int) -> List[Recommendation]:
        """Get all recommendations that include a specific product."""
        return self.db.query(Recommendation).filter(
            Recommendation.product_id == product_id
        ).order_by(desc(Recommendation.created_at)).all()

    def recommendation_exists(self, user_id: int, product_id: int) -> bool:
        """Check if a recommendation exists for user-product pair."""
        return self.db.query(Recommendation).filter(
            and_(Recommendation.user_id == user_id, Recommendation.product_id == product_id)
        ).first() is not None

    def get_active_recommendations(self, hours: int = 24) -> List[Recommendation]:
        """Get recommendations created in the last N hours (for refresh checking)."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Recommendation).filter(
            Recommendation.created_at >= since
        ).all()

    def delete_user_old_recommendations(self, user_id: int, keep_count: int = 5) -> int:
        """Delete old recommendations for a user, keeping only the latest N."""
        recommendations = self.db.query(Recommendation).filter(
            Recommendation.user_id == user_id
        ).order_by(desc(Recommendation.created_at)).offset(keep_count).all()
        
        for rec in recommendations:
            self.db.delete(rec)
        
        self.db.commit()
        return len(recommendations)
