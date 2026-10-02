from typing import List, Optional
from fastapi import HTTPException, status
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.repositories.product_repository import ProductRepositoryProtocol, product_repository
from app.repositories.category_repository import CategoryRepositoryProtocol, category_repository


class ProductService:
    def __init__(
        self,
        repo: ProductRepositoryProtocol = product_repository,
        category_repo: CategoryRepositoryProtocol = category_repository,
    ):
        self.repo = repo
        self.category_repo = category_repo

    def _resolve_and_validate_category(
        self, category_id: Optional[str] = None, category_name: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Validates category exists and is active.
        Returns tuple of (category_id, category_name).
        """
        if category_id:
            cat = self.category_repo.get_by_id(category_id)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID '{category_id}' not found.",
                )
            if not cat.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot assign inactive category '{cat.get('name')}' to a product.",
                )
            return cat["id"], cat["name"]

        clean_name = (category_name or "Accessory").strip()
        cat = self.category_repo.get_by_name(clean_name)
        if cat:
            if not cat.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot assign inactive category '{cat.get('name')}' to a product.",
                )
            return cat["id"], cat["name"]

        # Create new active category if not present
        new_cat = self.category_repo.create({"name": clean_name, "is_active": True})
        return new_cat["id"], new_cat["name"]

    def list_products(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        stock_status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[ProductResponse]:
        raw_products = self.repo.get_all(
            search=search,
            category=category,
            stock_status=stock_status,
            include_inactive=include_inactive,
        )
        return [ProductResponse(**p) for p in raw_products]

    def get_product(self, product_id: str) -> ProductResponse:
        raw_product = self.repo.get_by_id(product_id)
        if not raw_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found.",
            )
        return ProductResponse(**raw_product)

    def create_product(self, product_in: ProductCreate) -> ProductResponse:
        data = product_in.model_dump()
        resolved_cat_id, resolved_cat_name = self._resolve_and_validate_category(
            category_id=data.get("category_id"),
            category_name=data.get("category"),
        )
        data["category_id"] = resolved_cat_id
        data["category"] = resolved_cat_name

        created_raw = self.repo.create(data)
        return ProductResponse(**created_raw)

    def update_product(self, product_id: str, product_update: ProductUpdate) -> ProductResponse:
        existing = self.repo.get_by_id(product_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found.",
            )

        update_data = product_update.model_dump(exclude_unset=True)
        if "category_id" in update_data or "category" in update_data:
            resolved_cat_id, resolved_cat_name = self._resolve_and_validate_category(
                category_id=update_data.get("category_id"),
                category_name=update_data.get("category"),
            )
            update_data["category_id"] = resolved_cat_id
            update_data["category"] = resolved_cat_name

        updated_raw = self.repo.update(product_id, update_data)
        return ProductResponse(**updated_raw)

    def delete_product(self, product_id: str) -> None:
        existing = self.repo.get_by_id(product_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found.",
            )
        self.repo.soft_delete(product_id)


# Default singleton service instance
product_service = ProductService()
