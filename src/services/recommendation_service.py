"""Recommendation service - core recommendation logic."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.repositories.recommendation_repository import RecommendationRepository
from src.repositories.user_repository import UserRepository
from src.repositories.product_repository import ProductRepository
from src.services.event_service import EventService
from src.services.llm_service import LLMService
from src.database.models.recommendation import Recommendation
from src.logging_config.config import get_logger

logger = get_logger(__name__)


class RecommendationService:
    """Service for generating and managing recommendations."""

    def __init__(self, db: Session):
        self.db = db
        self.rec_repo = RecommendationRepository(db)
        self.user_repo = UserRepository(db)
        self.product_repo = ProductRepository(db)
        self.event_service = EventService(db)
        self.llm_service = LLMService()
        
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
            age = datetime.utcnow() - latest_rec.created_at
            if age < timedelta(hours=self.cache_ttl_hours):
                # Check if significant user activity
                should_refresh = self.event_service.should_refresh_recommendations(
                    user_id, latest_rec.created_at
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
            "generated_at": datetime.utcnow().isoformat(),
            "refresh_reason": "cold_start_user",
            "is_cached": False
        }

    def _generate_new_recommendation(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Generate a fresh recommendation based on user activity."""
        try:
            # Step 1: Get user activity context
            activity_summary = self.event_service.get_user_activity_summary(user_id, hours=48)
            activity_context = self.event_service.get_event_context(user_id, hours=48)
            
            if activity_summary["total_events"] == 0:
                return self._get_cold_start_recommendation(user_id)
            
            # Step 2: Extract user interests
            interests = self.llm_service.extract_user_interests(activity_context)
            logger.info(f"Extracted interests for user {user_id}: {interests}")
            
            # Step 3: Build semantic search query
            search_query = self.llm_service.build_search_query(activity_context, interests)
            logger.info(f"Generated search query for user {user_id}: {search_query}")
            
            # Step 4: Retrieve relevant products (simulated - will use Vector DB in production)
            # For now, search in SQL database
            retrieved_products = self.product_repo.search_products(
                " ".join(interests), limit=10
            )
            
            # Step 5: Evaluate retrieval quality
            retrieval_results = [
                {
                    "name": p.name,
                    "score": 0.8,  # Will be actual similarity score from Vector DB
                    "id": p.id
                }
                for p in retrieved_products
            ]
            quality_eval = self.llm_service.evaluate_retrieval_quality(search_query, retrieval_results)
            logger.info(f"Retrieval quality evaluation: {quality_eval}")
            
            # Step 6: If quality is poor, refine query and retry
            if not quality_eval.get("is_good_match", True) and len(retrieved_products) > 0:
                refined_query = self.llm_service.refine_search_query(
                    search_query,
                    "Initial results not relevant enough"
                )
                retrieved_products = self.product_repo.search_products(refined_query, limit=10)
                logger.info(f"Refined search query: {refined_query}")
            
            # Step 7: Generate persuasive narrative
            products_data = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price
                }
                for p in retrieved_products[:5]
            ]
            
            narrative = self.llm_service.generate_recommendation_narrative(
                user_id,
                interests,
                products_data,
                activity_context
            )
            logger.info(f"Generated narrative for user {user_id}")
            
            # Step 8: Store recommendation
            recommendation = self._store_recommendation(
                user_id,
                retrieved_products[:5],
                narrative,
                {
                    "interests": interests,
                    "search_query": search_query,
                    "quality_score": quality_eval.get("quality_score", 0.5),
                    "retrieval_count": len(retrieved_products)
                }
            )
            
            return self._format_recommendation(recommendation)
        
        except Exception as e:
            logger.error(f"Error generating recommendation for user {user_id}: {e}")
            return None

    def _store_recommendation(
        self,
        user_id: int,
        products: List,
        narrative: str,
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
                    "score": metadata.get("quality_score", 0.8),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
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
            "created_at": recommendation.created_at.isoformat(),
            "updated_at": recommendation.updated_at.isoformat()
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
