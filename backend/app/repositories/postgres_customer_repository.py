import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.db.models import Customer, Order, OrderItem, Product


class PostgresCustomerRepository:
    def __init__(self, session: Session):
        self.session = session

    def _build_aggregate_query(self):
        return (
            select(
                Customer,
                func.count(Order.id).filter(Order.status != "cancelled").label("order_count"),
                func.count(Order.id).filter(Order.status == "completed").label("completed_order_count"),
                func.coalesce(
                    func.sum(Order.total).filter(Order.status == "completed"), 0
                ).label("total_spent"),
                func.max(Order.created_at).label("last_order_at"),
            )
            .outerjoin(Order, Order.customer_id == Customer.id)
            .group_by(Customer.id)
        )

    def _get_lifetime_items(
        self, customer_ids: List[uuid.UUID]
    ) -> dict:
        """
        Grouped per-product quantity totals for the customers' non-cancelled orders.
        A single grouped query for all requested customer IDs (no N+1 pattern).
        """
        if not customer_ids:
            return {}

        stmt = (
            select(
                Order.customer_id.label("lifetime_customer_id"),
                Product.id.label("lifetime_product_id"),
                Product.name.label("lifetime_product_name"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("lifetime_total_quantity"),
            )
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(
                Order.status != "cancelled",
                Order.customer_id.in_(customer_ids),
            )
            .group_by(Order.customer_id, Product.id, Product.name)
            .order_by(Order.customer_id, Product.name)
        )

        grouped = {}
        for row in self.session.execute(stmt).all():
            grouped.setdefault(row.lifetime_customer_id, []).append(
                {
                    "product_id": str(row.lifetime_product_id),
                    "product_name": row.lifetime_product_name,
                    "total_quantity": int(row.lifetime_total_quantity or 0),
                }
            )
        return grouped

    def _row_to_dict(self, row, lifetime_items=None) -> dict:
        cust = row[0]
        order_count = int(row[1] or 0)
        completed_order_count = int(row[2] or 0)
        total_spent = Decimal(str(row[3] or "0.00"))
        last_order_at = row[4].isoformat() if row[4] else None

        return {
            "id": str(cust.id),
            "name": cust.name,
            "email": cust.email,
            "phone": cust.phone,
            "address": cust.address,
            "notes": cust.notes,
            "is_active": cust.is_active,
            "order_count": order_count,
            "completed_order_count": completed_order_count,
            "total_spent": total_spent,
            "lifetime_items": lifetime_items or [],
            "last_order_at": last_order_at,
            "created_at": cust.created_at.isoformat() if cust.created_at else "",
            "updated_at": cust.updated_at.isoformat() if cust.updated_at else "",
        }

    def get_all(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> List[dict]:
        stmt = self._build_aggregate_query()

        if status and status.lower() != "all":
            if status.lower() == "active":
                stmt = stmt.where(Customer.is_active == True)
            elif status.lower() == "inactive":
                stmt = stmt.where(Customer.is_active == False)

        if search:
            q = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Customer.name).like(q),
                    func.lower(Customer.email).like(q),
                    func.lower(Customer.phone).like(q),
                )
            )

        # Sorting
        if sort_by == "oldest":
            stmt = stmt.order_by(Customer.created_at.asc())
        elif sort_by == "name_asc":
            stmt = stmt.order_by(Customer.name.asc())
        elif sort_by == "name_desc":
            stmt = stmt.order_by(Customer.name.desc())
        elif sort_by == "total_spent_desc":
            stmt = stmt.order_by(func.sum(Order.total).desc().nullslast())
        elif sort_by == "orders_desc":
            stmt = stmt.order_by(func.count(Order.id).desc())
        else:  # newest default
            stmt = stmt.order_by(Customer.created_at.desc())

        offset_val = (page - 1) * page_size
        stmt = stmt.offset(offset_val).limit(page_size)

        rows = self.session.execute(stmt).all()
        lifetime_by_customer = self._get_lifetime_items([row[0].id for row in rows])
        return [
            self._row_to_dict(r, lifetime_by_customer.get(r[0].id, []))
            for r in rows
        ]

    def get_by_id(self, customer_id: str) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(customer_id)
        except ValueError:
            return None

        stmt = self._build_aggregate_query().where(Customer.id == val_uuid)
        row = self.session.execute(stmt).first()
        if not row:
            return None
        lifetime_by_customer = self._get_lifetime_items([val_uuid])
        return self._row_to_dict(row, lifetime_by_customer.get(val_uuid, []))

    def get_by_email(self, email: str) -> Optional[dict]:
        if not email:
            return None
        norm_email = email.strip().lower()
        stmt = self._build_aggregate_query().where(func.lower(Customer.email) == norm_email)
        row = self.session.execute(stmt).first()
        if not row:
            return None
        lifetime_by_customer = self._get_lifetime_items([row[0].id])
        return self._row_to_dict(row, lifetime_by_customer.get(row[0].id, []))

    def create(self, customer_data: dict) -> dict:
        cust_id_val = customer_data.get("id")
        uuid_id = uuid.UUID(str(cust_id_val)) if cust_id_val and len(str(cust_id_val)) == 36 else uuid.uuid4()

        email = customer_data.get("email")
        norm_email = email.strip().lower() if email else None

        customer = Customer(
            id=uuid_id,
            name=customer_data["name"].strip(),
            email=norm_email,
            phone=customer_data.get("phone"),
            address=customer_data.get("address"),
            notes=customer_data.get("notes"),
            is_active=customer_data.get("is_active", True),
        )

        self.session.add(customer)
        self.session.commit()
        self.session.refresh(customer)
        return self.get_by_id(str(customer.id))

    def update(self, customer_id: str, update_data: dict) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(customer_id)
        except ValueError:
            return None

        customer = self.session.query(Customer).filter_by(id=val_uuid).first()
        if not customer:
            return None

        for k, v in update_data.items():
            if k == "email" and v is not None:
                customer.email = v.strip().lower() if v.strip() else None
            elif k == "name" and v is not None:
                customer.name = v.strip()
            elif k in ["phone", "address", "notes", "is_active"] and v is not None:
                setattr(customer, k, v)

        customer.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(customer)
        return self.get_by_id(str(customer.id))

    def get_customer_orders(self, customer_id: str) -> List[dict]:
        try:
            val_uuid = uuid.UUID(customer_id)
        except ValueError:
            return []

        stmt = select(Order).where(Order.customer_id == val_uuid).order_by(Order.created_at.desc())
        orders = self.session.scalars(stmt).all()
        if not orders:
            return []

        # Attach order items in one grouped query for all fetched orders (no N+1).
        items_stmt = (
            select(
                OrderItem.order_id.label("item_order_id"),
                OrderItem.quantity.label("item_quantity"),
                Product.id.label("item_product_id"),
                Product.name.label("item_product_name"),
            )
            .select_from(OrderItem)
            .join(Product, Product.id == OrderItem.product_id)
            .where(OrderItem.order_id.in_([o.id for o in orders]))
            .order_by(OrderItem.created_at)
        )

        items_by_order = {}
        for row in self.session.execute(items_stmt).all():
            items_by_order.setdefault(row.item_order_id, []).append(
                {
                    "product_id": str(row.item_product_id),
                    "product_name": row.item_product_name,
                    "quantity": int(row.item_quantity or 0),
                }
            )

        return [
            {
                "id": str(o.id),
                "order_number": o.order_number,
                "status": o.status,
                "total": o.total,
                "items": items_by_order.get(o.id, []),
                "created_at": o.created_at.isoformat() if o.created_at else "",
            }
            for o in orders
        ]

    def get_metrics(self) -> dict:
        total_stmt = select(
            func.count(Customer.id).label("total_customers"),
            func.count(Customer.id).filter(Customer.is_active == True).label("active_customers"),
        )
        cust_res = self.session.execute(total_stmt).first()

        orders_stmt = select(
            func.count(func.distinct(Order.customer_id)).filter(Order.customer_id != None).label("customers_with_orders"),
            func.coalesce(func.sum(Order.total).filter(Order.status == "completed"), 0).label("total_revenue"),
        )
        orders_res = self.session.execute(orders_stmt).first()

        return {
            "total_customers": int(cust_res.total_customers or 0) if cust_res else 0,
            "active_customers": int(cust_res.active_customers or 0) if cust_res else 0,
            "customers_with_orders": int(orders_res.customers_with_orders or 0) if orders_res else 0,
            "total_revenue": Decimal(str(orders_res.total_revenue or "0.00")) if orders_res else Decimal("0.00"),
        }
