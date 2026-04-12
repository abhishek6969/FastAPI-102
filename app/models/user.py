import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import enum
from sqlalchemy import Enum  # Add to your existing sqlalchemy imports

# inherit from str so the database can store it as a simple string
class UserRole(str, enum.Enum):
    customer = "customer"
    seller = "seller"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    # __tablename__ tells SQLAlchemy what the actual PostgreSQL table
    # should be called. Without it, SQLAlchemy raises an error.

    # TODO 1: Primary Key
    # Use uuid as the primary key (not auto-increment integers).
    # WHY UUIDs? In a distributed system, two servers generating
    # auto-increment IDs would collide. UUIDs are globally unique.
    # Use: Mapped[uuid.UUID] with mapped_column() and default=uuid.uuid4
    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4,primary_key=True)

    # TODO 2: Core fields
    # email: String(255), unique=True, index=True, nullable=False
    #   WHY index? Without an index, looking up a user by email scans
    #   ALL rows (O(n)). An index creates a B-tree → O(log n) lookups.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # username: String(50), unique=True, index=True, nullable=False
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # We use Argon2 for hashing (via passlib). 
    # Important: Never compare plain passwords; only use pwd_context.verify().
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # TODO 3: Account status
    # is_active: Boolean, default=True, server_default="true"
    #   server_default means PostgreSQL itself sets the default,
    #   even if you INSERT via raw SQL outside of SQLAlchemy.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # TODO 4: Timestamps
    # created_at: DateTime(timezone=True), server_default=func.now()
    #   func.now() translates to PostgreSQL's NOW() function.
    # updated_at: DateTime(timezone=True), onupdate=func.now()
    #   onupdate= automatically refreshes this field on every UPDATE.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    # By default, everyone is a "customer". 
    # Promotion to Seller or Admin is done manually via seed/DB access.
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.customer, server_default="customer", nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
