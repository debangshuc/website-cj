import uuid
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Category, Product


class PostgresCategoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def _to_dict(self, category: Category, product_count: int = 0) -> dict:
        return {
            "id": str(category.id),
            "name": category.name,
            "description": category.description,
            "is_active": category.is_active,
            "product_count": product_count,
            "created_at": category.created_at.isoformat() if category.created_at else "",
        }

    def get_all(self, include_inactive: bool = False) -> List[dict]:
        stmt = (
            select(
                Category,
                func.count(Product.id).label("product_count")
            )
            .outerjoin(Product, (Product.category_id == Category.id) & (Product.is_active.is_(True)))
            .group_by(Category.id)
            .order_by(Category.name.asc())
        )

        if not include_inactive:
            stmt = stmt.where(Category.is_active.is_(True))

        results = self.session.execute(stmt).all()
        return [self._to_dict(cat, count) for cat, count in results]

    def get_by_id(self, category_id: str) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(category_id)
        except (ValueError, TypeError):
            return None

        stmt = (
            select(
                Category,
                func.count(Product.id).label("product_count")
            )
            .outerjoin(Product, (Product.category_id == Category.id) & (Product.is_active.is_(True)))
            .where(Category.id == val_uuid)
            .group_by(Category.id)
        )
        res = self.session.execute(stmt).first()
        if not res:
            return None
        cat, count = res
        return self._to_dict(cat, count)

    def get_by_name(self, name: str) -> Optional[dict]:
        clean_name = name.strip().lower()
        stmt = (
            select(
                Category,
                func.count(Product.id).label("product_count")
            )
            .outerjoin(Product, (Product.category_id == Category.id) & (Product.is_active.is_(True)))
            .where(func.lower(Category.name) == clean_name)
            .group_by(Category.id)
        )
        res = self.session.execute(stmt).first()
        if not res:
            return None
        cat, count = res
        return self._to_dict(cat, count)

    def count_products_for_category(self, category_id: str) -> int:
        try:
            val_uuid = uuid.UUID(category_id)
        except (ValueError, TypeError):
            return 0

        stmt = select(func.count(Product.id)).where(Product.category_id == val_uuid)
        return self.session.scalar(stmt) or 0

    def create(self, category_data: dict) -> dict:
        cat_id_val = category_data.get("id")
        uuid_id = uuid.UUID(str(cat_id_val)) if cat_id_val and len(str(cat_id_val)) == 36 else uuid.uuid4()

        category = Category(
            id=uuid_id,
            name=category_data["name"].strip(),
            description=category_data.get("description"),
            is_active=category_data.get("is_active", True),
        )
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return self._to_dict(category, 0)

    def update(self, category_id: str, update_data: dict) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(category_id)
        except (ValueError, TypeError):
            return None

        category = self.session.query(Category).filter_by(id=val_uuid).first()
        if not category:
            return None

        if "name" in update_data and update_data["name"] is not None:
            category.name = update_data["name"].strip()
        if "description" in update_data:
            category.description = update_data["description"]
        if "is_active" in update_data and update_data["is_active"] is not None:
            category.is_active = update_data["is_active"]

        self.session.commit()
        self.session.refresh(category)
        prod_count = self.count_products_for_category(category_id)
        return self._to_dict(category, prod_count)

    def delete(self, category_id: str) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(category_id)
        except (ValueError, TypeError):
            return None

        category = self.session.query(Category).filter_by(id=val_uuid).first()
        if not category:
            return None

        # Check for any referencing products (both active and inactive)
        product_ref_count = self.session.query(Product).filter_by(category_id=val_uuid).count()

        if product_ref_count > 0:
            # Soft delete / deactivate to preserve FK and historical integrity
            category.is_active = False
            self.session.commit()
            self.session.refresh(category)
            return self._to_dict(category, product_ref_count)
        else:
            # Safe hard delete when no products reference this category
            ret = self._to_dict(category, 0)
            self.session.delete(category)
            self.session.commit()
            return ret
