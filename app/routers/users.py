from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user , require_role
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse , UserUpdate
from app.services import user_service
from app.models.user import User , UserRole

# APIRouter is a "mini-app" — it groups related endpoints.
# prefix="/users" means all routes here start with /users.
# tags=["Users"] groups them in the Swagger docs UI.
router = APIRouter(prefix="/users", tags=["Users"])


# TODO 1: POST /users — Create a new user
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,                    # ← Request body (Pydantic validates this)
    db: AsyncSession = Depends(get_db),       # ← Dependency injection
):
    # Check if email already exists
    existing_email = await user_service.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    existing_username = await user_service.get_user_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )
    # WHY 409 CONFLICT? HTTP semantics:
    #   400 = bad request format
    #   409 = request is valid BUT conflicts with current state
    #   422 = request format is fine but values are invalid (Pydantic uses this)

    return await user_service.create_user(db, user_data)
    # FastAPI sees response_model=UserResponse.
    # It calls UserResponse.model_validate(db_user) automatically.
    # This strips hashed_password and only returns safe fields.


# TODO 2: GET /users — List all users (paginated)
@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    # require_role(UserRole.admin): Our "Bouncer" dependency. 
    # It checks the user's role BEFORE this function even starts.
    current_user : User = Depends(require_role(UserRole.admin))
):
    return await user_service.get_users(db, skip=skip, limit=limit)


# TODO 3: GET /users/{user_id} — Get single user
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,                            # ← Path parameter from URL
    db: AsyncSession = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="User is deactivated",
        )
    return user


# TODO 4: PATCH /users/{user_id} — Partial update
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,                    # ← Import UserUpdate in your imports!
    db: AsyncSession = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    # Call user_service.update_user()
    # If it returns None → raise 404
    # Otherwise return the updated user
    try:
        user = await user_service.update_user(db, user_id, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# TODO 5: DELETE /users/{user_id} — Soft delete
@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user : User = Depends(require_role(UserRole.admin))
):
    # Call user_service.delete_user()
    # If it returns None → raise 404
    # Return a confirmation message
    user = await user_service.delete_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"detail": "User deactivated", "user_id": str(user_id)}

