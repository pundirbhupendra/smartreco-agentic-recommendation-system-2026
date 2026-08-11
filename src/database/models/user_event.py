from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.db import Base

if TYPE_CHECKING:
    from src.database.models.product import Product
    from src.database.models.user import User


class UserEvent(Base):
    __tablename__ = "user_events"

  
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    # Similarity or confidence score (e.g., 0.95)
    score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow)

 

    # Example of a relationship to another table (if needed)
    user: Mapped["User"] = relationship("User", back_populates="events")

    def __repr__(self):
        return f"<UserEvent(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, score={self.score})"  