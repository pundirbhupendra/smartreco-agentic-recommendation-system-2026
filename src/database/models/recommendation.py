
import datetime

from database.models.user import User
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

from src.database.db import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Example of a relationship to another table (if needed)
    user: Mapped["User"] = relationship("User", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, score='{self.score}')>"