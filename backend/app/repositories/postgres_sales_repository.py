import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload
from app.db.models import Category, Product, Sale


class PostgresSalesRepository:
    def __init__(self, session: Session):
        self.session = session

    def _to_dict(self, sale: Sale) -> dict:
        prod = sale.product
        cat_name = prod.category.name if prod and prod.category else "Uncategorized"
        prod_name = prod.name if prod else "Unknown Product"
        return {
            "id": str(sale.id),
            "product_id": str(sale.product_id),
            "product_name": prod_name,
            "category": cat_name,
            "quantity": sale.quantity,
            "unit_price": sale.unit_price,
            "total": sale.total,
            "order_id": str(sale.order_id) if sale.order_id else None,
            "order_item_id": str(sale.order_item_id) if sale.order_item_id else None,
            "sold_at": sale.sold_at.isoformat() if sale.sold_at else "",
        }

    def get_all(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        date_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[dict]:
        stmt = (
            select(Sale)
            .options(
                joinedload(Sale.product).joinedload(Product.category)
            )
            .join(Sale.product)
            .join(Product.category)
        )

        if search:
            q = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.cast(Sale.id, String=None).ilike(q),
                    func.lower(Product.name).like(q),
                    func.lower(Category.name).like(q),
                )
            )

        if category and category.lower() != "all":
            cat_name = category.strip().lower()
            stmt = stmt.where(func.lower(Category.name) == cat_name)

        if date_filter and date_filter.lower() != "all":
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            if date_filter == "today":
                stmt = stmt.where(Sale.sold_at >= today_start)
            elif date_filter == "yesterday":
                yesterday_start = today_start - timedelta(days=1)
                stmt = stmt.where(Sale.sold_at >= yesterday_start, Sale.sold_at < today_start)
            elif date_filter == "this_week":
                week_start = today_start - timedelta(days=7)
                stmt = stmt.where(Sale.sold_at >= week_start)
            elif date_filter == "this_month":
                month_start = today_start - timedelta(days=30)
                stmt = stmt.where(Sale.sold_at >= month_start)

        # Sorting
        if sort_by == "oldest":
            stmt = stmt.order_by(Sale.sold_at.asc())
        elif sort_by == "amount_desc":
            stmt = stmt.order_by(Sale.total.desc())
        elif sort_by == "amount_asc":
            stmt = stmt.order_by(Sale.total.asc())
        else:  # newest default
            stmt = stmt.order_by(Sale.sold_at.desc())

        sales = self.session.scalars(stmt).unique().all()
        return [self._to_dict(s) for s in sales]

    def get_by_id(self, sale_id: str) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(sale_id)
        except ValueError:
            return None

        stmt = (
            select(Sale)
            .options(
                joinedload(Sale.product).joinedload(Product.category)
            )
            .where(Sale.id == val_uuid)
        )
        sale = self.session.scalars(stmt).unique().first()
        return self._to_dict(sale) if sale else None

    def create(self, sale_data: dict) -> dict:
        """
        Atomic sale recording transaction with SELECT ... FOR UPDATE row locking.
        Supports both standalone direct sales and order-completion sales.
        """
        product_id = sale_data["product_id"]
        quantity = int(sale_data["quantity"])
        unit_price = Decimal(str(sale_data["unit_price"]))
        sold_at_str = sale_data.get("sold_at")
        order_id_val = sale_data.get("order_id")
        order_item_id_val = sale_data.get("order_item_id")

        # Idempotency check: if order_item_id is provided, check if sale already exists
        if order_item_id_val:
            try:
                oi_uuid = uuid.UUID(str(order_item_id_val))
                existing_sale = self.session.query(Sale).filter_by(order_item_id=oi_uuid).first()
                if existing_sale:
                    return self._to_dict(existing_sale)
            except (ValueError, TypeError):
                pass

        try:
            val_prod_uuid = uuid.UUID(str(product_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found.",
            )

        try:
            # 1. Lock product row with FOR UPDATE
            lock_stmt = select(Product).where(Product.id == val_prod_uuid).with_for_update()
            product = self.session.scalars(lock_stmt).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID '{product_id}' not found.",
                )

            if quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity must be greater than 0.",
                )

            # 2. If standalone sale (not generated from an order), validate and decrement stock
            is_from_order = bool(order_id_val or order_item_id_val)
            if not is_from_order:
                if quantity > product.stock:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Only {product.stock} units are currently available.",
                    )
                product.stock -= quantity

            # Increment units sold
            product.units_sold += quantity

            # 3. Calculate total
            total = sale_data.get("total") or (Decimal(quantity) * unit_price)

            # 4. Insert sale record
            sale_id_val = sale_data.get("id")
            uuid_id = uuid.UUID(str(sale_id_val)) if sale_id_val and len(str(sale_id_val)) == 36 else uuid.uuid4()
            order_uuid = uuid.UUID(str(order_id_val)) if order_id_val and len(str(order_id_val)) == 36 else None
            order_item_uuid = uuid.UUID(str(order_item_id_val)) if order_item_id_val and len(str(order_item_id_val)) == 36 else None

            sale = Sale(
                id=uuid_id,
                product_id=product.id,
                order_id=order_uuid,
                order_item_id=order_item_uuid,
                quantity=quantity,
                unit_price=unit_price,
                total=Decimal(str(total)),
            )
            if sold_at_str:
                try:
                    dt = datetime.fromisoformat(sold_at_str)
                    sale.sold_at = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            self.session.add(sale)
            self.session.commit()
            self.session.refresh(sale)
            return self._to_dict(sale)

        except HTTPException:
            self.session.rollback()
            raise
        except Exception as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record sale: {str(exc)}",
            )

    def get_daily_revenue_breakdown(
        self, start_date: datetime, end_date: datetime
    ) -> List[dict]:
        """
        Group historical sales by day using PostgreSQL date_trunc aggregation.
        """
        day_col = func.date_trunc("day", Sale.sold_at).label("day_bucket")
        stmt = (
            select(
                day_col,
                func.sum(Sale.total).label("total_revenue"),
                func.count(Sale.id).label("total_orders"),
            )
            .where(Sale.sold_at >= start_date, Sale.sold_at <= end_date)
            .group_by(day_col)
            .order_by(day_col.asc())
        )
        results = self.session.execute(stmt).all()
        breakdown = []
        for r in results:
            dt_val = r.day_bucket
            date_str = dt_val.date().isoformat() if hasattr(dt_val, "date") else str(dt_val)[:10]
            breakdown.append({
                "date": date_str,
                "revenue": r.total_revenue or Decimal("0.00"),
                "order_count": int(r.total_orders or 0),
            })
        return breakdown
