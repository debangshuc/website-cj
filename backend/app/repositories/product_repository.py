from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Protocol


class ProductRepositoryProtocol(Protocol):
    def get_all(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        stock_status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[dict]: ...

    def get_by_id(self, product_id: str) -> Optional[dict]: ...

    def create(self, product_data: dict) -> dict: ...

    def update(self, product_id: str, update_data: dict) -> Optional[dict]: ...

    def soft_delete(self, product_id: str) -> Optional[dict]: ...

    def adjust_inventory(self, product_id: str, quantity: int) -> Optional[dict]: ...


def _get_initial_products() -> List[dict]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": "PRD-101",
            "name": "Anime Poster Collection",
            "sku": "PST-ANM-001",
            "category_id": "cat-poster-001",
            "category": "Poster",
            "price": Decimal("250.00"),
            "stock": 45,
            "units_sold": 126,
            "image_path": "assets/images/placeholder-poster-main.svg",
            "description": "Set of 6 high-definition aesthetic anime wall art posters with matte lamination.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-102",
            "name": "Sunset Landscape Poster",
            "sku": "PST-SNT-002",
            "category_id": "cat-poster-001",
            "category": "Poster",
            "price": Decimal("250.00"),
            "stock": 18,
            "units_sold": 42,
            "image_path": "assets/images/placeholder-wave.svg",
            "description": "Vibrant sunset landscape artwork printed on 300 GSM thick premium art paper.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-103",
            "name": "Vintage Car Poster",
            "sku": "PST-VTC-003",
            "category_id": "cat-poster-001",
            "category": "Poster",
            "price": Decimal("220.00"),
            "stock": 5,
            "units_sold": 89,
            "image_path": "assets/images/placeholder-car.svg",
            "description": "Classic vintage retro automobile illustration poster with distressed grunge border.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-104",
            "name": "Minimal Wave Poster",
            "sku": "PST-MWV-004",
            "category_id": "cat-poster-001",
            "category": "Poster",
            "price": Decimal("200.00"),
            "stock": 8,
            "units_sold": 64,
            "image_path": "assets/images/placeholder-wave.svg",
            "description": "Japanese inspired minimalist ocean wave decorative wall print.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-105",
            "name": "Black Dragon Keychain",
            "sku": "KCH-BDG-001",
            "category_id": "cat-keychain-002",
            "category": "Keychain",
            "price": Decimal("150.00"),
            "stock": 3,
            "units_sold": 95,
            "image_path": "assets/images/placeholder-keychain.svg",
            "description": "Solid zinc alloy black matte dragon charm keychain with reinforced ring.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-106",
            "name": "Aesthetic Keychain",
            "sku": "KCH-AST-002",
            "category_id": "cat-keychain-002",
            "category": "Keychain",
            "price": Decimal("180.00"),
            "stock": 24,
            "units_sold": 110,
            "image_path": "assets/images/placeholder-keychain.svg",
            "description": "Double-sided acrylic aesthetic pastel keychain for bags, keys, and backpacks.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-107",
            "name": "Minimalist Keychain",
            "sku": "KCH-MNM-003",
            "category_id": "cat-keychain-002",
            "category": "Keychain",
            "price": Decimal("160.00"),
            "stock": 0,
            "units_sold": 78,
            "image_path": "assets/images/placeholder-keychain.svg",
            "description": "Ultra-light aerospace titanium finish minimalist carabiner keychain.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-108",
            "name": "Space Explorer Stickers",
            "sku": "STK-SPC-001",
            "category_id": "cat-sticker-003",
            "category": "Sticker",
            "price": Decimal("120.00"),
            "stock": 7,
            "units_sold": 154,
            "image_path": "assets/images/placeholder-space.svg",
            "description": "Pack of 15 waterproof vinyl stickers featuring planets, astronauts, and rockets.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-109",
            "name": "Cute Stickers Pack",
            "sku": "STK-CTE-002",
            "category_id": "cat-sticker-003",
            "category": "Sticker",
            "price": Decimal("120.00"),
            "stock": 32,
            "units_sold": 180,
            "image_path": "assets/images/placeholder-space.svg",
            "description": "25 assorted cute kawaii animal die-cut stickers for laptops and phone cases.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-110",
            "name": "BTS Photo Card Set",
            "sku": "ACC-BTS-001",
            "category_id": "cat-accessory-004",
            "category": "Accessory",
            "price": Decimal("200.00"),
            "stock": 15,
            "units_sold": 98,
            "image_path": "assets/images/placeholder-poster-main.svg",
            "description": "55-piece glossy LOMO collectible photo cards set in a protective presentation box.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-111",
            "name": "Retro Game Sticker Pack",
            "sku": "STK-RGM-003",
            "category_id": "cat-sticker-003",
            "category": "Sticker",
            "price": Decimal("140.00"),
            "stock": 0,
            "units_sold": 67,
            "image_path": "assets/images/placeholder-space.svg",
            "description": "8-bit retro arcade gaming pixel vinyl decals with UV resistance.",
            "is_active": True,
            "created_at": now_iso,
        },
        {
            "id": "PRD-112",
            "name": "Custom Name Keychain",
            "sku": "KCH-CST-004",
            "category_id": "cat-keychain-002",
            "category": "Keychain",
            "price": Decimal("220.00"),
            "stock": 12,
            "units_sold": 53,
            "image_path": "assets/images/placeholder-keychain.svg",
            "description": "Personalized laser-engraved acrylic block keychain with metallic lobster clasp.",
            "is_active": True,
            "created_at": now_iso,
        },
    ]


