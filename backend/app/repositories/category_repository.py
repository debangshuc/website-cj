import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Protocol


class CategoryRepositoryProtocol(Protocol):
    def get_all(self, include_inactive: bool = False) -> List[dict]: ...

    def get_by_id(self, category_id: str) -> Optional[dict]: ...

    def get_by_name(self, name: str) -> Optional[dict]: ...

    def create(self, category_data: dict) -> dict: ...

    def update(self, category_id: str, update_data: dict) -> Optional[dict]: ...

    def delete(self, category_id: str) -> Optional[dict]: ...

    def count_products_for_category(self, category_id: str) -> int: ...


def _get_initial_categories() -> List[dict]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": "cat-poster-001",
            "name": "Poster",
            "description": "High-definition aesthetic anime and art posters",
            "is_active": True,
            "product_count": 4,
            "created_at": now_iso,
        },
        {
            "id": "cat-keychain-002",
            "name": "Keychain",
            "description": "Durable metal, acrylic, and enamel keychains",
            "is_active": True,
            "product_count": 4,
            "created_at": now_iso,
        },
        {
            "id": "cat-sticker-003",
            "name": "Sticker",
            "description": "Waterproof vinyl and die-cut sticker packs",
            "is_active": True,
            "product_count": 3,
            "created_at": now_iso,
        },
        {
            "id": "cat-accessory-004",
            "name": "Accessory",
            "description": "Photo cards, phone charms, and miscellaneous collectibles",
            "is_active": True,
            "product_count": 1,
            "created_at": now_iso,
        },
    ]


class InMemoryCategoryRepository:
    def __init__(self):
        self._categories: Dict[str, dict] = {c["id"]: dict(c) for c in _get_initial_categories()}

    def reset_to_default(self) -> None:
        self._categories = {c["id"]: dict(c) for c in _get_initial_categories()}

    def get_all(self, include_inactive: bool = False) -> List[dict]:
        cats = list(self._categories.values())
        if not include_inactive:
            cats = [c for c in cats if c.get("is_active", True)]
        # Sort by name
        cats.sort(key=lambda c: c["name"].lower())
        return [dict(c) for c in cats]

    def get_by_id(self, category_id: str) -> Optional[dict]:
        cat = self._categories.get(category_id)
        return dict(cat) if cat else None

    def get_by_name(self, name: str) -> Optional[dict]:
        clean_name = name.strip().lower()
        for cat in self._categories.values():
            if cat["name"].strip().lower() == clean_name:
                return dict(cat)
        return None

    def create(self, category_data: dict) -> dict:
        cat_id = category_data.get("id") or str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        new_cat = {
            "id": cat_id,
            "name": category_data["name"].strip(),
            "description": category_data.get("description"),
            "is_active": category_data.get("is_active", True),
            "product_count": 0,
            "created_at": category_data.get("created_at", now_iso),
        }
        self._categories[cat_id] = new_cat
        return dict(new_cat)

    def update(self, category_id: str, update_data: dict) -> Optional[dict]:
        if category_id not in self._categories:
            return None

        cat = self._categories[category_id]
        if "name" in update_data and update_data["name"] is not None:
            cat["name"] = update_data["name"].strip()
        if "description" in update_data:
            cat["description"] = update_data["description"]
        if "is_active" in update_data and update_data["is_active"] is not None:
            cat["is_active"] = update_data["is_active"]
        if "product_count" in update_data and update_data["product_count"] is not None:
            cat["product_count"] = update_data["product_count"]

        return dict(cat)

    def delete(self, category_id: str) -> Optional[dict]:
        if category_id not in self._categories:
            return None
        cat = self._categories[category_id]
        # Soft delete / deactivate to preserve references
        cat["is_active"] = False
        return dict(cat)

    def count_products_for_category(self, category_id: str) -> int:
        cat = self._categories.get(category_id)
        return cat.get("product_count", 0) if cat else 0

    def clear(self):
        self._categories.clear()


category_repository = InMemoryCategoryRepository()
