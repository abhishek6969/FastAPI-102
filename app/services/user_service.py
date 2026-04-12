from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

# Password hashing context
# WHY CryptContext? It's a "multi-hasher" wrapper.
# We use Argon2 (the current industry favorite) for all NEW hashes.
# deprecated="auto" ensures that if we ever switch from Argon2 to something 
# else, passlib will automatically handle old Argon2 hashes correctly.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# TODO 1: Create user
async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    # Step 1: Hash the plaintext password
    # pwd_context.hash() runs bcrypt with a random salt.
    # The result looks like: $2b$12$LJ3m4ys... (~60 chars)
    #   $2b = bcrypt version
    #   $12 = cost factor (2^12 = 4096 iterations)
    #   rest = salt + hash concatenated
    hashed_password = pwd_context.hash(user_data.password)

    # Step 2: Create the SQLAlchemy model instance
    # Note: We use user_data.model_dump() to convert Pydantic → dict,
    # then exclude "password" (we don't store plaintext).
    # Then we add hashed_password separately.
    db_user = User(
        **user_data.model_dump(exclude={"password"}),
        hashed_password=hashed_password,
    )

    # Step 3: Add to session and flush
    # add() → stages the INSERT in the session's "identity map"
    # flush() → sends the SQL to PostgreSQL BUT doesn't commit yet.
    # The actual "Commit" happens in our get_db dependency in the router.
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user


# TODO 2: Get user by ID
async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    # select() builds a SQL SELECT statement.
    # .where() adds a WHERE clause.
    # await db.execute() sends it to PostgreSQL via asyncpg.
    # .scalar_one_or_none() returns the object or None.
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# TODO 3: Get user by email (for login later)
async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


# TODO 4: Get all users (paginated)
# WHY pagination? Without it, SELECT * on a table with 1M users
# loads ALL rows into memory → OOM crash.
# offset = skip N rows, limit = take N rows.
async def get_users(db: AsyncSession, skip: int = 0, limit: int = 10) -> list[User]:
    result = await db.execute(select(User).where(User.is_active == True).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

# TODO 5: Update user (partial)
async def update_user(db: AsyncSession, user_id: UUID, user_data: UserUpdate) -> User | None:
    # Step 1: Fetch the existing user
    db_user = await get_user(db, user_id)
    if not db_user:
        return None

    if not db_user.is_active:
        raise ValueError("Cannot update a deactivated User.")

    # Step 2: Get only the fields that were ACTUALLY sent
    # model_dump(exclude_unset=True) is the key here.
    # If client sent {"email": "new@x.com"}, this returns {"email": "new@x.com"}
    # Username and password are NOT in the dict — they won't be touched.
    update_data = user_data.model_dump(exclude_unset=True)

    # Step 3: Handle password separately (needs hashing)
    if "password" in update_data:
        update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))
        # .pop() removes "password" from dict AND returns its value.
        # We replace it with "hashed_password" — the actual DB column.

    # Step 4: Apply updates to the model
    # setattr(object, name, value) is Python's way to set
    # an attribute by name dynamically.
    # It's equivalent to: db_user.email = "new@x.com"
    # But works when the attribute name is a variable.
    for field, value in update_data.items():
        setattr(db_user, field, value)

    await db.flush()
    await db.refresh(db_user)
    return db_user


# TODO 6: Soft delete user
async def delete_user(db: AsyncSession, user_id: UUID) -> User | None:
    db_user = await get_user(db, user_id)
    if not db_user:
        return None

    # Soft delete: We deactivate the user instead of deleting the row.
    # Why? To maintain data integrity (orders/logs) while preventing login.
    db_user.is_active = False
    await db.flush()
    await db.refresh(db_user)
    return db_user
