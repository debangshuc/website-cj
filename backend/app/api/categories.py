from typing import List
from fastapi import APIRouter, Depends, Query, status
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService
from app.api.dependencies import require_admin, get_category_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get(
    "",
    response_model=List[CategoryResponse],
    summary="List categories",
    description="Retrieve product categories with optional inclusion of inactive categories and aggregated product counts.",
)
def list_categories(
    include_inactive: bool = Query(
        default=False,
        description="Whether to include deactivated categories",
    ),
    service: CategoryService = Depends(get_category_service),
) -> List[CategoryResponse]:
    return service.list_categories(include_inactive=include_inactive)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
    description="Retrieve a single category by its unique ID.",
)
def get_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    return service.get_category(category_id)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Create a new product category entity with unique name and optional description.",
)
def create_category(
    category_in: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    return service.create_category(category_in)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category",
    description="Partially update an existing category's name, description, or active status.",
)
def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    return service.update_category(category_id, category_update)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete / Deactivate category",
    description="Deactivate a category if referenced by products, or hard delete if unused.",
)
def delete_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
) -> None:
    service.delete_category(category_id)
