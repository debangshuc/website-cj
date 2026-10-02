import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload
from app.db.models import Category, Customer, Order, OrderItem, Product


class PostgresOrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def _to_dict(self, order: Order) -> dict:
        items_list = []
        for item in order.items:
            prod = item.product
            cat_name = prod.category.name if prod and prod.category else "Accessory"
            prod_name = prod.name if prod else "Product"
            sku = prod.sku if prod else "SKU"
            items_list.append({
                "id": str(item.id),
                "product_id": str(item.product_id),
                "product_name": prod_name,
                "sku": sku,
                "category": cat_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "line_total": item.line_total,
            })

        return {
            "id": str(order.id),
            "order_number": order.order_number,
            "customer_id": str(order.customer_id) if order.customer_id else None,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "status": order.status,
            "subtotal": order.subtotal,
            "total": order.total,
            "notes": order.notes,
            "items": items_list,
            "created_at": order.created_at.isoformat() if order.created_at else "",
            "updated_at": order.updated_at.isoformat() if order.updated_at else "",
        }

    def _generate_unique_order_number(self) -> str:
        now = datetime.now(timezone.utc)
        prefix = now.strftime("ORD-%Y%m%d")
        for _ in range(10):
            suffix = str(uuid.uuid4())[:6].upper()
            candidate = f"{prefix}-{suffix}"
            exists = self.session.query(Order).filter_by(order_number=candidate).first()
            if not exists:
                return candidate
        return f"{prefix}-{str(uuid.uuid4())[:8].upper()}"

    def get_all(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        date_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[dict]:
        stmt = (
            select(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.category)
            )
        )

        if status and status.lower() != "all":
            clean_status = status.strip().lower()
            stmt = stmt.where(Order.status == clean_status)

        if search:
            q = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Order.order_number).like(q),
                    func.lower(Order.customer_name).like(q),
                    func.lower(Order.customer_email).like(q),
                )
            )

        if sort_by == "oldest":
            stmt = stmt.order_by(Order.created_at.asc())
        elif sort_by == "total_desc":
            stmt = stmt.order_by(Order.total.desc())
        elif sort_by == "total_asc":
            stmt = stmt.order_by(Order.total.asc())
        else:  # newest default
            stmt = stmt.order_by(Order.created_at.desc())

        orders = self.session.scalars(stmt).unique().all()
        return [self._to_dict(o) for o in orders]

    def get_by_id(self, order_id: str) -> Optional[dict]:
        stmt = (
            select(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.category)
            )
        )

        try:
            val_uuid = uuid.UUID(order_id)
            stmt = stmt.where(Order.id == val_uuid)
        except (ValueError, TypeError):
            # Try searching by order_number
            stmt = stmt.where(func.lower(Order.order_number) == order_id.strip().lower())

        order = self.session.scalars(stmt).unique().first()
        return self._to_dict(order) if order else None

    def create(self, order_data: dict, items_data: List[dict]) -> dict:
        order_id_val = order_data.get("id")
        uuid_id = uuid.UUID(str(order_id_val)) if order_id_val and len(str(order_id_val)) == 36 else uuid.uuid4()
        order_number = order_data.get("order_number") or self._generate_unique_order_number()

        cust_id_val = order_data.get("customer_id")
        cust_uuid = uuid.UUID(str(cust_id_val)) if cust_id_val and len(str(cust_id_val)) == 36 else None

        subtotal = Decimal("0.00")
        order_items_objs = []

        for item_data in items_data:
            item_id_val = item_data.get("id")
            item_uuid = uuid.UUID(str(item_id_val)) if item_id_val and len(str(item_id_val)) == 36 else uuid.uuid4()
            prod_uuid = uuid.UUID(str(item_data["product_id"]))
            qty = int(item_data["quantity"])
            unit_price = Decimal(str(item_data["unit_price"]))
            line_total = Decimal(str(item_data.get("line_total") or (qty * unit_price)))
            subtotal += line_total

            order_item = OrderItem(
                id=item_uuid,
                order_id=uuid_id,
                product_id=prod_uuid,
                quantity=qty,
                unit_price=unit_price,
                line_total=line_total,
            )
            order_items_objs.append(order_item)

        total = order_data.get("total", subtotal)

        order = Order(
            id=uuid_id,
            order_number=order_number,
            customer_id=cust_uuid,
            customer_name=order_data.get("customer_name"),
            customer_email=order_data.get("customer_email"),
            status=order_data.get("status", "pending"),
            subtotal=subtotal,
            total=Decimal(str(total)),
            notes=order_data.get("notes"),
        )
        order.items = order_items_objs

        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return self.get_by_id(str(order.id))

    def update_status(self, order_id: str, new_status: str) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(order_id)
            order = self.session.query(Order).filter_by(id=val_uuid).first()
        except (ValueError, TypeError):
            order = self.session.query(Order).filter(func.lower(Order.order_number) == order_id.strip().lower()).first()

        if not order:
            return None

        order.status = new_status
        order.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(order)
        return self.get_by_id(str(order.id))

    def get_metrics(self) -> dict:
        total_stmt = select(
            func.count(Order.id).label("total_orders"),
            func.count(Order.id).filter(Order.status == "pending").label("pending_orders"),
            func.count(Order.id).filter(Order.status == "confirmed").label("confirmed_orders"),
            func.count(Order.id).filter(Order.status == "completed").label("completed_orders"),
            func.count(Order.id).filter(Order.status == "cancelled").label("cancelled_orders"),
            func.coalesce(func.sum(Order.total).filter(Order.status == "completed"), 0).label("total_revenue"),
        )
        res = self.session.execute(total_stmt).first()
        if not res:
            return {
                "total_orders": 0,
                "pending_orders": 0,
                "confirmed_orders": 0,
                "completed_orders": 0,
                "cancelled_orders": 0,
                "total_revenue": Decimal("0.00"),
            }

        return {
            "total_orders": int(res.total_orders or 0),
            "pending_orders": int(res.pending_orders or 0),
            "confirmed_orders": int(res.confirmed_orders or 0),
            "completed_orders": int(res.completed_orders or 0),
            "cancelled_orders": int(res.cancelled_orders or 0),
            "total_revenue": Decimal(str(res.total_revenue or "0.00")),
        }
