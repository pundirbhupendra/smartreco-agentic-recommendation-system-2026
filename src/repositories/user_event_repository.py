"""User event repository for database operations."""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database.models.user_event import UserEvent
from src.repositories.base_repository import BaseRepository


class UserEventRepository(BaseRepository[UserEvent]):
    """Repository for UserEvent model operations."""

    def __init__(self, db: Session):
        super().__init__(db, UserEvent)

    def get_user_events(self, user_id: int, skip: int = 0, limit: int = 100) -> List[UserEvent]:
        """Get all events for a user."""
        return self.db.query(UserEvent).filter(
            UserEvent.user_id == user_id
        ).order_by(UserEvent.created_at.desc()).offset(skip).limit(limit).all()

    def get_user_events_since(self, user_id: int, since: datetime) -> List[UserEvent]:
        """Get user events since a specific datetime."""
        return self.db.query(UserEvent).filter(
            and_(UserEvent.user_id == user_id, UserEvent.created_at >= since)
        ).order_by(UserEvent.created_at.desc()).all()

    def get_recent_user_events(self, user_id: int, hours: int = 24) -> List[UserEvent]:
        """Get user events from the last N hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.get_user_events_since(user_id, since)

    def get_events_by_type(self, user_id: int, event_type: str) -> List[UserEvent]:
        """Get events of a specific type for a user."""
        return self.db.query(UserEvent).filter(
            and_(UserEvent.user_id == user_id, UserEvent.product_id == event_type)
        ).order_by(UserEvent.created_at.desc()).all()

    def get_product_views_for_user(self, user_id: int) -> List[int]:
        """Get list of product IDs viewed by user."""
        events = self.db.query(UserEvent).filter(
            UserEvent.user_id == user_id
        ).all()
        return list(set([event.product_id for event in events if event.product_id]))

    def batch_create_events(self, events_data: List[dict]) -> List[UserEvent]:
        """Efficiently create multiple events at once."""
        events = [UserEvent(**event_data) for event_data in events_data]
        self.db.add_all(events)
        self.db.commit()
        return events

    def count_user_events(self, user_id: int) -> int:
        """Get total event count for a user."""
        return self.db.query(UserEvent).filter(UserEvent.user_id == user_id).count()
