"""Shared Pydantic request and response models for SmartReco."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime


class EventIn(BaseModel):
    user_id: int
    product_id: int
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: Optional[datetime] = None


class EventBatch(BaseModel):
    events: list[EventIn] = Field(min_length=1, max_length=100)


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    score: float
    created_at: datetime


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    category: Optional[str] = None
    price: float
    created_at: datetime
    updated_at: datetime


class RecommendationProductOut(BaseModel):
    id: int
    name: str
    description: str
    price: float


class RecommendationOut(BaseModel):
    id: int
    user_id: int
    product: RecommendationProductOut
    score: float
    created_at: str
    updated_at: str


class RecommendationFeedOut(BaseModel):
    user_id: int
    recommendations: list[RecommendationOut]
    total_count: int
    last_updated: Optional[str] = None


class ActivitySummaryOut(BaseModel):
    user_id: int
    total_events: int
    unique_products: int
    avg_score: float


class APIMessage(BaseModel):
    message: str
    details: Optional[Any] = None
