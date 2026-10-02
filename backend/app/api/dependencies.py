from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import AuthenticatedUser, verify_supabase_jwt
from app.repositories.category_repository import CategoryRepositoryProtocol
from app.repositories.product_repository import ProductRepositoryProtocol
from app.repositories.sales_repository import SalesRepositoryProtocol
from app.repositories.order_repository import OrderRepositoryProtocol
from app.repositories.customer_repository import CustomerRepositoryProtocol
from app.repositories.postgres_category_repository import PostgresCategoryRepository
from app.repositories.postgres_product_repository import PostgresProductRepository
from app.repositories.postgres_sales_repository import PostgresSalesRepository
from app.repositories.postgres_order_repository import PostgresOrderRepository
from app.repositories.postgres_customer_repository import PostgresCustomerRepository
from app.services.category_service import CategoryService
from app.services.product_service import ProductService
from app.services.sales_service import SalesService
from app.services.order_service import OrderService
from app.services.customer_service import CustomerService
from app.services.dashboard_service import DashboardService
from app.services.storage_service import StorageServiceProtocol, storage_service

http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> AuthenticatedUser:
    """
    FastAPI dependency to extract and authenticate the Supabase Bearer token.
    Raises 401 Unauthorized if missing, malformed, or expired.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Bearer scheme required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_supabase_jwt(credentials.credentials)


def require_admin(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """
    FastAPI dependency to enforce administrator authorization.
    Verifies that the authenticated user possesses administrator privileges.
    Raises 403 Forbidden if the user is authenticated but not an administrator.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrator access required to perform this action.",
        )
    return current_user


def get_category_repository(db: Session = Depends(get_db)) -> CategoryRepositoryProtocol:
    return PostgresCategoryRepository(db)


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepositoryProtocol:
    return PostgresProductRepository(db)


def get_sales_repository(db: Session = Depends(get_db)) -> SalesRepositoryProtocol:
    return PostgresSalesRepository(db)


def get_order_repository(db: Session = Depends(get_db)) -> OrderRepositoryProtocol:
    return PostgresOrderRepository(db)


def get_customer_repository(db: Session = Depends(get_db)) -> CustomerRepositoryProtocol:
    return PostgresCustomerRepository(db)


def get_storage_service() -> StorageServiceProtocol:
    return storage_service


def get_category_service(
    repo: CategoryRepositoryProtocol = Depends(get_category_repository),
) -> CategoryService:
    return CategoryService(repo=repo)


def get_product_service(
    repo: ProductRepositoryProtocol = Depends(get_product_repository),
    category_repo: CategoryRepositoryProtocol = Depends(get_category_repository),
) -> ProductService:
    return ProductService(repo=repo, category_repo=category_repo)


def get_sales_service(
    sales_repo: SalesRepositoryProtocol = Depends(get_sales_repository),
    product_repo: ProductRepositoryProtocol = Depends(get_product_repository),
) -> SalesService:
    return SalesService(sales_repo=sales_repo, product_repo=product_repo)


def get_order_service(
    order_repo: OrderRepositoryProtocol = Depends(get_order_repository),
    product_repo: ProductRepositoryProtocol = Depends(get_product_repository),
    sales_repo: SalesRepositoryProtocol = Depends(get_sales_repository),
    customer_repo: CustomerRepositoryProtocol = Depends(get_customer_repository),
) -> OrderService:
    return OrderService(
        order_repo=order_repo,
        product_repo=product_repo,
        sales_repo=sales_repo,
        customer_repo=customer_repo,
    )


def get_customer_service(
    repo: CustomerRepositoryProtocol = Depends(get_customer_repository),
) -> CustomerService:
    return CustomerService(repo=repo)


def get_dashboard_service(
    product_repo: ProductRepositoryProtocol = Depends(get_product_repository),
    sales_repo: SalesRepositoryProtocol = Depends(get_sales_repository),
) -> DashboardService:
    return DashboardService(product_repo=product_repo, sales_repo=sales_repo)
