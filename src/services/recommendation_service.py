"""Recommendation service - core recommendation logic."""
from typing import Optional, List, Dict, Any, cast
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os
from sqlalchemy.orm import Session

from src.repositories.recommendation_repository import RecommendationRepository
from src.repositories.user_repository import UserRepository
from src.repositories.product_repository import ProductRepository
from src.services.event_service import EventService
from src.services.llm_service import LLMService
from src.database.models.recommendation import Recommendation
from src.logging_config.config import get_logger

logger = get_logger(__name__)


def _utcnow() -> datetime:
    """Return a naive UTC datetime for the existing database columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RecommendationService:
    """Service for generating and managing recommendations."""

    def __init__(self, db: Session):
        self.db = db
        self.rec_repo = RecommendationRepository(db)
        self.user_repo = UserRepository(db)
        self.product_repo = ProductRepository(db)
        self.event_service = EventService(db)
        self.llm_service = None
        if os.getenv("ENABLE_LLM_RECOMMENDATIONS", "false").lower() == "true":
            try:
                self.llm_service = LLMService()
            except ValueError:
                # Deterministic recommendations remain available without Mesh.
                self.llm_service = None
        
        # Caching configuration
        self.cache_ttl_hours = 6  # Refresh cache every 6 hours
        self.min_events_for_refresh = 5

    def get_or_generate_recommendation(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get existing recommendation or generate a new one if needed."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        # Check if user is cold start (new/inactive)
        event_count = self.event_service.event_repo.count_user_events(user_id)
        if event_count == 0:
            return self._get_cold_start_recommendation(user_id)
        
        # Check if cached recommendation is still valid
        latest_rec = self.rec_repo.get_latest_recommendation(user_id)
        if latest_rec:
            # Check if cache is still fresh
            created_at = cast(datetime, latest_rec.created_at)
            age = _utcnow() - created_at
            if age < timedelta(hours=self.cache_ttl_hours):
                # Check if significant user activity
                should_refresh = self.event_service.should_refresh_recommendations(
                    user_id, created_at
                )
                if not should_refresh:
                    return self._format_recommendation(latest_rec)
        
        # Generate new recommendation
        return self._generate_new_recommendation(user_id)

    def _get_cold_start_recommendation(self, user_id: int) -> Dict[str, Any]:
        """Get recommendations for new/cold-start users."""
        # For cold start users, recommend popular/trending products
        top_products = self.product_repo.get_top_products(limit=5)
        
        narrative = f"""
Welcome! We've curated our most popular courses to help you get started. 
Browse these courses and tell us what interests you by viewing them!
        """.strip()
        
        return {
            "user_id": user_id,
            "narrative": narrative,
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price,
                    "score": 0.8  # Default score for popular products
                }
                for p in top_products
            ],
            "generated_at": _utcnow().isoformat(),
            "refresh_reason": "cold_start_user",
            "is_cached": False
        }

    def _generate_new_recommendation(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Generate explainable recommendations from recent product activity."""
        try:
            events = self.event_service.event_repo.get_recent_user_events(user_id, hours=72)
            if not events:
                return self._get_cold_start_recommendation(user_id)

            category_scores: dict[str, float] = defaultdict(float)
            seen_product_ids = set()
            for event in events:
                product = self.product_repo.get_by_id(event.product_id)
                if product is None:
                    continue
                seen_product_ids.add(product.id)
                category_scores[product.category or "uncategorized"] += max(event.score, 0.1)

            candidates = []
            for product in self.product_repo.get_all(0, 1000):
                if product.id in seen_product_ids:
                    continue
                category_score = category_scores.get(product.category or "uncategorized", 0.0)
                if category_score > 0:
                    candidates.append((product, category_score))

            if not candidates:
                candidates = [
                    (product, 0.5)
                    for product in self.product_repo.get_top_products(limit=10)
                    if product.id not in seen_product_ids
                ]

            candidates.sort(key=lambda item: (-item[1], item[0].created_at), reverse=False)
            retrieved_products = [product for product, _ in candidates[:5]]
            max_category_score = max((score for _, score in candidates), default=1.0)
            scores = {
                product.id: round(min(0.99, 0.55 + (score / max_category_score) * 0.4), 2)
                for product, score in candidates[:5]
            }
            recommendation = self._store_recommendation(
                user_id, retrieved_products, {"scores": scores}
            )
            
            return self._format_recommendation(recommendation)
        
        except Exception as e:
            logger.error(f"Error generating recommendation for user {user_id}: {e}")
            return None

    def _store_recommendation(
        self,
        user_id: int,
        products: List,
        metadata: Dict[str, Any]
    ) -> Optional[Recommendation]:
        """Store recommendation in database."""
        try:
            # Store one recommendation per product
            recommendations = []
            for product in products[:5]:  # Limit to top 5
                rec_data = {
                    "user_id": user_id,
                    "product_id": product.id,
                    "score": metadata.get("scores", {}).get(product.id, 0.8),
                    "created_at": _utcnow(),
                    "updated_at": _utcnow()
                }
                rec = self.rec_repo.create(rec_data)
                recommendations.append(rec)
            
            # Clean up old recommendations (keep only 5 most recent)
            self.rec_repo.delete_user_old_recommendations(user_id, keep_count=5)
            
            return recommendations[0] if recommendations else None
        except Exception as e:
            logger.error(f"Error storing recommendation: {e}")
            return None

    def _format_recommendation(self, recommendation: Recommendation) -> Dict[str, Any]:
        """Format a recommendation object for API response."""
        product = self.product_repo.get_by_id(recommendation.product_id)
        if product is None:
            raise ValueError(
                f"Product {recommendation.product_id} no longer exists for recommendation "
                f"{recommendation.id}"
            )

        created_at = cast(datetime, recommendation.created_at)
        updated_at = cast(datetime, recommendation.updated_at)
        
        return {
            "id": recommendation.id,
            "user_id": recommendation.user_id,
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
            },
            "score": recommendation.score,
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat()
        }

    def get_user_recommendations(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get all recommendations for a user."""
        recommendations = self.rec_repo.get_user_recommendations(user_id, limit)
        return [self._format_recommendation(rec) for rec in recommendations]

    def get_recommendation_feed(self, user_id: int, limit: int = 5) -> Dict[str, Any]:
        """Get a personalized recommendation feed for a user."""
        recs = self.get_user_recommendations(user_id, limit)
        
        return {
            "user_id": user_id,
            "recommendations": recs,
            "total_count": len(recs),
            "last_updated": recs[0]["created_at"] if recs else None
        }
