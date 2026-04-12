import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    # gt=0 means "Greater Than 0". 
    # This prevents anyone from listing a product with a negative price!
    price: float = Field(..., gt=0)
    # ge=0 means "Greater than or Equal to 0".
    stock: int = Field(..., ge=0)
    category: str = Field(..., min_length=1, max_length=100)


    


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    category: str | None = Field(default=None, min_length=1, max_length=100)


class ProductResponse(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None
    model_config = ConfigDict(from_attributes=True)
    is_active: bool