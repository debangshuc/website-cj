from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from app.schemas.product import ProductResponse
from app.schemas.sale import (
    BestSellerResponse,
    DailyRevenuePoint,
    DashboardSummaryResponse,
    RevenueAnalyticsResponse,
    SaleResponse,
)
from app.repositories.product_repository import ProductRepositoryProtocol, product_repository
from app.repositories.sales_repository import SalesRepositoryProtocol, sales_repository


class DashboardService:
    def __init__(
        self,
        product_repo: ProductRepositoryProtocol = product_repository,
        sales_repo: SalesRepositoryProtocol = sales_repository,
    ):
        self.product_repo = product_repo
        self.sales_repo = sales_repo

    def get_revenue_analytics(self, period: str = "week") -> RevenueAnalyticsResponse:
        now = datetime.now(timezone.utc)
        today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

        normalized_period = period.lower().strip() if period else "week"

        if normalized_period == "today":
            start_date = today_midnight
            end_date = now
            prev_start = today_midnight - timedelta(days=1)
            prev_end = today_midnight
            date_list = [start_date.date()]
        elif normalized_period == "month":
            start_date = today_midnight - timedelta(days=29)
            end_date = now
            prev_start = start_date - timedelta(days=30)
            prev_end = start_date
            date_list = [(start_date + timedelta(days=i)).date() for i in range(30)]
        else:  # "week" default (last 7 days)
            normalized_period = "week"
            start_date = today_midnight - timedelta(days=6)
            end_date = now
            prev_start = start_date - timedelta(days=7)
            prev_end = start_date
            date_list = [(start_date + timedelta(days=i)).date() for i in range(7)]

        # Fetch daily grouped revenue directly from repository aggregation
        current_rows = self.sales_repo.get_daily_revenue_breakdown(start_date, end_date)
        prev_rows = self.sales_repo.get_daily_revenue_breakdown(prev_start, prev_end)

        revenue_by_date = {r["date"]: r for r in current_rows}
        points: List[DailyRevenuePoint] = []
        total_revenue = Decimal("0.00")

        for d in date_list:
            d_str = d.isoformat()
            data_row = revenue_by_date.get(d_str, {"revenue": Decimal("0.00"), "order_count": 0})
            rev = Decimal(str(data_row.get("revenue", 0)))
            orders = int(data_row.get("order_count", 0))
            total_revenue += rev

            if normalized_period == "today":
                day_label = "Today"
            elif normalized_period == "week":
                day_label = d.strftime("%a")
            else:
                day_label = d.strftime("%d %b")

            points.append(
                DailyRevenuePoint(
                    date=d_str,
                    day=day_label,
                    revenue=rev,
                    order_count=orders,
                )
            )

        prev_total = sum((Decimal(str(r.get("revenue", 0))) for r in prev_rows), Decimal("0.00"))

        return RevenueAnalyticsResponse(
            period=normalized_period,
            total_revenue=total_revenue,
            previous_period_revenue=prev_total,
            points=points,
        )

    def get_summary(self, period: str = "week") -> DashboardSummaryResponse:
        # Active products
        active_products_raw = self.product_repo.get_all(include_inactive=False)
        total_products = len(active_products_raw)
        total_stock = sum(p.get("stock", 0) for p in active_products_raw)

        # Today's sales metrics
        today_sales_raw = self.sales_repo.get_all(date_filter="today")
        today_revenue = sum(s.get("total", Decimal("0.00")) for s in today_sales_raw)
        today_sales_count = len(today_sales_raw)
        units_sold_today = sum(s.get("quantity", 0) for s in today_sales_raw)

        # Best selling product with authoritative historical revenue
        best_selling: Optional[BestSellerResponse] = None
        if active_products_raw:
            sorted_products = sorted(active_products_raw, key=lambda p: p.get("units_sold", 0), reverse=True)
            top_prod = dict(sorted_products[0])
            
            # Authoritatively aggregate historical sales total for this product
            all_sales_raw = self.sales_repo.get_all()
            prod_sales = [s for s in all_sales_raw if s.get("product_id") == top_prod.get("id")]
            top_prod["revenue"] = sum(s.get("total", Decimal("0.00")) for s in prod_sales)
            
            best_selling = BestSellerResponse(**top_prod)

        # Recent 5 sales
        recent_sales_raw = self.sales_repo.get_all(sort_by="newest")[:5]
        recent_sales: List[SaleResponse] = [SaleResponse(**s) for s in recent_sales_raw]

        # Low stock products (0 < stock <= 8)
        low_stock_raw = [p for p in active_products_raw if 0 < p.get("stock", 0) <= 8]
        low_stock_products: List[ProductResponse] = [ProductResponse(**p) for p in low_stock_raw[:4]]

        # Revenue Overview Analytics
        revenue_overview = self.get_revenue_analytics(period=period)

        return DashboardSummaryResponse(
            total_products=total_products,
            total_stock=total_stock,
            today_revenue=today_revenue,
            today_sales=today_sales_count,
            units_sold_today=units_sold_today,
            best_selling_product=best_selling,
            recent_sales=recent_sales,
            low_stock_products=low_stock_products,
            revenue_overview=revenue_overview,
        )


# Default singleton service instance
dashboard_service = DashboardService()
