from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductResponse , ProductUpdate
from app.services import product_service
from app.models.user import User , UserRole
from app.core.deps import get_current_user, require_role

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate, 
    db: AsyncSession = Depends(get_db),
    # This route allows both Sellers and Admins.
    current_user : User = Depends(require_role(UserRole.seller, UserRole.admin))
):
    return await product_service.create_product(db, product_data)

@router.get("/", response_model=list[ProductResponse])
async def get_products(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db),):
    # Notice: No get_current_user dependency here. This route is PUBLIC.
    return await product_service.get_products(db, skip, limit)

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    product = await product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    if not product.is_active:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Product is deactivated")
    return product

@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: UUID, product_data: ProductUpdate, db: AsyncSession = Depends(get_db),current_user : User = Depends(require_role(UserRole.seller, UserRole.admin))):
    try:
        product = await product_service.update_product(db, product_id, product_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.delete("/{product_id}", response_model=ProductResponse)
async def delete_product(product_id: UUID, db: AsyncSession = Depends(get_db),current_user : User = Depends(require_role(UserRole.seller, UserRole.admin))):
    product = await product_service.delete_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product