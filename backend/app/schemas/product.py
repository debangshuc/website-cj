from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product display name")
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit")
    category_id: Optional[str] = Field(default=None, description="Category UUID identifier")
    category: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Product category display name")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Current selling price in INR")
    stock: int = Field(default=0, ge=0, description="Available stock quantity")
    image_path: Optional[str] = Field(default=None, description="Relative path or asset identifier for product image")
    description: Optional[str] = Field(default=None, description="Optional product description")
    is_active: bool = Field(default=True, description="Soft deletion indicator")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    sku: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category_id: Optional[str] = Field(default=None, description="Category UUID identifier")
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    stock: Optional[int] = Field(default=None, ge=0)
    image_path: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: str = Field(..., description="Unique product ID")
    category_id: Optional[str] = Field(default=None, description="Category UUID identifier")
    category: str = Field(..., description="Category display name")
    units_sold: int = Field(default=0, ge=0, description="Lifetime physical units sold")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")

    model_config = ConfigDict(from_attributes=True)
