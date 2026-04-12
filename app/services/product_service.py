from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate 

async def get_product(db: AsyncSession, product_id: UUID) -> Product | None:
    # scalar_one_or_none(): Returns exactly one row if found, 
    # or None if no match. If multiple rows found, it raises an error.
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 10) -> list[Product]:
    # We always filter by is_active so customers don't see deleted products.
    result = await db.execute(select(Product).where(Product.is_active == True).offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
    product = Product(**product_data.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product

async def update_product(db: AsyncSession, product_id: UUID, product_data: ProductUpdate) -> Product | None:
    product = await get_product(db, product_id)
    if not product:
        return None

    if not product.is_active:
        raise ValueError("Cannot update a deactivated Product.")
    
    # exclude_unset=True: This ensures we ONLY update the fields 
    # the client actually sent in the request (partial update).
    for field, value in product_data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.flush()
    await db.refresh(product)
    return product

async def delete_product(db: AsyncSession, product_id: UUID) -> Product | None:
    product = await get_product(db, product_id)
    if not product:
        return None
    product.is_active = False
    await db.flush()
    await db.refresh(product)
    return product
