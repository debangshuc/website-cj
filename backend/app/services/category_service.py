from typing import List, Optional
from fastapi import HTTPException, status
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.repositories.category_repository import (
    CategoryRepositoryProtocol,
    category_repository,
)


class CategoryService:
    def __init__(self, repo: CategoryRepositoryProtocol = category_repository):
        self.repo = repo

    def list_categories(self, include_inactive: bool = False) -> List[CategoryResponse]:
        raw_cats = self.repo.get_all(include_inactive=include_inactive)
        return [CategoryResponse(**c) for c in raw_cats]

    def get_category(self, category_id: str) -> CategoryResponse:
        raw_cat = self.repo.get_by_id(category_id)
        if not raw_cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID '{category_id}' not found.",
            )
        return CategoryResponse(**raw_cat)

    def create_category(self, category_in: CategoryCreate) -> CategoryResponse:
        clean_name = category_in.name.strip()
        existing = self.repo.get_by_name(clean_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with name '{clean_name}' already exists.",
            )

        data = {
            "name": clean_name,
            "description": category_in.description,
            "is_active": True,
        }
        created = self.repo.create(data)
        return CategoryResponse(**created)

    def update_category(
        self, category_id: str, category_update: CategoryUpdate
    ) -> CategoryResponse:
        existing = self.repo.get_by_id(category_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID '{category_id}' not found.",
            )

        update_dict = category_update.model_dump(exclude_unset=True)
        if "name" in update_dict and update_dict["name"] is not None:
            new_name = update_dict["name"].strip()
            existing_with_name = self.repo.get_by_name(new_name)
            if existing_with_name and existing_with_name["id"] != category_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category with name '{new_name}' already exists.",
                )
            update_dict["name"] = new_name

        updated = self.repo.update(category_id, update_dict)
        return CategoryResponse(**updated)

    def delete_category(self, category_id: str) -> None:
        existing = self.repo.get_by_id(category_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID '{category_id}' not found.",
            )
        self.repo.delete(category_id)


category_service = CategoryService()
