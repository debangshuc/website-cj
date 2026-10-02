from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.schemas.sale import DashboardSummaryResponse, RevenueAnalyticsResponse
from app.services.dashboard_service import DashboardService
from app.api.dependencies import require_admin, get_dashboard_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get dashboard summary metrics",
    description="Calculate live overview KPI metrics, revenue, sales counts, best sellers, low stock products, and overview chart analytics.",
)
def get_dashboard_summary(
    period: Optional[str] = Query(
        default="week",
        description="Time period for revenue overview chart ('today', 'week', 'month')",
    ),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryResponse:
    return service.get_summary(period=period or "week")


@router.get(
    "/revenue",
    response_model=RevenueAnalyticsResponse,
    summary="Get historical revenue analytics",
    description="Get daily aggregated revenue time-series points and period totals for charting.",
)
def get_revenue_analytics(
    period: Optional[str] = Query(
        default="week",
        description="Analytics interval ('today', 'week', 'month')",
    ),
    service: DashboardService = Depends(get_dashboard_service),
) -> RevenueAnalyticsResponse:
    return service.get_revenue_analytics(period=period or "week")
