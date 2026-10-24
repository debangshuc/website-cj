from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from app.schemas.order import (
    OrderCreate,
    OrderMetricsResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.repositories.order_repository import (
    OrderRepositoryProtocol,
    order_repository,
)
from app.repositories.product_repository import (
    ProductRepositoryProtocol,
    product_repository,
)
from app.repositories.sales_repository import (
    SalesRepositoryProtocol,
    sales_repository,
)
from app.repositories.customer_repository import (
    CustomerRepositoryProtocol,
    customer_repository,
)
from app.repositories.postgres_order_repository import PostgresOrderRepository
from app.repositories.postgres_product_repository import PostgresProductRepository
from app.repositories.postgres_sales_repository import PostgresSalesRepository


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepositoryProtocol = order_repository,
        product_repo: ProductRepositoryProtocol = product_repository,
        sales_repo: SalesRepositoryProtocol = sales_repository,
        customer_repo: CustomerRepositoryProtocol = customer_repository,
    ):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.sales_repo = sales_repo
        self.customer_repo = customer_repo

    def list_orders(
        self,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        date_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[OrderResponse]:
        raw_orders = self.order_repo.get_all(
            search=search,
            status=status_filter,
            date_filter=date_filter,
            sort_by=sort_by,
        )
        return [OrderResponse(**o) for o in raw_orders]

    def get_order(self, order_id: str) -> OrderResponse:
        raw_order = self.order_repo.get_by_id(order_id)
        if not raw_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID or number '{order_id}' not found.",
            )
        return OrderResponse(**raw_order)

    def get_metrics(self) -> OrderMetricsResponse:
        raw_metrics = self.order_repo.get_metrics()
        return OrderMetricsResponse(**raw_metrics)

    def create_order(self, order_in: OrderCreate) -> OrderResponse:
        if not order_in.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must contain at least one item.",
            )

        # Handle Customer Resolution & Snapshotting
        customer_id = None
        customer_name = order_in.customer_name.strip() if order_in.customer_name else None
        customer_email = order_in.customer_email.strip().lower() if order_in.customer_email else None

        if order_in.customer_id:
            customer = self.customer_repo.get_by_id(order_in.customer_id)
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer with ID '{order_in.customer_id}' not found.",
                )
            if not customer.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot create order for inactive customer '{customer.get('name')}'.",
                )
            customer_id = customer["id"]
            # Authoritative snapshot from customer entity
            customer_name = customer["name"]
            customer_email = customer.get("email")

        items_to_create = []
        subtotal = Decimal("0.00")

        # 1. Validate all products and stock availability authoritatively before mutating
        for item in order_in.items:
            product = self.product_repo.get_by_id(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID '{item.product_id}' not found.",
                )

            if not product.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot create order for inactive product '{product.get('name')}'.",
                )

            available_stock = product.get("stock", 0)
            if item.quantity > available_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient inventory for '{product.get('name')}'. Only {available_stock} units available.",
                )

            authoritative_unit_price = Decimal(str(product["price"]))
            line_total = Decimal(item.quantity) * authoritative_unit_price
            subtotal += line_total

            items_to_create.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "sku": product["sku"],
                "category": product.get("category", "Accessory"),
                "quantity": item.quantity,
                "unit_price": authoritative_unit_price,
                "line_total": line_total,
            })

        # 3. Create the order record in pending state
        order_data = {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "status": "pending",
            "subtotal": subtotal,
            "total": subtotal,
            "notes": order_in.notes.strip() if order_in.notes else None,
        }

        # 4. Atomic write: reserve inventory AND create the order + line items in
        #    one transaction. If anything fails, every change rolls back.
        if self._is_postgres_transactional():
            try:
                # Consistent lock ordering by product id reduces deadlock risk
                # across concurrent multi-item orders.
                for item_data in sorted(items_to_create, key=lambda i: str(i["product_id"])):
                    self.product_repo.adjust_inventory(
                        item_data["product_id"], item_data["quantity"], commit=False
                    )
                created = self.order_repo.create(order_data, items_to_create, commit=False)
                self.order_repo.commit()
            except HTTPException:
                self.order_repo.rollback()
                raise
            except Exception as exc:
                self.order_repo.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create order: {str(exc)}",
                )
        else:
            # In-memory repositories (unit testing): single-threaded writes.
            for item_data in items_to_create:
                self.product_repo.adjust_inventory(item_data["product_id"], item_data["quantity"])
            created = self.order_repo.create(order_data, items_to_create)

        return OrderResponse(**created)

    def update_order_status(self, order_id: str, status_update: OrderStatusUpdate) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID '{order_id}' not found.",
            )

        current_status = order["status"].lower()
        target_status = status_update.status.lower()

        # Idempotent no-op if already in target status
        if current_status == target_status:
            return OrderResponse(**order)

        # Terminal state protection
        if current_status in ["completed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition order in terminal '{current_status}' state.",
            )

        # State Machine Transitions
        valid_transitions = {
            "pending": ["confirmed", "cancelled"],
            "confirmed": ["completed", "cancelled"],
        }

        if target_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from '{current_status}' to '{target_status}'.",
            )

        if self._is_postgres_transactional():
            # Atomic Postgres path: claim the status transition conditionally and
            # apply its side effects (inventory restore / sale records) in one
            # transaction owned by the service.
            updated_order = self._transition_status_postgres(order, current_status, target_status)
            return OrderResponse(**updated_order)

        # Handle Side Effects:
        # A) Cancellation -> Restore reserved inventory
        if target_status == "cancelled":
            for item in order.get("items", []):
                prod_id = item["product_id"]
                qty = item["quantity"]
                # Negative quantity in adjust_inventory adds stock back
                self.product_repo.adjust_inventory(prod_id, -qty)

        # B) Completion -> Idempotently generate Sale records (stock is NOT decremented again)
        elif target_status == "completed":
            for item in order.get("items", []):
                prod = self.product_repo.get_by_id(item["product_id"])
                prod_name = item.get("product_name") or (prod["name"] if prod else "Product")
                cat_name = item.get("category") or (prod.get("category") if prod else "Accessory")
                sale_payload = {
                    "product_id": item["product_id"],
                    "product_name": prod_name,
                    "category": cat_name,
                    "order_id": order["id"],
                    "order_item_id": item.get("id"),
                    "quantity": item["quantity"],
                    "unit_price": Decimal(str(item["unit_price"])),
                    "total": Decimal(str(item["line_total"])),
                }
                # Create sale record for analytics
                self.sales_repo.create(sale_payload)

        updated_order = self.order_repo.update_status(order["id"], target_status)
        return OrderResponse(**updated_order)

    def _is_postgres_transactional(self) -> bool:
        return (
            isinstance(self.order_repo, PostgresOrderRepository)
            and isinstance(self.product_repo, PostgresProductRepository)
            and isinstance(self.sales_repo, PostgresSalesRepository)
        )

    def _transition_status_postgres(self, order: dict, current_status: str, target_status: str) -> dict:
        """
        Claim the status transition atomically, then apply side effects and
        commit everything together. A conditional UPDATE (WHERE status =
        current_status) guarantees duplicate or concurrent lifecycle requests
        act exactly once: only the winner proceeds to restore inventory or
        record sales; the loser either gets an idempotent result or a 409.
        Failures roll back the status change together with all side effects.
        """
        order_id = str(order["id"])
        try:
            claimed = self.order_repo.try_update_status(
                order_id, current_status, target_status, commit=False
            )
            if not claimed:
                # Another request modified this row concurrently.
                refreshed = self.order_repo.get_by_id(order_id)
                if refreshed and refreshed["status"].lower() == target_status:
                    return refreshed
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Order '{order_id}' was modified concurrently. Reload and retry.",
                )

            # A) Cancellation -> Restore reserved inventory exactly once.
            if target_status == "cancelled":
                for item in sorted(order.get("items", []), key=lambda i: str(i["product_id"])):
                    self.product_repo.adjust_inventory(
                        item["product_id"], -int(item["quantity"]), commit=False
                    )

            # B) Completion -> Idempotently record sales; stock was already
            #    reserved at order creation and is NOT decremented again.
            elif target_status == "completed":
                for item in order.get("items", []):
                    sale_payload = {
                        "product_id": item["product_id"],
                        "product_name": item.get("product_name", "Product"),
                        "category": item.get("category", "Accessory"),
                        "order_id": order_id,
                        "order_item_id": item.get("id"),
                        "quantity": item["quantity"],
                        "unit_price": Decimal(str(item["unit_price"])),
                        "total": Decimal(str(item["line_total"])),
                    }
                    self.sales_repo.create(sale_payload, commit=False)

            self.order_repo.commit()
            return self.order_repo.get_by_id(order_id)

        except HTTPException:
            self.order_repo.rollback()
            raise
        except Exception as exc:
            self.order_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update order status: {str(exc)}",
            )


order_service = OrderService()