class InMemoryProductRepository:
    def __init__(self):
        self._products: Dict[str, dict] = {p["id"]: dict(p) for p in _get_initial_products()}
        self._counter: int = 113

    def reset_to_default(self) -> None:
        self._products = {p["id"]: dict(p) for p in _get_initial_products()}
        self._counter = 113

    def get_all(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        stock_status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[dict]:
        results = list(self._products.values())

        if not include_inactive:
            results = [p for p in results if p.get("is_active", True)]

        if search:
            q = search.strip().lower()
            results = [
                p for p in results
                if q in p["name"].lower() or q in p["sku"].lower() or q in p.get("category", "").lower()
            ]

        if category and category.lower() != "all":
            cat = category.strip().lower()
            results = [
                p for p in results
                if p.get("category", "").lower() == cat or p.get("category_id", "").lower() == cat
            ]

        if stock_status:
            status = stock_status.strip().lower()
            if status == "in_stock":
                results = [p for p in results if p["stock"] > 10]
            elif status == "low_stock":
                results = [p for p in results if 0 < p["stock"] <= 10]
            elif status == "out_of_stock":
                results = [p for p in results if p["stock"] <= 0]

        return [dict(p) for p in results]

    def get_by_id(self, product_id: str) -> Optional[dict]:
        product = self._products.get(product_id)
        return dict(product) if product else None

    def create(self, product_data: dict) -> dict:
        product_id = product_data.get("id")
        if not product_id:
            product_id = f"PRD-{self._counter}"
            self._counter += 1

        cat_id = product_data.get("category_id")
        cat_name = product_data.get("category")
        if not cat_name and cat_id:
            cat_name = cat_id.replace("cat-", "").capitalize()
        elif not cat_name:
            cat_name = "Accessory"

        new_product = {
            **product_data,
            "id": product_id,
            "category_id": cat_id or f"cat-{cat_name.lower()}-001",
            "category": cat_name,
            "units_sold": product_data.get("units_sold", 0),
            "is_active": product_data.get("is_active", True),
            "created_at": product_data.get("created_at", datetime.now(timezone.utc).isoformat()),
        }
        self._products[product_id] = new_product
        return dict(new_product)

    def update(self, product_id: str, update_data: dict) -> Optional[dict]:
        if product_id not in self._products:
            return None

        product = self._products[product_id]
        for key, value in update_data.items():
            if key in ["image_path", "description"]:
                product[key] = value
            elif value is not None:
                product[key] = value

        if "category_id" in update_data and update_data["category_id"] and not update_data.get("category"):
            product["category"] = update_data["category_id"].replace("cat-", "").capitalize()

        return dict(product)

    def soft_delete(self, product_id: str) -> Optional[dict]:
        if product_id not in self._products:
            return None

        product = self._products[product_id]
        product["is_active"] = False
        return dict(product)

    def adjust_inventory(self, product_id: str, quantity: int) -> Optional[dict]:
        if product_id not in self._products:
            return None

        product = self._products[product_id]
        product["stock"] -= quantity
        product["units_sold"] = product.get("units_sold", 0) + quantity
        return dict(product)

    def clear(self):
        self._products.clear()
        self._counter = 101


# Singleton repository instance for application runtime
product_repository = InMemoryProductRepository()
