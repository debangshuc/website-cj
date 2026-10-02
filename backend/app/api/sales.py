from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.sale import SaleCreate, SaleResponse
from app.services.sales_service import SalesService
from app.api.dependencies import require_admin, get_sales_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get(
    "",
    response_model=List[SaleResponse],
    summary="List sales",
    description="Retrieve sales transactions with optional filters by search term, category, date range, or sorting.",
)
def list_sales(
    search: Optional[str] = Query(default=None, description="Search by Sale ID, Product Name, or Category"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    date_filter: Optional[str] = Query(
        default=None,
        description="Filter by relative date range ('today', 'yesterday', 'this_week', 'this_month', 'all')",
    ),
    sort_by: Optional[str] = Query(
        default=None,
        description="Sort order ('newest', 'oldest', 'amount_desc', 'amount_asc')",
    ),
    service: SalesService = Depends(get_sales_service),
) -> List[SaleResponse]:
    return service.list_sales(
        search=search,
        category=category,
        date_filter=date_filter,
        sort_by=sort_by,
    )


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get sale by ID",
    description="Retrieve a single sales transaction by its unique ID.",
)
def get_sale(
    sale_id: str,
    service: SalesService = Depends(get_sales_service),
) -> SaleResponse:
    return service.get_sale(sale_id)


@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record sale",
    description="Record a new sales transaction. Automatically calculates total, validates stock, and decrements inventory.",
)
def record_sale(
    sale_in: SaleCreate,
    service: SalesService = Depends(get_sales_service),
) -> SaleResponse:
    return service.record_sale(sale_in)
