"""Event tracking API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models.user import User
from src.deps import CurrentUser, DatabaseSession
from src.schemas import ActivitySummaryOut, EventBatch, EventIn, EventOut
from src.services.event_service import EventService
from src.logging_config.config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/track", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def track_event(
    event: EventIn,
    db: DatabaseSession,
    user: CurrentUser,
):
    """Track a single user event (real-time)."""
    try:
        # Verify user can only track their own events
        if event.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot track events for other users"
            )
        
        event_service = EventService(db)
        tracked_event = event_service.track_event(
            user_id=event.user_id,
            product_id=event.product_id,
            score=event.score
        )
        
        return tracked_event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track event"
        )


@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def batch_track_events(
    request: EventBatch,
    db: DatabaseSession,
    user: CurrentUser,
):
    """Batch track multiple events (non-blocking, efficient)."""
    try:
        # Verify all events belong to authenticated user
        for event in request.events:
            if event.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot track events for other users"
                )
        
        event_service = EventService(db)
        events_data = [
            {
                "user_id": event.user_id,
                "product_id": event.product_id,
                "score": event.score,
                "created_at": event.created_at or datetime.utcnow(),
            }
            for event in request.events
        ]
        
        tracked_events = event_service.batch_track_events(events_data)
        
        logger.info(f"Batched {len(tracked_events)} events for user {user.id}")
        
        return {
            "status": "accepted",
            "events_count": len(tracked_events),
            "user_id": user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error batch tracking events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch track events"
        )


@router.get("/summary", response_model=ActivitySummaryOut)
async def get_activity_summary(
    db: DatabaseSession,
    user: CurrentUser,
    hours: int = 24,
):
    """Get user's activity summary (insights)."""
    try:
        event_service = EventService(db)
        activity = event_service.get_user_activity_summary(user.id, hours)
        
        return ActivitySummaryOut(
            user_id=user.id,
            total_events=activity["total_events"],
            unique_products=activity["unique_products"],
            avg_score=activity["avg_score"]
        )
    except Exception as e:
        logger.error(f"Error getting activity summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity summary"
        )


@router.get("/interests", response_model=dict)
async def get_user_interests(
    db: DatabaseSession,
    user: CurrentUser,
    hours: int = 72,
):
    """Get user's interests based on recent activity."""
    try:
        event_service = EventService(db)
        interests = event_service.get_user_interests(user.id, hours)
        
        return {
            "user_id": user.id,
            "interests": interests,
            "period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting user interests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get interests"
        )


@router.get("/context", response_model=dict)
async def get_activity_context(
    db: DatabaseSession,
    user: CurrentUser,
    hours: int = 48,
):
    """Get activity context (text description for LLM)."""
    try:
        event_service = EventService(db)
        context = event_service.get_event_context(user.id, hours)
        
        return {
            "user_id": user.id,
            "context": context,
            "period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting activity context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get context"
        )
