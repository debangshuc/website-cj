from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.order import (
    OrderCreate,
    OrderMetricsResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services.order_service import OrderService
from app.api.dependencies import require_admin, get_order_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="List orders",
    description="Retrieve customer orders with optional status, search, and sorting filters.",
)
def list_orders(
    status: Optional[str] = Query(default=None, description="Filter by status (pending, confirmed, completed, cancelled)"),
    search: Optional[str] = Query(default=None, description="Search query across order number, customer name, email, or products"),
    date_filter: Optional[str] = Query(default=None, description="Date filter interval"),
    sort_by: Optional[str] = Query(default="newest", description="Sort order: newest, oldest, total_desc, total_asc"),
    service: OrderService = Depends(get_order_service),
) -> List[OrderResponse]:
    return service.list_orders(
        search=search,
        status_filter=status,
        date_filter=date_filter,
        sort_by=sort_by,
    )


@router.get(
    "/metrics",
    response_model=OrderMetricsResponse,
    summary="Order KPI summary metrics",
    description="Retrieve aggregated counts by status and completed revenue.",
)
def get_order_metrics(
    service: OrderService = Depends(get_order_service),
) -> OrderMetricsResponse:
    return service.get_metrics()


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details",
    description="Retrieve detailed order information and snapshot line items by UUID or human-readable order number.",
)
def get_order(
    order_id: str,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return service.get_order(order_id)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer order",
    description="Create a new customer order in pending state with authoritative price snapshots and inventory reservation.",
)
def create_order(
    order_in: OrderCreate,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return service.create_order(order_in)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
    description="Execute controlled order lifecycle status transitions: pending -> confirmed/cancelled, confirmed -> completed/cancelled.",
)
def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return service.update_order_status(order_id, status_update)
