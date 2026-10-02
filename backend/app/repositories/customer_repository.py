import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Protocol


class CustomerRepositoryProtocol(Protocol):
    def get_all(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> List[dict]: ...

    def get_by_id(self, customer_id: str) -> Optional[dict]: ...

    def get_by_email(self, email: str) -> Optional[dict]: ...

    def create(self, customer_data: dict) -> dict: ...

    def update(self, customer_id: str, update_data: dict) -> Optional[dict]: ...

    def get_metrics(self) -> dict: ...

    def get_customer_orders(self, customer_id: str) -> List[dict]: ...


def _get_initial_customers() -> List[dict]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": "cust-001",
            "name": "Aarav Sharma",
            "email": "aarav.sharma@example.com",
            "phone": "+91 98765 43210",
            "address": "42 Connaught Place, New Delhi",
            "notes": "VIP regular collector",
            "is_active": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "cust-002",
            "name": "Priya Patel",
            "email": "priya.p@example.com",
            "phone": "+91 98234 56789",
            "address": "15 MG Road, Bengaluru",
            "notes": "Prefers gift packaging",
            "is_active": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "id": "cust-003",
            "name": "Rohan Gupta",
            "email": "rohan.g@example.com",
            "phone": "+91 97111 22233",
            "address": "78 Park Street, Kolkata",
            "notes": "Sticker enthusiast",
            "is_active": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
    ]


class InMemoryCustomerRepository:
    def __init__(self, order_repo=None):
        self._customers: Dict[str, dict] = {c["id"]: dict(c) for c in _get_initial_customers()}
        self._order_repo = order_repo

    def set_order_repository(self, order_repo):
        self._order_repo = order_repo

    def reset_to_default(self) -> None:
        self._customers = {c["id"]: dict(c) for c in _get_initial_customers()}

    def _enrich_customer(self, customer: dict) -> dict:
        cust_copy = dict(customer)
        cust_id = cust_copy["id"]
        orders = self.get_customer_orders(cust_id)

        # Non-cancelled orders count
        active_orders = [o for o in orders if o["status"] != "cancelled"]
        completed_orders = [o for o in orders if o["status"] == "completed"]

        total_spent = sum((o["total"] for o in completed_orders), Decimal("0.00"))

        last_order = max((o.get("created_at", "") for o in orders), default=None) if orders else None

        cust_copy["order_count"] = len(active_orders)
        cust_copy["completed_order_count"] = len(completed_orders)
        cust_copy["total_spent"] = total_spent
        cust_copy["last_order_at"] = last_order
        return cust_copy

    def get_all(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> List[dict]:
        results = [self._enrich_customer(c) for c in self._customers.values()]

        # Filter by status
        if status and status.lower() != "all":
            if status.lower() == "active":
                results = [c for c in results if c["is_active"]]
            elif status.lower() == "inactive":
                results = [c for c in results if not c["is_active"]]

        # Search
        if search:
            q = search.strip().lower()
            results = [
                c for c in results
                if q in c["name"].lower()
                or (c.get("email") and q in c["email"].lower())
                or (c.get("phone") and q in c["phone"].lower())
            ]

        # Sorting
        if sort_by == "oldest":
            results.sort(key=lambda c: c.get("created_at", ""))
        elif sort_by == "name_asc":
            results.sort(key=lambda c: c.get("name", "").lower())
        elif sort_by == "name_desc":
            results.sort(key=lambda c: c.get("name", "").lower(), reverse=True)
        elif sort_by == "total_spent_desc":
            results.sort(key=lambda c: c.get("total_spent", 0), reverse=True)
        elif sort_by == "orders_desc":
            results.sort(key=lambda c: c.get("order_count", 0), reverse=True)
        else:  # newest default
            results.sort(key=lambda c: c.get("created_at", ""), reverse=True)

        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end]

    def get_by_id(self, customer_id: str) -> Optional[dict]:
        customer = self._customers.get(customer_id)
        if not customer:
            return None
        return self._enrich_customer(customer)

    def get_by_email(self, email: str) -> Optional[dict]:
        if not email:
            return None
        norm = email.strip().lower()
        for c in self._customers.values():
            if c.get("email") and c["email"].strip().lower() == norm:
                return self._enrich_customer(c)
        return None

    def create(self, customer_data: dict) -> dict:
        cust_id = customer_data.get("id") or str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        email = customer_data.get("email")
        norm_email = email.strip().lower() if email else None

        new_cust = {
            "id": cust_id,
            "name": customer_data["name"].strip(),
            "email": norm_email,
            "phone": customer_data.get("phone"),
            "address": customer_data.get("address"),
            "notes": customer_data.get("notes"),
            "is_active": customer_data.get("is_active", True),
            "created_at": customer_data.get("created_at", now_iso),
            "updated_at": customer_data.get("updated_at", now_iso),
        }
        self._customers[cust_id] = new_cust
        return self._enrich_customer(new_cust)

    def update(self, customer_id: str, update_data: dict) -> Optional[dict]:
        cust = self._customers.get(customer_id)
        if not cust:
            return None

        for k, v in update_data.items():
            if k == "email" and v:
                cust[k] = v.strip().lower()
            elif k in ["name", "phone", "address", "notes", "is_active"]:
                cust[k] = v

        cust["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._customers[customer_id] = cust
        return self._enrich_customer(cust)

    def get_customer_orders(self, customer_id: str) -> List[dict]:
        if not self._order_repo:
            return []
        all_orders = self._order_repo.get_all()
        # Find orders by customer_id or matching customer_email
        cust = self._customers.get(customer_id)
        cust_email = cust.get("email").lower() if cust and cust.get("email") else None

        matching = []
        for o in all_orders:
            if o.get("customer_id") == customer_id:
                matching.append(o)
            elif not o.get("customer_id") and cust_email and o.get("customer_email"):
                if o["customer_email"].strip().lower() == cust_email:
                    matching.append(o)

        matching.sort(key=lambda o: o.get("created_at", ""), reverse=True)
        return matching

    def get_metrics(self) -> dict:
        customers = [self._enrich_customer(c) for c in self._customers.values()]
        total = len(customers)
        active = sum(1 for c in customers if c["is_active"])
        with_orders = sum(1 for c in customers if c["order_count"] > 0)
        total_rev = sum((c["total_spent"] for c in customers), Decimal("0.00"))

        return {
            "total_customers": total,
            "active_customers": active,
            "customers_with_orders": with_orders,
            "total_revenue": total_rev,
        }

    def clear(self):
        self._customers.clear()


customer_repository = InMemoryCustomerRepository()
