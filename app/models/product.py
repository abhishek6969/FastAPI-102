import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, Integer, Boolean, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] =mapped_column(default=uuid.uuid4,primary_key=True)        # primary_key, default=uuid.uuid4
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)                    # String(200), nullable=False, index=True
    description: Mapped[str | None] = mapped_column(Text, nullable=True)      # Text, nullable=True (optional field)
    # Numeric(10, 2) means 10 digits total, with 2 after the decimal (e.g., 99,999,999.99)
    # Why Mapped[float]? FastAPI/Pydantic handle floats better in JSON responses.
    # For high-stakes financial apps, you would use Python's Decimal type instead.
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    stock: Mapped[int] = mapped_column(Integer, default=0, server_default="0")                   # Integer, default=0, server_default="0"
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)                # String(100), index=True, nullable=False
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")              # Boolean, default=True, server_default="true"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())         # DateTime(timezone=True), server_default=func.now()
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())  # DateTime(timezone=True), onupdate=func.now()

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
