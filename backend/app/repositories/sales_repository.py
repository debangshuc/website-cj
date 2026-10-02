from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Protocol


class SalesRepositoryProtocol(Protocol):
    def get_all(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        date_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[dict]: ...

    def get_by_id(self, sale_id: str) -> Optional[dict]: ...

    def create(self, sale_data: dict) -> dict: ...

    def get_daily_revenue_breakdown(
        self, start_date: datetime, end_date: datetime
    ) -> List[dict]: ...


def _get_relative_iso(days_ago: int = 0, minutes_ago: int = 0) -> str:
    now = datetime.now(timezone.utc)
    target = now - timedelta(days=days_ago, minutes=minutes_ago)
    return target.isoformat()


def _get_initial_sales() -> List[dict]:
    return [
        {
            "id": "SALE-1048",
            "product_id": "PRD-106",
            "product_name": "Aesthetic Keychain",
            "category": "Keychain",
            "quantity": 2,
            "unit_price": Decimal("180.00"),
            "total": Decimal("360.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(0, minutes_ago=30),
        },
        {
            "id": "SALE-1047",
            "product_id": "PRD-102",
            "product_name": "Sunset Landscape Poster",
            "category": "Poster",
            "quantity": 1,
            "unit_price": Decimal("250.00"),
            "total": Decimal("250.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(0, minutes_ago=90),
        },
        {
            "id": "SALE-1046",
            "product_id": "PRD-109",
            "product_name": "Cute Stickers Pack",
            "category": "Sticker",
            "quantity": 3,
            "unit_price": Decimal("120.00"),
            "total": Decimal("360.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(0, minutes_ago=180),
        },
        {
            "id": "SALE-1045",
            "product_id": "PRD-110",
            "product_name": "BTS Photo Card Set",
            "category": "Accessory",
            "quantity": 1,
            "unit_price": Decimal("200.00"),
            "total": Decimal("200.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(0, minutes_ago=240),
        },
        {
            "id": "SALE-1044",
            "product_id": "PRD-101",
            "product_name": "Anime Poster Collection",
            "category": "Poster",
            "quantity": 2,
            "unit_price": Decimal("250.00"),
            "total": Decimal("500.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(0, minutes_ago=360),
        },
        {
            "id": "SALE-1043",
            "product_id": "PRD-107",
            "product_name": "Minimalist Keychain",
            "category": "Keychain",
            "quantity": 2,
            "unit_price": Decimal("160.00"),
            "total": Decimal("320.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(1, minutes_ago=60),
        },
        {
            "id": "SALE-1042",
            "product_id": "PRD-108",
            "product_name": "Space Explorer Stickers",
            "category": "Sticker",
            "quantity": 4,
            "unit_price": Decimal("120.00"),
            "total": Decimal("480.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(1, minutes_ago=150),
        },
        {
            "id": "SALE-1041",
            "product_id": "PRD-103",
            "product_name": "Vintage Car Poster",
            "category": "Poster",
            "quantity": 1,
            "unit_price": Decimal("220.00"),
            "total": Decimal("220.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(1, minutes_ago=300),
        },
        {
            "id": "SALE-1040",
            "product_id": "PRD-101",
            "product_name": "Anime Poster Collection",
            "category": "Poster",
            "quantity": 3,
            "unit_price": Decimal("250.00"),
            "total": Decimal("750.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(3, minutes_ago=60),
        },
        {
            "id": "SALE-1039",
            "product_id": "PRD-112",
            "product_name": "Custom Name Keychain",
            "category": "Keychain",
            "quantity": 2,
            "unit_price": Decimal("220.00"),
            "total": Decimal("440.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(4, minutes_ago=120),
        },
        {
            "id": "SALE-1038",
            "product_id": "PRD-104",
            "product_name": "Minimal Wave Poster",
            "category": "Poster",
            "quantity": 2,
            "unit_price": Decimal("200.00"),
            "total": Decimal("400.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(5, minutes_ago=200),
        },
        {
            "id": "SALE-1037",
            "product_id": "PRD-111",
            "product_name": "Retro Game Sticker Pack",
            "category": "Sticker",
            "quantity": 5,
            "unit_price": Decimal("140.00"),
            "total": Decimal("700.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(12, minutes_ago=100),
        },
        {
            "id": "SALE-1036",
            "product_id": "PRD-105",
            "product_name": "Black Dragon Keychain",
            "category": "Keychain",
            "quantity": 2,
            "unit_price": Decimal("150.00"),
            "total": Decimal("300.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(18, minutes_ago=100),
        },
        {
            "id": "SALE-1035",
            "product_id": "PRD-102",
            "product_name": "Sunset Landscape Poster",
            "category": "Poster",
            "quantity": 2,
            "unit_price": Decimal("250.00"),
            "total": Decimal("500.00"),
            "order_id": None,
            "order_item_id": None,
            "sold_at": _get_relative_iso(24, minutes_ago=100),
        },
    ]


class InMemorySalesRepository:
    def __init__(self):
        self._sales: Dict[str, dict] = {s["id"]: dict(s) for s in _get_initial_sales()}
        self._counter: int = 1049

    def reset_to_default(self) -> None:
        self._sales = {s["id"]: dict(s) for s in _get_initial_sales()}
        self._counter = 1049

    def get_all(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        date_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[dict]:
        results = list(self._sales.values())

        if search:
            q = search.strip().lower()
            results = [
                s for s in results
                if q in s["id"].lower() or q in s["product_name"].lower() or q in s.get("category", "").lower()
            ]

        if category and category.lower() != "all":
            cat = category.strip().lower()
            results = [s for s in results if s.get("category", "").lower() == cat]

        if date_filter and date_filter.lower() != "all":
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            filtered = []
            for s in results:
                try:
                    s_dt = datetime.fromisoformat(s["sold_at"])
                    if s_dt.tzinfo is None:
                        s_dt = s_dt.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    continue

                diff_days = (today_start - s_dt.replace(hour=0, minute=0, second=0, microsecond=0)).days

                if date_filter == "today" and diff_days == 0:
                    filtered.append(s)
                elif date_filter == "yesterday" and diff_days == 1:
                    filtered.append(s)
                elif date_filter == "this_week" and 0 <= diff_days <= 7:
                    filtered.append(s)
                elif date_filter == "this_month" and 0 <= diff_days <= 30:
                    filtered.append(s)

            results = filtered

        # Sorting
        if sort_by == "oldest":
            results.sort(key=lambda s: s.get("sold_at", ""))
        elif sort_by == "amount_desc":
            results.sort(key=lambda s: s.get("total", 0), reverse=True)
        elif sort_by == "amount_asc":
            results.sort(key=lambda s: s.get("total", 0))
        else:  # newest default
            results.sort(key=lambda s: s.get("sold_at", ""), reverse=True)

        return [dict(s) for s in results]

    def get_by_id(self, sale_id: str) -> Optional[dict]:
        sale = self._sales.get(sale_id)
        return dict(sale) if sale else None

    def create(self, sale_data: dict) -> dict:
        # Idempotency check: if order_item_id is provided and already exists, return existing
        oi_id = sale_data.get("order_item_id")
        if oi_id:
            for s in self._sales.values():
                if s.get("order_item_id") == oi_id:
                    return dict(s)

        sale_id = sale_data.get("id")
        if not sale_id:
            sale_id = f"SALE-{self._counter}"
            self._counter += 1

        new_sale = {
            **sale_data,
            "id": sale_id,
            "sold_at": sale_data.get("sold_at", datetime.now(timezone.utc).isoformat()),
        }
        self._sales[sale_id] = new_sale
        return dict(new_sale)

    def get_daily_revenue_breakdown(
        self, start_date: datetime, end_date: datetime
    ) -> List[dict]:
        daily_map: Dict[str, dict] = {}
        for s in self._sales.values():
            sold_at_str = s.get("sold_at")
            if not sold_at_str:
                continue
            try:
                dt = datetime.fromisoformat(sold_at_str)
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

            if start_date <= dt <= end_date:
                day_key = dt.strftime("%Y-%m-%d")
                if day_key not in daily_map:
                    daily_map[day_key] = {
                        "date": day_key,
                        "revenue": Decimal("0.00"),
                        "order_count": 0,
                    }
                daily_map[day_key]["revenue"] += Decimal(str(s.get("total", 0)))
                daily_map[day_key]["order_count"] += 1

        return [daily_map[k] for k in sorted(daily_map.keys())]

    def clear(self):
        self._sales.clear()
        self._counter = 1001


# Singleton repository instance for application runtime
sales_repository = InMemorySalesRepository()
