import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, joinedload
from app.db.models import Category, Product


class PostgresProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def _to_dict(self, product: Product) -> dict:
        return {
            "id": str(product.id),
            "name": product.name,
            "sku": product.sku,
            "category_id": str(product.category_id) if product.category_id else None,
            "category": product.category.name if product.category else "Uncategorized",
            "price": product.price,
            "stock": product.stock,
            "units_sold": product.units_sold,
            "image_path": product.image_path,
            "description": product.description,
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat() if product.created_at else "",
        }

    def _resolve_category(self, category_id: Optional[str] = None, category_name: Optional[str] = None) -> Category:
        if category_id:
            try:
                cat_uuid = uuid.UUID(str(category_id))
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Malformed category ID: '{category_id}'",
                )
            category = self.session.query(Category).filter_by(id=cat_uuid).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID '{category_id}' not found.",
                )
            if not category.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot assign inactive category '{category.name}' to a product.",
                )
            return category

        clean_name = (category_name or "Accessory").strip()
        existing = self.session.query(Category).filter(func.lower(Category.name) == clean_name.lower()).first()
        if existing:
            if not existing.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot assign inactive category '{existing.name}' to a product.",
                )
            return existing

        # Create new category if not existing
        new_cat = Category(name=clean_name, is_active=True)
        self.session.add(new_cat)
        self.session.commit()
        self.session.refresh(new_cat)
        return new_cat

    def get_all(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        stock_status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[dict]:
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .order_by(Product.created_at.desc())
        )

        if not include_inactive:
            stmt = stmt.where(Product.is_active.is_(True))

        if search:
            q = f"%{search.strip().lower()}%"
            stmt = stmt.join(Product.category).where(
                or_(
                    func.lower(Product.name).like(q),
                    func.lower(Product.sku).like(q),
                    func.lower(Category.name).like(q),
                )
            )

        if category and category.lower() != "all":
            cat_query = category.strip().lower()
            if not search:  # avoid duplicate join
                stmt = stmt.join(Product.category)
            # Match by category name or category_id UUID
            stmt = stmt.where(
                or_(
                    func.lower(Category.name) == cat_query,
                    func.cast(Category.id, String=None) == cat_query,
                )
            )

        if stock_status:
            status = stock_status.strip().lower()
            if status == "in_stock":
                stmt = stmt.where(Product.stock > 10)
            elif status == "low_stock":
                stmt = stmt.where(Product.stock > 0, Product.stock <= 10)
            elif status == "out_of_stock":
                stmt = stmt.where(Product.stock <= 0)

        products = self.session.scalars(stmt).unique().all()
        return [self._to_dict(p) for p in products]

    def get_by_id(self, product_id: str) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(product_id)
        except ValueError:
            return None

        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == val_uuid)
        )
        product = self.session.scalars(stmt).unique().first()
        return self._to_dict(product) if product else None

    def create(self, product_data: dict) -> dict:
        category_obj = self._resolve_category(
            category_id=product_data.get("category_id"),
            category_name=product_data.get("category"),
        )

        prod_id = product_data.get("id")
        uuid_id = uuid.UUID(prod_id) if prod_id and isinstance(prod_id, str) and len(prod_id) == 36 else uuid.uuid4()

        product = Product(
            id=uuid_id,
            name=product_data["name"],
            sku=product_data["sku"],
            category_id=category_obj.id,
            price=product_data["price"],
            stock=product_data.get("stock", 0),
            units_sold=product_data.get("units_sold", 0),
            image_path=product_data.get("image_path"),
            description=product_data.get("description"),
            is_active=product_data.get("is_active", True),
        )
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return self._to_dict(product)

    def update(self, product_id: str, update_data: dict) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(product_id)
        except ValueError:
            return None

        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == val_uuid)
        )
        product = self.session.scalars(stmt).unique().first()
        if not product:
            return None

        if ("category_id" in update_data and update_data["category_id"]) or ("category" in update_data and update_data["category"]):
            cat_obj = self._resolve_category(
                category_id=update_data.get("category_id"),
                category_name=update_data.get("category"),
            )
            product.category_id = cat_obj.id

        for field in ["name", "sku", "price", "stock", "is_active"]:
            if field in update_data and update_data[field] is not None:
                setattr(product, field, update_data[field])

        for field in ["image_path", "description"]:
            if field in update_data:
                setattr(product, field, update_data[field])

        self.session.commit()
        self.session.refresh(product)
        return self._to_dict(product)

    def soft_delete(self, product_id: str) -> Optional[dict]:
        try:
            val_uuid = uuid.UUID(product_id)
        except ValueError:
            return None

        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == val_uuid)
        )
        product = self.session.scalars(stmt).unique().first()
        if not product:
            return None

        product.is_active = False
        self.session.commit()
        self.session.refresh(product)
        return self._to_dict(product)
