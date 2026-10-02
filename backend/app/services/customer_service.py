from typing import List, Optional
from fastapi import HTTPException, status
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerMetricsResponse,
    CustomerOrderSummary,
    CustomerResponse,
    CustomerUpdate,
)
from app.repositories.customer_repository import (
    CustomerRepositoryProtocol,
    customer_repository,
)


class CustomerService:
    def __init__(self, repo: CustomerRepositoryProtocol = customer_repository):
        self.repo = repo

    def list_customers(
        self,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> List[CustomerResponse]:
        raw_customers = self.repo.get_all(
            search=search,
            status=status_filter,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )
        return [CustomerResponse(**c) for c in raw_customers]

    def get_customer(self, customer_id: str) -> CustomerDetailResponse:
        raw_cust = self.repo.get_by_id(customer_id)
        if not raw_cust:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID '{customer_id}' not found.",
            )

        recent_orders = self.repo.get_customer_orders(customer_id)
        return CustomerDetailResponse(
            **raw_cust,
            recent_orders=[CustomerOrderSummary(**o) for o in recent_orders],
        )

    def get_metrics(self) -> CustomerMetricsResponse:
        raw_metrics = self.repo.get_metrics()
        return CustomerMetricsResponse(**raw_metrics)

    def create_customer(self, customer_in: CustomerCreate) -> CustomerResponse:
        # Check email uniqueness if email provided
        if customer_in.email:
            existing = self.repo.get_by_email(customer_in.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A customer with email '{customer_in.email}' already exists.",
                )

        created = self.repo.create(customer_in.model_dump())
        return CustomerResponse(**created)

    def update_customer(self, customer_id: str, customer_in: CustomerUpdate) -> CustomerResponse:
        existing = self.repo.get_by_id(customer_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID '{customer_id}' not found.",
            )

        update_dict = customer_in.model_dump(exclude_unset=True)

        # Check email conflict if email changed
        new_email = update_dict.get("email")
        if new_email and new_email.lower() != (existing.get("email") or "").lower():
            conflict = self.repo.get_by_email(new_email)
            if conflict and conflict["id"] != customer_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A customer with email '{new_email}' already exists.",
                )

        updated = self.repo.update(customer_id, update_dict)
        return CustomerResponse(**updated)


customer_service = CustomerService()
