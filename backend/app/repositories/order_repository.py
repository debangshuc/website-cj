import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Protocol


class OrderRepositoryProtocol(Protocol):
    def get_all(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        date_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[dict]: ...

    def get_by_id(self, order_id: str) -> Optional[dict]: ...

    def create(self, order_data: dict, items_data: List[dict]) -> dict: ...

    def update_status(self, order_id: str, new_status: str) -> Optional[dict]: ...

    def get_metrics(self) -> dict: ...


def _generate_order_number() -> str:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:6].upper()
    return f"ORD-{ts}-{short_uuid}"


def _get_initial_orders() -> List[dict]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": "ord-sample-001",
            "order_number": "ORD-20260901-A101",
            "customer_id": "cust-001",
            "customer_name": "Aarav Sharma",
            "customer_email": "aarav.sharma@example.com",
            "status": "completed",
            "subtotal": Decimal("500.00"),
            "total": Decimal("500.00"),
            "notes": "Delivered to reception desk",
            "items": [
                {
                    "id": "item-001",
                    "product_id": "PRD-101",
                    "product_name": "Anime Poster Collection",
                    "sku": "PST-ANM-001",
                    "category": "Poster",
                    "quantity": 2,
                    "unit_price": Decimal("250.00"),
                    "line_total": Decimal("500.00"),
                }
            ],
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "ord-sample-002",
            "order_number": "ORD-20260901-B202",
            "customer_id": "cust-002",
            "customer_name": "Priya Patel",
            "customer_email": "priya.p@example.com",
            "status": "confirmed",
            "subtotal": Decimal("300.00"),
            "total": Decimal("300.00"),
            "notes": "Gift wrap requested",
            "items": [
                {
                    "id": "item-002",
                    "product_id": "PRD-105",
                    "product_name": "Black Dragon Keychain",
                    "sku": "KCH-BDG-001",
                    "category": "Keychain",
                    "quantity": 2,
                    "unit_price": Decimal("150.00"),
                    "line_total": Decimal("300.00"),
                }
            ],
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "ord-sample-003",
            "order_number": "ORD-20260901-C303",
            "customer_id": "cust-003",
            "customer_name": "Rohan Gupta",
            "customer_email": "rohan.g@example.com",
            "status": "pending",
            "subtotal": Decimal("240.00"),
            "total": Decimal("240.00"),
            "notes": "Awaiting online payment confirmation",
            "items": [
                {
                    "id": "item-003",
                    "product_id": "PRD-108",
                    "product_name": "Space Explorer Stickers",
                    "sku": "STK-SPC-001",
                    "category": "Sticker",
                    "quantity": 2,
                    "unit_price": Decimal("120.00"),
                    "line_total": Decimal("240.00"),
                }
            ],
            "created_at": now_iso,
            "updated_at": now_iso,
        },
    ]


class InMemoryOrderRepository:
    def __init__(self):
        self._orders: Dict[str, dict] = {o["id"]: dict(o) for o in _get_initial_orders()}

    def reset_to_default(self) -> None:
        self._orders = {o["id"]: dict(o) for o in _get_initial_orders()}

    def get_all(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        date_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[dict]:
        results = list(self._orders.values())

        if status and status.lower() != "all":
            clean_status = status.strip().lower()
            results = [o for o in results if o["status"].lower() == clean_status]

        if search:
            q = search.strip().lower()
            filtered = []
            for o in results:
                match_num = q in o["order_number"].lower()
                match_cust = (o.get("customer_name") and q in o["customer_name"].lower()) or (
                    o.get("customer_email") and q in o["customer_email"].lower()
                )
                match_items = any(
                    q in item["product_name"].lower() or q in item["sku"].lower()
                    for item in o.get("items", [])
                )
                if match_num or match_cust or match_items:
                    filtered.append(o)
            results = filtered

        # Sorting
        if sort_by == "oldest":
            results.sort(key=lambda o: o.get("created_at", ""))
        elif sort_by == "total_desc":
            results.sort(key=lambda o: o.get("total", 0), reverse=True)
        elif sort_by == "total_asc":
            results.sort(key=lambda o: o.get("total", 0))
        else:  # newest default
            results.sort(key=lambda o: o.get("created_at", ""), reverse=True)

        return [dict(o) for o in results]

    def get_by_id(self, order_id: str) -> Optional[dict]:
        order = self._orders.get(order_id)
        if not order:
            # Also allow lookup by order_number
            for o in self._orders.values():
                if o["order_number"].lower() == order_id.lower():
                    return dict(o)
            return None
        return dict(order)

    def create(self, order_data: dict, items_data: List[dict]) -> dict:
        order_id = order_data.get("id") or str(uuid.uuid4())
        order_number = order_data.get("order_number") or _generate_order_number()
        now_iso = datetime.now(timezone.utc).isoformat()

        formatted_items = []
        subtotal = Decimal("0.00")
        for item in items_data:
            item_id = item.get("id") or str(uuid.uuid4())
            qty = int(item["quantity"])
            unit_price = Decimal(str(item["unit_price"]))
            line_total = Decimal(str(item.get("line_total") or (qty * unit_price)))
            subtotal += line_total
            formatted_items.append({
                "id": item_id,
                "product_id": item["product_id"],
                "product_name": item.get("product_name", "Product"),
                "sku": item.get("sku", "SKU"),
                "category": item.get("category", "Accessory"),
                "quantity": qty,
                "unit_price": unit_price,
                "line_total": line_total,
            })

        total = order_data.get("total", subtotal)

        new_order = {
            "id": order_id,
            "order_number": order_number,
            "customer_id": order_data.get("customer_id"),
            "customer_name": order_data.get("customer_name"),
            "customer_email": order_data.get("customer_email"),
            "status": order_data.get("status", "pending"),
            "subtotal": subtotal,
            "total": Decimal(str(total)),
            "notes": order_data.get("notes"),
            "items": formatted_items,
            "created_at": order_data.get("created_at", now_iso),
            "updated_at": order_data.get("updated_at", now_iso),
        }
        self._orders[order_id] = new_order
        return dict(new_order)

    def update_status(self, order_id: str, new_status: str) -> Optional[dict]:
        order = self.get_by_id(order_id)
        if not order:
            return None

        actual_id = order["id"]
        self._orders[actual_id]["status"] = new_status
        self._orders[actual_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        return dict(self._orders[actual_id])

    def get_metrics(self) -> dict:
        orders = list(self._orders.values())
        total = len(orders)
        pending = sum(1 for o in orders if o["status"] == "pending")
        confirmed = sum(1 for o in orders if o["status"] == "confirmed")
        completed = sum(1 for o in orders if o["status"] == "completed")
        cancelled = sum(1 for o in orders if o["status"] == "cancelled")
        revenue = sum(
            (o["total"] for o in orders if o["status"] == "completed"),
            Decimal("0.00"),
        )

        return {
            "total_orders": total,
            "pending_orders": pending,
            "confirmed_orders": confirmed,
            "completed_orders": completed,
            "cancelled_orders": cancelled,
            "total_revenue": revenue,
        }

    def clear(self):
        self._orders.clear()


order_repository = InMemoryOrderRepository()
