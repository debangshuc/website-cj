from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from app.schemas.sale import SaleCreate, SaleResponse
from app.repositories.product_repository import ProductRepositoryProtocol, product_repository
from app.repositories.sales_repository import SalesRepositoryProtocol, sales_repository
from app.repositories.postgres_sales_repository import PostgresSalesRepository


class SalesService:
    def __init__(
        self,
        sales_repo: SalesRepositoryProtocol = sales_repository,
        product_repo: ProductRepositoryProtocol = product_repository,
    ):
        self.sales_repo = sales_repo
        self.product_repo = product_repo

    def list_sales(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        date_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[SaleResponse]:
        raw_sales = self.sales_repo.get_all(
            search=search,
            category=category,
            date_filter=date_filter,
            sort_by=sort_by,
        )
        return [SaleResponse(**s) for s in raw_sales]

    def get_sale(self, sale_id: str) -> SaleResponse:
        raw_sale = self.sales_repo.get_by_id(sale_id)
        if not raw_sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sale with ID '{sale_id}' not found.",
            )
        return SaleResponse(**raw_sale)

    def record_sale(self, sale_in: SaleCreate) -> SaleResponse:
        # If using Postgres repository, the complete transaction & row-lock is owned by the repository
        if isinstance(self.sales_repo, PostgresSalesRepository):
            sale_data = {
                "product_id": sale_in.product_id,
                "quantity": sale_in.quantity,
                "unit_price": sale_in.unit_price,
            }
            if sale_in.sold_at:
                sale_data["sold_at"] = sale_in.sold_at
            created_sale = self.sales_repo.create(sale_data)
            return SaleResponse(**created_sale)

        # In-Memory fallback implementation for unit tests
        product = self.product_repo.get_by_id(sale_in.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{sale_in.product_id}' not found.",
            )

        if sale_in.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0.",
            )

        available_stock = product.get("stock", 0)
        if sale_in.quantity > available_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {available_stock} units are currently available.",
            )

        total = Decimal(sale_in.quantity) * sale_in.unit_price
        self.product_repo.adjust_inventory(sale_in.product_id, sale_in.quantity)

        sale_data = {
            "product_id": product["id"],
            "product_name": product["name"],
            "category": product["category"],
            "quantity": sale_in.quantity,
            "unit_price": sale_in.unit_price,
            "total": total,
        }
        if sale_in.sold_at:
            sale_data["sold_at"] = sale_in.sold_at

        created_sale = self.sales_repo.create(sale_data)
        return SaleResponse(**created_sale)


# Default singleton service instance
sales_service = SalesService()
