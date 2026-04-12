# Database Evolutions: Alembic Migrations 🏗️📜

Alembic tracks every change to your database schema like a version control system (Git) for your tables.

## 🚀 The Migration Timeline
Each file in `versions/` represents a specific moment in the project's history:
1. **Initial Setup**: Creation of the `users` table with UUIDs.
2. **Catalog Expansion**: Creation of the `products` table.
3. **Core Business**: Implementation of `orders` and `order_items`.
4. **Identity & Access**: Addition of the `role` column for RBAC.

## 🛠️ The PostgreSQL "Enum Fix"
PostgreSQL handles `Enum` types differently than other databases like SQLite. In **FastAPI-102**, we encountered a common hurdle: Alembic's auto-generator doesn't always handle the creation of the underlying Postgres Enum type correctly.

We implemented a **Manual Handshake** in the migration script:
```python
# Create the custom PostgreSQL enum type FIRST before adding the column
user_role = sa.Enum('customer', 'seller', 'admin', name='userrole')
user_role.create(op.get_bind())

# Now add the column using that newly created type
op.add_column('users', sa.Column('role', sa.Enum(..., name='userrole')))
```
Checking the `upgrade()` and `downgrade()` functions in your versions folder will show you this pattern in action.

## 🏁 How to Sync
- **Upgrade**: `alembic upgrade head` (Brings the DB to the latest version).
- **History**: `alembic history` (Shows the timeline of changes).
