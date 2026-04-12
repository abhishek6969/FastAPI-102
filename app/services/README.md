# Service Layer: Business Engine 🛠️🏭

This directory implements the **Service Layer Pattern**. By separating business logic from the routers (endpoints), we ensure that our API is easier to test, maintain, and reuse.

## ⚖️ Fat Service / Thin Router
In **FastAPI-102**, our routers are just "Traffic Controllers." They:
1. Receive the request.
2. Authenticate the user (via dependencies).
3. Call the appropriate Service.
4. Return the result.

The **Service** does the heavy lifting: checking stock, calculating subtotals, and hashing passwords.

## 🛒 Price Snapshotting (`order_service.py`)
One of the most critical patterns in this project is **Historical Integrity**:
- When a user places an order, we don't just link to the `Product`. 
- We **Snapshot** the `unit_price` at the moment of the sale into the `OrderItem` table.
- **Why?** If the price of a laptop changes from $900 to $1000 tomorrow, the user's receipt from yesterday must still show $900.

## 🔄 Transaction Safety: `flush()` vs `commit()`
You'll notice that our services use `await db.flush()` but almost never `await db.commit()`.
- **`flush()`**: Sends the SQL to the database but doesn't "finalize" it. This lets us get the server-generated `id` or `created_at` timestamp.
- **Handover**: The actual `commit()` happens in the **Router** or via the **Dependency (get_db)**. If a service operation fails halfway through, the whole transaction is safely rolled back.
