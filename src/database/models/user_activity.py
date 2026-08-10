import datetime

from database.models.user import User
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.models.product import Product
from src.database.db import Base


class UserActivity(Base):
    __tablename__ = "user_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    activity_type: Mapped[str] = mapped_column(String)
    activity_data: Mapped[str] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Example of a relationship to another table (if needed)
    user: Mapped["User"] = relationship("User", back_populates="activities")
    products: Mapped[list["Product"]] = relationship("Product", secondary="user_activity_products", back_populates="user_activities")

    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, activity_type='{self.activity_type}', activity_data='{self.activity_data}')>"