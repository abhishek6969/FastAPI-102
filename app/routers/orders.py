
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services import order_service
from app.models.user import User , UserRole
from app.core.deps import get_current_user , require_role

router = APIRouter(prefix="/orders", tags=["Orders"])


# POST /orders?user_id=xxx — Create a new order
@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    try:
        # We use current_user.id from the token instead of trusting 
        # a user_id from the JSON body. This prevents "Identity Theft".
        return await order_service.create_order(db, current_user.id, order_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# GET /orders/{order_id} — Get single order with items
@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: UUID, db: AsyncSession = Depends(get_db),current_user : User = Depends(get_current_user)):
    order = await order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


# GET /orders/user/{user_id} — Get all orders for a user
@router.get("/user/{user_id}", response_model=list[OrderResponse])
async def get_user_orders(user_id: UUID, db: AsyncSession = Depends(get_db),current_user : User = Depends(get_current_user)):
    return await order_service.get_user_orders(db, user_id)


# PATCH /orders/{order_id}/status — Update order status
@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    status_data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user : User = Depends(require_role( UserRole.admin))
):
    order = await order_service.update_order_status(db, order_id, status_data)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
