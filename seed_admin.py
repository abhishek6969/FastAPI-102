import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from app.models.user import User, UserRole
from app.core.config import get_settings
from app.core.database import get_connection_string

settings = get_settings()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def seed_admin():
    # 1. Connect to DB
    engine = create_async_engine(get_connection_string())
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 2. Create the admin user from settings. 
        # IMPORTANT: These ADMIN_ vars MUST be set in your Azure App Service 
        # Environment Variables for this to work in production!
        admin_user = User(
            email=settings.admin_email,
            username=settings.admin_username,
            hashed_password=pwd_context.hash(settings.admin_password),
            is_active=True,
            role=UserRole.admin
        )
        
        try:
            session.add(admin_user)
            await session.commit()
            print("✅ Admin user created")
        except Exception as e:
            print(f"❌ Error: {e}. Maybe the user already exists?")

if __name__ == "__main__":
    asyncio.run(seed_admin())
