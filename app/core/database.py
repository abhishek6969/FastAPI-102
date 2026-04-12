from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

from sqlalchemy.engine import URL

settings = get_settings()

def get_connection_string() -> str:
    """
    Constructs the database connection string.
    Priority:
    1. Individual components (Hostname, Password, etc.) via URL.create
       - Why? URL.create handles special characters (like @) in passwords safely.
    2. Fallback to settings.database_url
    """
    if settings.database_hostname:
        # SQLAlchemy async requires "postgresql+asyncpg". 
        # We add it here so our Terraform variables can stay simple ("postgresql").
        driver = settings.database_driver
        if "asyncpg" not in driver:
            driver = f"{driver}+asyncpg"
            
        return URL.create(
            drivername=driver,
            username=settings.database_username,
            password=settings.database_password,
            host=settings.database_hostname,
            port=int(settings.database_port),
            database=settings.database_name,
        ).render_as_string(hide_password=False)
    
    if not settings.database_url:
        raise ValueError("DATABASE_URL or separate database components must be provided.")
        
    return settings.database_url

# Create the async engine
engine = create_async_engine(
    get_connection_string(), 
    echo=settings.debug, 
    pool_size=5, 
    max_overflow=10
)

# TODO 2: Create the session factory
# Use async_sessionmaker() with:
#   - bind=engine           (which engine to use)
#   - class_=AsyncSession   (produce async sessions, not sync)
#   - expire_on_commit=False (objects stay usable after commit)
#
# WHY expire_on_commit=False?
# By default, SQLAlchemy "expires" all attributes after commit.
# The next access triggers a lazy-load SQL query.
# In async mode, lazy-loading is ILLEGAL (it would block the event loop).
# So we disable it and load everything explicitly.
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# TODO 3: Create the Base class
# All your models will inherit from this.
# Under the hood, DeclarativeBase uses a metaclass that:
# 1. Collects all Column() definitions from your class
# 2. Builds a Table object in SQLAlchemy's MetaData registry
# 3. Creates a mapper linking Python attributes → DB columns
class Base(DeclarativeBase):
    pass

# TODO 4: Create a dependency function for FastAPI
# This is a Python GENERATOR (uses yield, not return).
# FastAPI's dependency injection calls __anext__() to get the session,
# then __anext__() again after your route finishes → runs the finally block.
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
