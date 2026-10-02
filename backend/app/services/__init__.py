"""Services package"""
from app.services.product_service import ProductService, product_service
from app.services.sales_service import SalesService, sales_service
from app.services.dashboard_service import DashboardService, dashboard_service

__all__ = [
    "ProductService",
    "product_service",
    "SalesService",
    "sales_service",
    "DashboardService",
    "dashboard_service",
]
