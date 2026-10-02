"""Schemas package"""
from app.schemas.product import ProductBase, ProductCreate, ProductUpdate, ProductResponse
from app.schemas.sale import SaleCreate, SaleResponse, DashboardSummaryResponse

__all__ = [
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "SaleCreate",
    "SaleResponse",
    "DashboardSummaryResponse",
]
