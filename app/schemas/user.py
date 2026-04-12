import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field


# TODO 1: UserBase — shared fields (DRY principle)
# Contains fields common to BOTH creation and response.
# Fields: email (EmailStr), username (str, min 3, max 50)
#
# WHY EmailStr? It uses a regex validator that checks for
# proper email format. "abc" would fail, "abc@x.com" passes.
# NOTE: You'll need to `pip install email-validator` — add it
# to requirements.txt!
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


# TODO 2: UserCreate — what the API RECEIVES on POST /users
# Inherits from UserBase (gets email + username for free).
# Adds: password (str, min 8 chars)
# This is the ONLY schema that ever contains a plaintext password.
class UserCreate(UserBase):
    password: str = Field(min_length=8)


# TODO 3: UserResponse — what the API SENDS BACK
# Inherits from UserBase (gets email + username).
# Adds: id (uuid), is_active (bool), created_at (datetime)
# NEVER includes password or hashed_password.
#
# model_config with from_attributes=True is the "Special Bridge". 
# By default, Pydantic only understands dictionaries (e.g. user_dict["email"]).
# This flag tells Pydantic: "It's okay to use dot notation (e.g. user_obj.email)
# to read from a SQLAlchemy class object."
class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    role: str
    model_config = ConfigDict(from_attributes=True)


# TODO 4: UserUpdate — PATCH /users/{id} (partial updates)
# ALL fields are Optional (None = "don't change this field")
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(min_length=3, max_length=50 , default = None) 
    password: str | None = Field(min_length=8 , default = None) 
