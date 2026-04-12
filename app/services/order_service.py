from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderStatusUpdate


async def create_order(db: AsyncSession, user_id: UUID, order_data: OrderCreate) -> Order:
    """
    The most complex service function in our app.
    Think of it as a cashier at a store:
    1. Scan each item (validate products exist)
    2. Check shelf stock (enough quantity?)
    3. Ring up prices (snapshot from current price)
    4. Calculate total
    5. Remove items from shelf (reduce stock)
    6. Print receipt (create order + items in DB)
    """

    order_items = []
    total_amount = 0.0

    # --- Step 1 & 2: Validate each item ---
    for item_data in order_data.items:
        # Fetch the product from DB
        result = await db.execute(
            select(Product).where(Product.id == item_data.product_id)
        )
        product = result.scalar_one_or_none()

        # Does this product exist?
        if not product:
            raise ValueError(f"Product {item_data.product_id} not found")

        # Is it active?
        if not product.is_active:
            raise ValueError(f"Product '{product.name}' is no longer available")

        # Is there enough stock?
        if product.stock < item_data.quantity:
            raise ValueError(
                f"Not enough stock for '{product.name}'. "
                f"Available: {product.stock}, Requested: {item_data.quantity}"
            )

        # --- Step 3: Snapshot price ---
        # Why? If the store owner changes the price tomorrow, 
        # this order must still reflect the price from TODAY.
        unit_price = float(product.price)
        subtotal = unit_price * item_data.quantity

        # --- Step 4: Accumulate total ---
        total_amount += subtotal

        # --- Step 5: Reduce stock ---
        product.stock -= item_data.quantity

        # --- Step 6: Build the OrderItem ---
        order_item = OrderItem(
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        order_items.append(order_item)

    # --- Step 7: Create the Order ---
    order = Order(
        user_id=user_id,
        total_amount=round(total_amount, 2),
        items=order_items,       # SQLAlchemy handles the FK linking!
    )

    db.add(order)
    # Flush prepares the SQL but doesn't finish the transaction.
    # The actual "Commit" happens in our get_db dependency.
    await db.flush()

    return await get_order(db, order.id)


async def get_order(db: AsyncSession, order_id: UUID) -> Order | None:
    # We MUST use selectinload here.
    # Why? Standard lazy-loading (accessing order.items later) 
    # doesn't work in async and will crash your app.
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    return result.scalar_one_or_none()


async def get_user_orders(db: AsyncSession, user_id: UUID) -> list[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())    # Newest first
    )
    return list(result.scalars().all())


async def update_order_status(
    db: AsyncSession, order_id: UUID, status_data: OrderStatusUpdate
) -> Order | None:
    order = await get_order(db, order_id)
    if not order:
        return None
    order.status = status_data.status
    await db.flush()
    #await db.refresh(order) #Triggers lazy load when querying
    return await get_order(db, order.id)
