from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Settings loads values from environment variables (or .env file).

    HOW IT WORKS UNDER THE HOOD:
    1. pydantic-settings reads os.environ at import time.
    2. Each field name (e.g., "database_url") is matched CASE-INSENSITIVELY
       to environment variables (e.g., "DATABASE_URL").
    3. Type hints act as validators — if DATABASE_URL is missing and there's
       no default, Pydantic raises ValidationError at startup. Fail FAST.
    4. model_config uses .env file as a fallback source.
    """

    # --- Database (LEGO System) ---
    # We use separate fields instead of one string to prevent 
    # passwords with special characters (like @ or $) from breaking the URL.
    database_url: str | None = None
    database_driver: str = "postgresql+asyncpg"
    database_hostname: str | None = None
    database_username: str | None = None
    database_password: str | None = None
    database_port: str = "5432"
    database_name: str | None = None
    access_token_expire_minutes: int = 30

    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_db: str | None = None
    
    # --- Application ---
    app_name: str 
    debug: bool 
    secret_key: str 
    algorithm: str = "HS256"

    # --- Admin Seed ---
    admin_email: str
    admin_username: str
    admin_password: str
    
    model_config = {
        "env_file": ".env",       # Read from .env file as fallback
        "env_file_encoding": "utf-8",
        "case_sensitive": False,  # DATABASE_URL matches database_url
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton pattern via lru_cache.

    WHY lru_cache?
    Without it, every request that calls get_settings() would:
    1. Re-read the .env file from disk (I/O operation)
    2. Re-parse and validate all fields
    3. Create a new Settings object in memory

    lru_cache stores the FIRST result in a dictionary keyed by arguments.
    Since get_settings() takes no arguments, it returns the same object forever.
    One object, one I/O read, for the lifetime of the process.

    YOUR TASK: Can you think of when this cache would be a PROBLEM?
    Hint: What happens if you change .env while the app is running?
    """
    return Settings()
