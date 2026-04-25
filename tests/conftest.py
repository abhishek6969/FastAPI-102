# conftest.py
import sys
import asyncio
import pytest_asyncio
from types import SimpleNamespace
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import URL
from app.main import app
from app.core.database import Base, get_db
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models import user, product, order
from app.models.user import UserRole 
from app.services import user_service
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

settings = get_settings()

TEST_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.database_username,
    password=settings.database_password,
    host=settings.database_hostname,
    port=int(settings.database_port),
    database=settings.database_name,
)

async def promote_to_admin(db_session, user_id: str):
    user = await user_service.get_user(db_session, user_id)
    user.role = UserRole.admin
    await db_session.flush()
    await db_session.refresh(user)

# Session-scoped engine with NullPool.
# NullPool = no connection caching, so every request gets a fresh
# connection on the current running loop. This is the correct approach
# for async tests — the rollback pattern doesn't work reliably with
# asyncpg because the app and fixture share the same connection object,
# causing "another operation is in progress" conflicts.
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():
    _engine = create_async_engine(TEST_URL, echo=False, poolclass=NullPool)

    print("\n⚙️  [engine] Creating tables...")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ [engine] Tables ready.")

    yield _engine

    await _engine.dispose()
    print("🔌 [engine] Engine disposed.")


# Function-scoped session — each test gets a clean session.
# Isolation comes from drop/create at session start (all tests
# see the same schema) and tests should not depend on each
# other's data. If you need row-level isolation, truncate tables
# in a teardown fixture instead of relying on rollback.
@pytest_asyncio.fixture()
async def db_session(engine):
    async_session = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        print("\n🗄️  [db_session] Session opened.")
        yield session
    print("🔒 [db_session] Session closed.")


@pytest_asyncio.fixture()
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    print("🌐 [client] AsyncClient started.")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    print("🧹 [client] Dependency overrides cleared.")


@pytest_asyncio.fixture()
async def create_test_user(client):
    user_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "Testpass@123",
    }
    response = await client.post("/users/", json=user_data)
    print(f"👤 [create_test_user] Status: {response.status_code} | User: {user_data['email']}")
    assert response.status_code == 201

    result = SimpleNamespace(**response.json())
    result.password = user_data["password"]
    return result


@pytest_asyncio.fixture()
async def token(create_test_user):
    return create_access_token(
        user_id=create_test_user.id,
        email=create_test_user.email
    )


@pytest_asyncio.fixture()
async def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    print("🔑 [authorized_client] Bearer token injected.")
    return client


@pytest_asyncio.fixture()
async def admin_token(client, db_session):
    import uuid as _uuid
    
    # Create a SECOND, SEPARATE user specifically for admin operations.
    # Never the same as create_test_user — that user stays customer forever.
    admin_data = {
        "email": "admin_fixture@test.com",
        "username": "admin_fixture_user",
        "password": "AdminFixture@123",
    }
    response = await client.post("/users/", json=admin_data)
    assert response.status_code == 201
    admin_user = SimpleNamespace(**response.json())

    # Promote THIS second user to admin (not create_test_user)
    await promote_to_admin(db_session, admin_user.id)

    # Generate a token for the admin user
    admin_token = create_access_token(
        user_id=admin_user.id,
        email=admin_user.email
    )
    return admin_token

@pytest_asyncio.fixture()
async def create_test_product(client, admin_token):
    product_data = {
        "name": "Test Widget",
        "description": "A widget for testing",
        "price": 9.99,
        "stock": 100,
        "category": "Electronics",
    }
    response = await client.post(
        "/products/",
        json=product_data,
        headers={"Authorization": f"Bearer {admin_token}"},  # per-request
    )
    print("create_test_product response: ", response.json())
    assert response.status_code == 201
    return SimpleNamespace(**response.json())
