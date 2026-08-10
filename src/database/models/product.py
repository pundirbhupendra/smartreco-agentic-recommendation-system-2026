from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

from src.database.db import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Example of a relationship to another table (if needed)
    # recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', description='{self.description}', price={self.price})>" 