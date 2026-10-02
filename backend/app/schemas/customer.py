import re
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Customer full display name")
    email: Optional[str] = Field(default=None, max_length=150, description="Contact email address")
    phone: Optional[str] = Field(default=None, max_length=50, description="Contact phone number")
    address: Optional[str] = Field(default=None, max_length=300, description="Shipping or billing address")
    notes: Optional[str] = Field(default=None, max_length=500, description="Administrative CRM notes")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Customer name cannot be empty or whitespace only")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().lower()
        if not clean:
            return None
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email format")
        return clean

    @field_validator("phone", "address", "notes")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        return clean if clean else None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    email: Optional[str] = Field(default=None, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=300)
    notes: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None, description="Soft-delete status indicator")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        if not clean:
            raise ValueError("Customer name cannot be empty or whitespace only")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().lower()
        if not clean:
            return None
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email format")
        return clean

    @field_validator("phone", "address", "notes")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        return clean if clean else None


class CustomerOrderSummary(BaseModel):
    id: str = Field(..., description="Unique Order UUID")
    order_number: str = Field(..., description="Human-readable Order number")
    status: str = Field(..., description="Order lifecycle status")
    total: Decimal = Field(..., description="Order total amount")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class CustomerResponse(BaseModel):
    id: str = Field(..., description="Unique customer UUID")
    name: str = Field(..., description="Customer full name")
    email: Optional[str] = Field(default=None, description="Normalized email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    address: Optional[str] = Field(default=None, description="Address")
    notes: Optional[str] = Field(default=None, description="CRM notes")
    is_active: bool = Field(default=True, description="Soft-delete status")
    order_count: int = Field(default=0, description="Total non-cancelled orders count")
    completed_order_count: int = Field(default=0, description="Completed orders count")
    total_spent: Decimal = Field(default=Decimal("0.00"), description="Authoritative total revenue accumulated from completed orders")
    last_order_at: Optional[str] = Field(default=None, description="ISO timestamp of most recent order")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class CustomerDetailResponse(CustomerResponse):
    recent_orders: List[CustomerOrderSummary] = Field(default_factory=list, description="Recent orders associated with this customer")

    model_config = ConfigDict(from_attributes=True)


class CustomerMetricsResponse(BaseModel):
    total_customers: int = Field(default=0, description="Total count of all customers")
    active_customers: int = Field(default=0, description="Count of active customers")
    customers_with_orders: int = Field(default=0, description="Count of customers with at least one order")
    total_revenue: Decimal = Field(default=Decimal("0.00"), description="Total revenue generated across all completed customer orders")

    model_config = ConfigDict(from_attributes=True)
