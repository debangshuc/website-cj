from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.product import ProductResponse


class SaleCreate(BaseModel):
    product_id: str = Field(..., description="ID of the product sold")
    quantity: int = Field(..., gt=0, description="Number of units sold (must be > 0)")
    unit_price: Decimal = Field(..., ge=0, decimal_places=2, description="Historical transaction unit price")
    order_id: Optional[str] = Field(default=None, description="Optional linked Order UUID")
    order_item_id: Optional[str] = Field(default=None, description="Optional linked OrderItem UUID")
    sold_at: Optional[str] = Field(default=None, description="Optional ISO timestamp; defaults to current time")


class SaleResponse(BaseModel):
    id: str = Field(..., description="Unique transaction ID")
    product_id: str = Field(..., description="ID of the product sold")
    product_name: str = Field(..., description="Product name at transaction time")
    category: str = Field(..., description="Product category")
    quantity: int = Field(..., description="Quantity of physical units sold")
    unit_price: Decimal = Field(..., description="Historical unit price")
    total: Decimal = Field(..., description="Calculated total (quantity * unit_price)")
    order_id: Optional[str] = Field(default=None, description="Optional linked Order UUID")
    order_item_id: Optional[str] = Field(default=None, description="Optional linked OrderItem UUID")
    sold_at: str = Field(..., description="ISO 8601 transaction timestamp")

    model_config = ConfigDict(from_attributes=True)


class BestSellerResponse(BaseModel):
    id: str = Field(..., description="Unique product ID")
    name: str = Field(..., description="Product display name")
    sku: str = Field(..., description="Stock Keeping Unit")
    category: str = Field(..., description="Product category")
    price: Decimal = Field(..., description="Current product selling price")
    stock: int = Field(..., description="Current stock quantity")
    units_sold: int = Field(default=0, description="Lifetime physical units sold")
    revenue: Decimal = Field(default=Decimal("0.00"), description="Authoritative total revenue accumulated from historical sales of this product")
    image_path: Optional[str] = Field(default=None, description="Image path or asset identifier")
    description: Optional[str] = Field(default=None, description="Optional product description")
    is_active: bool = Field(default=True, description="Soft deletion indicator")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class DailyRevenuePoint(BaseModel):
    date: str = Field(..., description="Calendar date formatted as YYYY-MM-DD")
    day: str = Field(..., description="Display label (e.g. 'Mon', '18 Aug')")
    revenue: Decimal = Field(..., description="Authoritative revenue sum for this date")
    order_count: int = Field(default=0, description="Count of sales transactions on this date")

    model_config = ConfigDict(from_attributes=True)


class RevenueAnalyticsResponse(BaseModel):
    period: str = Field(..., description="Analytics interval: 'today', 'week', 'month'")
    total_revenue: Decimal = Field(..., description="Total gross revenue for the selected period")
    previous_period_revenue: Decimal = Field(default=Decimal("0.00"), description="Total revenue for preceding comparison period")
    points: List[DailyRevenuePoint] = Field(default_factory=list, description="Ordered chronological daily revenue points")

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryResponse(BaseModel):
    total_products: int = Field(..., description="Total count of active products")
    total_stock: int = Field(..., description="Total sum of units across active products")
    today_revenue: Decimal = Field(..., description="Gross revenue from sales recorded today")
    today_sales: int = Field(..., description="Total completed sales transactions today")
    units_sold_today: int = Field(..., description="Total physical units sold today")
    best_selling_product: Optional[BestSellerResponse] = Field(default=None, description="Product with highest units sold and historical revenue")
    recent_sales: List[SaleResponse] = Field(default_factory=list, description="5 most recent sales transactions")
    low_stock_products: List[ProductResponse] = Field(default_factory=list, description="Active products with stock <= 8")
    revenue_overview: Optional[RevenueAnalyticsResponse] = Field(default=None, description="Time-series revenue analytics for the overview chart")

    model_config = ConfigDict(from_attributes=True)
