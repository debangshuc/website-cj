"""API router package"""
from fastapi import APIRouter
from app.api.categories import router as categories_router
from app.api.products import router as products_router
from app.api.sales import router as sales_router
from app.api.orders import router as orders_router
from app.api.customers import router as customers_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(categories_router, prefix="/categories", tags=["Categories"])
api_router.include_router(products_router, prefix="/products", tags=["Products"])
api_router.include_router(sales_router, prefix="/sales", tags=["Sales"])
api_router.include_router(orders_router, prefix="/orders", tags=["Orders"])
api_router.include_router(customers_router, prefix="/customers", tags=["Customers"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

__all__ = ["api_router"]
