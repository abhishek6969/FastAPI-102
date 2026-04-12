import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0)


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    unit_price: float
    subtotal: float
    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    # Nested Validation: Pydantic will validate every item in this list 
    # against the OrderItemCreate rules!
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: OrderStatus
    total_amount: float
    created_at: datetime
    updated_at: datetime | None
    # items: list[OrderItemResponse] works perfectly because 
    # from_attributes=True is also set in OrderItemResponse (recursive).
    items: list[OrderItemResponse]
    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

# 