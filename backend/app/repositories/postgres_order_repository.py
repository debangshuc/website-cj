import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.db.models import Category, Customer, Order, OrderItem, Product

# PostgreSQL's default name for the inline UNIQUE constraint on order_number.
ORDER_NUMBER_CONSTRAINT_NAME = "orders_order_number_key"

MAX_ORDER_NUMBER_COLLISION_RETRIES = 3


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

    def create(self, order_data: dict, items_data: List[dict], *, commit: bool = True) -> dict:
        """
        Create the order and its line items within the caller's session.

        Pass commit=False to insert without committing so the caller can group
        inventory reservation, order creation, and status updates into a single
        atomic transaction. On any failure the caller must roll the session back
        so partially inserted rows are discarded.

        Order-number generation is a check-then-insert sequence, so concurrent
        requests can pick the same candidate. A losing candidate raises a
        unique violation on the order number inside a savepoint: the collision
        is retried with a fresh candidate while the surrounding transaction
        (inventory reservation, caller-owned work) stays intact. Only the
        order-number uniqueness violation is retried; caller-supplied numbers
        and all other errors propagate immediately. The format
        ORD-YYYYMMDD-<suffix> is unchanged.
        """
        order_id_val = order_data.get("id")
        uuid_id = uuid.UUID(str(order_id_val)) if order_id_val and len(str(order_id_val)) == 36 else uuid.uuid4()
        explicit_order_number = order_data.get("order_number")

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

        order: Optional[Order] = None
        collision_failures = 0
        while True:
            try:
                candidate_number = explicit_order_number or self._generate_unique_order_number()
                order = Order(
                    id=uuid_id,
                    order_number=candidate_number,
                    customer_id=cust_uuid,
                    customer_name=order_data.get("customer_name"),
                    customer_email=order_data.get("customer_email"),
                    status=order_data.get("status", "pending"),
                    subtotal=subtotal,
                    total=Decimal(str(total)),
                    notes=order_data.get("notes"),
                )
                order.items = order_items_objs
                with self.session.begin_nested():
                    self.session.add(order)
                    self.session.flush()
                break
            except IntegrityError as exc:
                collision_failures += 1
                if (
                    explicit_order_number
                    or collision_failures > MAX_ORDER_NUMBER_COLLISION_RETRIES
                    or not self._is_order_number_unique_violation(exc)
                ):
                    raise
                # The savepoint rolled back only the collision-losing insert;
                # the outer transaction (inventory reservation, service-owned
                # work) remains valid. Regenerate a candidate and retry.

        if commit:
            self.session.commit()
        self.session.refresh(order)
        return self.get_by_id(str(order.id))

    @staticmethod
    def _is_order_number_unique_violation(exc: IntegrityError) -> bool:
        """True only for the unique violation raised by the order_number key."""
        orig = exc.orig
        sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
        if sqlstate != "23505":
            return False
        constraint_name = getattr(getattr(orig, "diag", None), "constraint_name", None)
        if constraint_name:
            return constraint_name == ORDER_NUMBER_CONSTRAINT_NAME
        return "order_number" in str(orig).lower()

    def try_update_status(self, order_id: str, from_status: str, new_status: str, *, commit: bool = True) -> bool:
        """
        Concurrency-safe conditional status transition.

        Atomically moves the order from `from_status` to `new_status`. Returns
        True only when this caller claimed the transition (exactly one row
        updated, blocking duplicate/cancel-races from acting twice). Returns
        False when the order is no longer in `from_status` (another request won
        the race). Pass commit=False to include this update in a larger,
        service-owned transaction with inventory/sale side effects.
        """
        try:
            val_uuid = uuid.UUID(order_id)
        except (ValueError, TypeError):
            return False

        stmt = (
            update(Order)
            .where(Order.id == val_uuid, Order.status == from_status)
            .values(status=new_status, updated_at=datetime.now(timezone.utc))
        )
        result = self.session.execute(stmt)
        if result.rowcount != 1:
            return False

        if commit:
            self.session.commit()
        return True

    def update_status(self, order_id: str, new_status: str, *, commit: bool = True) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(order_id)
            order = self.session.query(Order).filter_by(id=val_uuid).first()
        except (ValueError, TypeError):
            order = self.session.query(Order).filter(func.lower(Order.order_number) == order_id.strip().lower()).first()

        if not order:
            return None

        order.status = new_status
        order.updated_at = datetime.now(timezone.utc)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        self.session.refresh(order)
        return self.get_by_id(str(order.id))

    def commit(self) -> None:
        """Commit the shared session after a multi-step, service-owned transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Roll back the shared session, discarding all uncommitted changes."""
        self.session.rollback()

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
