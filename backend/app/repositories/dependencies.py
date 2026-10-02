from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.repositories.product_repository import ProductRepositoryProtocol, product_repository
from app.repositories.sales_repository import SalesRepositoryProtocol, sales_repository
from app.repositories.postgres_product_repository import PostgresProductRepository
from app.repositories.postgres_sales_repository import PostgresSalesRepository
from app.services.product_service import ProductService
from app.services.sales_service import SalesService
from app.services.dashboard_service import DashboardService


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepositoryProtocol:
    return PostgresProductRepository(db)


def get_sales_repository(db: Session = Depends(get_db)) -> SalesRepositoryProtocol:
    return PostgresSalesRepository(db)


def get_product_service(
    repo: ProductRepositoryProtocol = Depends(get_product_repository),
) -> ProductService:
    return ProductService(repo=repo)


def get_sales_service(
    sales_repo: SalesRepositoryProtocol = Depends(get_sales_repository),
    product_repo: ProductRepositoryProtocol = Depends(get_product_repository),
) -> SalesService:
    return SalesService(sales_repo=sales_repo, product_repo=product_repo)


def get_dashboard_service(
    product_repo: ProductRepositoryProtocol = Depends(get_product_repository),
    sales_repo: SalesRepositoryProtocol = Depends(get_sales_repository),
) -> DashboardService:
    return DashboardService(product_repo=product_repo, sales_repo=sales_repo)
