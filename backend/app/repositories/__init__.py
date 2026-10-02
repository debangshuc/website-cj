"""Repositories package"""
from app.repositories.product_repository import (
    ProductRepositoryProtocol,
    InMemoryProductRepository,
    product_repository,
)
from app.repositories.sales_repository import (
    SalesRepositoryProtocol,
    InMemorySalesRepository,
    sales_repository,
)
from app.repositories.postgres_product_repository import PostgresProductRepository
from app.repositories.postgres_sales_repository import PostgresSalesRepository

__all__ = [
    "ProductRepositoryProtocol",
    "InMemoryProductRepository",
    "product_repository",
    "SalesRepositoryProtocol",
    "InMemorySalesRepository",
    "sales_repository",
    "PostgresProductRepository",
    "PostgresSalesRepository",
]
