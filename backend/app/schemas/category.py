from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category display name")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional detailed category description")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Category name cannot be empty or only whitespace.")
        return trimmed


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Updated category name")
    description: Optional[str] = Field(default=None, max_length=500, description="Updated category description")
    is_active: Optional[bool] = Field(default=None, description="Active status indicator")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Category name cannot be empty or only whitespace.")
            return trimmed
        return v


class CategoryResponse(BaseModel):
    id: str = Field(..., description="Unique category identifier (UUID)")
    name: str = Field(..., description="Category display name")
    description: Optional[str] = Field(default=None, description="Optional category description")
    is_active: bool = Field(default=True, description="Whether the category is active")
    product_count: Optional[int] = Field(default=0, description="Number of products assigned to this category")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")

    model_config = ConfigDict(from_attributes=True)
