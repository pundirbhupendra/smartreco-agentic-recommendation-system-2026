
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.database.models.recommendation import Recommendation
    from src.database.models.user_activity import UserActivity
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship,Mapped,mapped_column
from src.database.db import Base



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

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    
