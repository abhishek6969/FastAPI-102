import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    String, Numeric, Integer, Boolean, DateTime,
    ForeignKey, Enum, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# --- Order Status Enum ---
# Python's enum.Enum creates a fixed set of allowed values.
# SQLAlchemy's Enum() type maps this to PostgreSQL's ENUM type,
# which enforces valid values AT THE DATABASE LEVEL.
# Trying to INSERT status='banana' → PostgreSQL rejects it.
class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    # Inheriting from BOTH str and enum.Enum makes JSON serialization
    # work automatically — FastAPI can serialize it without custom logic.


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)           # primary_key, default=uuid.uuid4

    # --- Foreign Key ---
    # ForeignKey("users.id") creates a CONSTRAINT in PostgreSQL:
    #   FOREIGN KEY (user_id) REFERENCES users(id)
    # This means: user_id MUST be a valid id in the users table.
    # If you try to insert an order with a fake user_id → IntegrityError.
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.pending, server_default="pending"
    )
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())        # same pattern as User/Product
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now()) # same pattern

    # --- Relationships ---
    # relationship() does NOT create a database column.
    # It tells SQLAlchemy: "When I access order.items, run a SELECT
    # on order_items WHERE order_id = this order's id."
    # back_populates creates a bidirectional link:
    #   order.items → list of OrderItems
    #   order_item.order → the parent Order
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status})>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True , default=uuid.uuid4)               # primary_key, default=uuid.uuid4
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # Why SNAPSHOT the price here? 
    # If the product price changes in the future, the receipt for this 
    # specific order must still show the price paid at the time of purchase.
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # --- Relationships ---
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
    # No back_populates on product — we don't need product.order_items

    def __repr__(self) -> str:
        return f"<OrderItem(product_id={self.product_id}, qty={self.quantity})>"
