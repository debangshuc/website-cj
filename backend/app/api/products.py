from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService
from app.services.storage_service import StorageServiceProtocol
from app.api.dependencies import require_admin, get_product_service, get_storage_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="List products",
    description="Retrieve all products with optional filters by search term, category, or stock status.",
)
def list_products(
    search: Optional[str] = Query(default=None, description="Search term for name, SKU, or category"),
    category: Optional[str] = Query(default=None, description="Filter by product category"),
    stock_status: Optional[str] = Query(
        default=None,
        description="Filter by stock status ('in_stock', 'low_stock', 'out_of_stock')",
    ),
    include_inactive: bool = Query(
        default=False,
        description="Whether to include soft-deleted/inactive products",
    ),
    service: ProductService = Depends(get_product_service),
) -> List[ProductResponse]:
    return service.list_products(
        search=search,
        category=category,
        stock_status=stock_status,
        include_inactive=include_inactive,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Retrieve a single product by its unique identifier.",
)
def get_product(
    product_id: str,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    return service.get_product(product_id)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new product and add it to the inventory catalog.",
)
def create_product(
    product_in: ProductCreate,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    return service.create_product(product_in)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product",
    description="Partially update an existing product's fields.",
)
def update_product(
    product_id: str,
    product_update: ProductUpdate,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    return service.update_product(product_id, product_update)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product (Soft delete)",
    description="Soft-delete a product by setting is_active=False. Preserves historical sales.",
)
def delete_product(
    product_id: str,
    service: ProductService = Depends(get_product_service),
) -> None:
    service.delete_product(product_id)


@router.post(
    "/{product_id}/image",
    response_model=ProductResponse,
    summary="Upload product image",
    description="Upload a product image to Supabase Storage and update the product's image_path.",
)
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(..., description="Image file (JPEG, PNG, or WebP up to 5MB)"),
    product_service: ProductService = Depends(get_product_service),
    storage_srv: StorageServiceProtocol = Depends(get_storage_service),
) -> ProductResponse:
    # 1. Verify product exists
    existing_product = product_service.get_product(product_id)

    # 2. Read file content
    file_bytes = await file.read()
    content_type = file.content_type or "image/png"
    filename = file.filename or f"image_{product_id}.png"

    # 3. Upload to storage (validates format and size)
    image_url = storage_srv.upload_file(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
        product_id=product_id,
    )

    # 4. Update product image_path in database
    old_image_path = existing_product.image_path
    updated_prod = product_service.update_product(
        product_id,
        ProductUpdate(image_path=image_url)
    )

    # 5. Clean up previously uploaded image if replaced
    if old_image_path and old_image_path != image_url and ("storage" in old_image_path or "supabase" in old_image_path):
        storage_srv.delete_file(old_image_path)

    return updated_prod


@router.delete(
    "/{product_id}/image",
    response_model=ProductResponse,
    summary="Delete product image",
    description="Delete a product's image from Supabase Storage and set image_path to null.",
)
def delete_product_image(
    product_id: str,
    product_service: ProductService = Depends(get_product_service),
    storage_srv: StorageServiceProtocol = Depends(get_storage_service),
) -> ProductResponse:
    existing_product = product_service.get_product(product_id)
    if existing_product.image_path and ("storage" in existing_product.image_path or "supabase" in existing_product.image_path):
        storage_srv.delete_file(existing_product.image_path)
    return product_service.update_product(
        product_id,
        ProductUpdate(image_path=None)
    )
