from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import jwt, JWTError
from app.core.config import get_settings

settings = get_settings()

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(user_id: UUID, email: str) -> str:
    """Print the wristband — encode user info into a signed token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        # "sub" (subject) is the unique identifier for the user. 
        # We store the UUID as a string so the client can't guess IDs.
        "sub": str(user_id),
        "email": email,
        "exp": expire,           # 'jose' auto-rejects expired tokens during decode
    }
    # Algorithm and Secret Key are synced with your Terraform/Deployment vars
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> dict | None:
    """Check the wristband — decode and verify signature + expiration."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
