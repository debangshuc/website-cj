from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerMetricsResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService
from app.api.dependencies import require_admin, get_customer_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get(
    "",
    response_model=List[CustomerResponse],
    summary="List customers",
    description="Retrieve customers with optional search, status filtering, sorting, and pagination.",
)
def list_customers(
    search: Optional[str] = Query(default=None, description="Search query across name, email, or phone"),
    status: Optional[str] = Query(default=None, description="Filter by status: active, inactive, or all"),
    sort_by: Optional[str] = Query(default="newest", description="Sort order: newest, oldest, name_asc, name_desc, total_spent_desc, orders_desc"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    service: CustomerService = Depends(get_customer_service),
) -> List[CustomerResponse]:
    return service.list_customers(
        search=search,
        status_filter=status,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/metrics",
    response_model=CustomerMetricsResponse,
    summary="Customer summary KPI metrics",
    description="Retrieve aggregated customer counts and total customer lifetime spend.",
)
def get_customer_metrics(
    service: CustomerService = Depends(get_customer_service),
) -> CustomerMetricsResponse:
    return service.get_metrics()


@router.get(
    "/{customer_id}",
    response_model=CustomerDetailResponse,
    summary="Get customer details",
    description="Retrieve comprehensive customer CRM profile and associated order history.",
)
def get_customer(
    customer_id: str,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerDetailResponse:
    return service.get_customer(customer_id)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer",
    description="Register a new customer record with normalized email and phone contact details.",
)
def create_customer(
    customer_in: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    return service.create_customer(customer_in)


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update customer profile / status",
    description="Update customer contact information, notes, or toggle is_active status (soft-delete).",
)
def update_customer(
    customer_id: str,
    customer_in: CustomerUpdate,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    return service.update_customer(customer_id, customer_in)
