from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class OrderItemCreate(BaseModel):
    product_id: str = Field(..., description="Product UUID identifier")
    quantity: int = Field(..., gt=0, description="Quantity of physical units (must be > 0)")


class OrderItemResponse(BaseModel):
    id: str = Field(..., description="Unique OrderItem ID")
    product_id: str = Field(..., description="Product UUID identifier")
    product_name: str = Field(..., description="Product display title")
    sku: str = Field(..., description="Stock Keeping Unit")
    category: str = Field(..., description="Product category name")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    unit_price: Decimal = Field(..., ge=0, decimal_places=2, description="Authoritative unit price at order creation")
    line_total: Decimal = Field(..., ge=0, decimal_places=2, description="Calculated line total (quantity * unit_price)")

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    customer_id: Optional[str] = Field(default=None, description="Optional Customer UUID identifier")
    customer_name: Optional[str] = Field(default=None, max_length=150, description="Optional customer display name (snapshot)")
    customer_email: Optional[str] = Field(default=None, max_length=150, description="Optional customer contact email (snapshot)")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="List of order line items")
    notes: Optional[str] = Field(default=None, max_length=500, description="Optional administrative or customer notes")


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., description="Target order state: pending, confirmed, completed, cancelled")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ["pending", "confirmed", "completed", "cancelled"]:
            raise ValueError("Status must be one of: pending, confirmed, completed, cancelled")
        return clean


class OrderResponse(BaseModel):
    id: str = Field(..., description="Unique order UUID")
    order_number: str = Field(..., description="Human-facing unique order number (e.g. ORD-20260901-A1B2)")
    customer_id: Optional[str] = Field(default=None, description="Linked Customer UUID")
    status: str = Field(..., description="Order lifecycle state: pending, confirmed, completed, cancelled")
    customer_name: Optional[str] = Field(default=None, description="Customer name (snapshot)")
    customer_email: Optional[str] = Field(default=None, description="Customer email (snapshot)")
    subtotal: Decimal = Field(..., description="Sum of item line totals")
    total: Decimal = Field(..., description="Total order amount")
    notes: Optional[str] = Field(default=None, description="Order notes")
    items: List[OrderItemResponse] = Field(default_factory=list, description="Order line items")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class OrderMetricsResponse(BaseModel):
    total_orders: int = Field(default=0, description="Total count of all orders")
    pending_orders: int = Field(default=0, description="Count of orders in pending status")
    confirmed_orders: int = Field(default=0, description="Count of orders in confirmed status")
    completed_orders: int = Field(default=0, description="Count of orders in completed status")
    cancelled_orders: int = Field(default=0, description="Count of orders in cancelled status")
    total_revenue: Decimal = Field(default=Decimal("0.00"), description="Total revenue from completed orders")

    model_config = ConfigDict(from_attributes=True)
