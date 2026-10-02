import pytest
from app.main import app
from app.api.dependencies import (
    get_current_user,
    require_admin,
    get_category_repository,
    get_product_repository,
    get_sales_repository,
    get_order_repository,
    get_customer_repository,
    get_storage_service,
)
from app.core.security import AuthenticatedUser
from app.repositories.category_repository import InMemoryCategoryRepository
from app.repositories.product_repository import InMemoryProductRepository
from app.repositories.sales_repository import InMemorySalesRepository
from app.repositories.order_repository import InMemoryOrderRepository
from app.repositories.customer_repository import InMemoryCustomerRepository
from app.services.storage_service import InMemoryStorageService


@pytest.fixture(autouse=True)
def override_repositories_for_unit_tests():
    """
    Ensure all standard unit tests use fresh, isolated InMemory repositories, Storage, and Authenticated Admin User.
    """
    cat_repo = InMemoryCategoryRepository()
    prod_repo = InMemoryProductRepository()
    sales_repo = InMemorySalesRepository()
    order_repo = InMemoryOrderRepository()
    cust_repo = InMemoryCustomerRepository(order_repo=order_repo)
    storage_srv = InMemoryStorageService()
    test_user = AuthenticatedUser(
        user_id="test-admin-uuid",
        email="admin@accessoryinventory.com",
        role="authenticated",
        app_metadata={"role": "admin"},
    )
    app.dependency_overrides[get_category_repository] = lambda: cat_repo
    app.dependency_overrides[get_product_repository] = lambda: prod_repo
    app.dependency_overrides[get_sales_repository] = lambda: sales_repo
    app.dependency_overrides[get_order_repository] = lambda: order_repo
    app.dependency_overrides[get_customer_repository] = lambda: cust_repo
    app.dependency_overrides[get_storage_service] = lambda: storage_srv
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[require_admin] = lambda: test_user
    yield
    app.dependency_overrides.clear()
