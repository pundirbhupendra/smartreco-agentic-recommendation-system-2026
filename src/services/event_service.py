"""Event service for user activity tracking and aggregation."""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from collections import defaultdict

from src.repositories.user_event_repository import UserEventRepository
from src.database.models.user_event import UserEvent


class EventService:
    """Service for managing user events and activity tracking."""

    def __init__(self, db: Session):
        self.db = db
        self.event_repo = UserEventRepository(db)

    def track_event(self, user_id: int, product_id: int, score: float = 0.0) -> UserEvent:
        """Track a single user event/activity."""
        event_data = {
            "user_id": user_id,
            "product_id": product_id,
            "score": score,
            "created_at": datetime.utcnow(),
        }
        return self.event_repo.create(event_data)

    def batch_track_events(self, events: List[Dict[str, Any]]) -> List[UserEvent]:
        """Efficiently batch track multiple events."""
        validated_events = []
        for event in events:
            validated_event = {
                "user_id": event.get("user_id"),
                "product_id": event.get("product_id"),
                "score": event.get("score", 0.0),
                "created_at": event.get("created_at", datetime.utcnow()),
            }
            validated_events.append(validated_event)
        
        return self.event_repo.batch_create_events(validated_events)

    def get_user_activity_summary(self, user_id: int, hours: int = 24) -> Dict[str, Any]:
        """Get a summary of user activity in the last N hours."""
        events = self.event_repo.get_recent_user_events(user_id, hours)
        
        # Group by product
        product_interactions = defaultdict(int)
        total_score = 0.0
        
        for event in events:
            if event.product_id:
                product_interactions[event.product_id] += 1
            total_score += event.score
        
        return {
            "user_id": user_id,
            "total_events": len(events),
            "unique_products": len(product_interactions),
            "product_interactions": dict(product_interactions),
            "avg_score": total_score / len(events) if events else 0.0,
            "recent_events": events[:10],  # Last 10 events
        }

    def get_user_interests(self, user_id: int, hours: int = 72) -> List[int]:
        """Get list of product IDs user is interested in (viewed/interacted with)."""
        events = self.event_repo.get_recent_user_events(user_id, hours)
        product_ids = list(set([event.product_id for event in events if event.product_id]))
        return product_ids

    def should_refresh_recommendations(self, user_id: int, last_recommendation_time: datetime) -> bool:
        """Determine if recommendations should be refreshed based on user activity."""
        # Get events since last recommendation
        events_since = self.event_repo.get_user_events_since(user_id, last_recommendation_time)
        
        # Threshold: refresh if 5+ new events or 24+ hours since last recommendation
        significant_activity = len(events_since) >= 5
        time_elapsed = datetime.utcnow() - last_recommendation_time
        time_threshold = time_elapsed >= timedelta(hours=24)
        
        return significant_activity or time_threshold

    def get_event_context(self, user_id: int, hours: int = 48) -> str:
        """Get a text description of user's recent activity for LLM context."""
        activity = self.get_user_activity_summary(user_id, hours)
        
        context = f"""
User Activity Summary (Last {hours} hours):
- Total interactions: {activity['total_events']}
- Unique products viewed: {activity['unique_products']}
- Average engagement score: {activity['avg_score']:.2f}
- Products of interest: {activity['product_interactions']}
        """
        return context.strip()

    def cleanup_old_events(self, days: int = 90) -> int:
        """Delete events older than N days (data retention)."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_events = self.db.query(UserEvent).filter(
            UserEvent.created_at < cutoff_date
        ).delete()
        self.db.commit()
        return old_events
