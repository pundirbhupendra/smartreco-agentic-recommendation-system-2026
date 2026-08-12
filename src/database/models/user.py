
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.db import Base

if TYPE_CHECKING:
    from src.database.models.recommendation import Recommendation
    from src.database.models.user_activity import UserActivity
    from src.database.models.user_event import UserEvent

# Import related models at runtime to ensure SQLAlchemy relationship targets are registered.
import src.database.models.recommendation  # noqa: F401
import src.database.models.user_activity  # noqa: F401
import src.database.models.user_event  # noqa: F401



class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Example of a relationship to another table (if needed)
    recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="user")
    activities: Mapped[List["UserActivity"]] = relationship("UserActivity", back_populates="user")
    events: Mapped[List["UserEvent"]] = relationship("UserEvent", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    
