"""Event tracking API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models.user import User
from src.services.event_service import EventService
from src.services.auth_service import AuthService
from src.logging_config.config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


# Pydantic models
class EventData(BaseModel):
    """Single event data."""
    user_id: int
    product_id: int
    score: float = 0.0
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "product_id": 5,
                "score": 0.85,
                "created_at": "2026-08-10T14:30:00Z"
            }
        }


class BatchEventsRequest(BaseModel):
    """Batch events request (non-blocking ingestion)."""
    events: List[EventData]

    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "user_id": 1,
                        "product_id": 5,
                        "score": 0.85
                    },
                    {
                        "user_id": 1,
                        "product_id": 12,
                        "score": 0.92
                    }
                ]
            }
        }


class EventResponse(BaseModel):
    """Event response."""
    id: int
    user_id: int
    product_id: int
    score: float
    created_at: str

    class Config:
        from_attributes = True


class ActivitySummaryResponse(BaseModel):
    """User activity summary response."""
    user_id: int
    total_events: int
    unique_products: int
    avg_score: float


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


@router.post("/track", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def track_event(
    event: EventData,
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_auth_user)
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
    request: BatchEventsRequest,
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_auth_user)
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


@router.get("/summary", response_model=ActivitySummaryResponse)
async def get_activity_summary(
    hours: int = 24,
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_auth_user)
):
    """Get user's activity summary (insights)."""
    try:
        event_service = EventService(db)
        activity = event_service.get_user_activity_summary(user.id, hours)
        
        return ActivitySummaryResponse(
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
    hours: int = 72,
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_auth_user)
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
    hours: int = 48,
    auth_token: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_auth_user)
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
