-- ============================================================================
-- Migration: 20260901000002_create_orders_and_order_items.sql
-- Description: Create orders, order_items tables and link sales to orders
-- ============================================================================

-- 1. Create orders table
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number TEXT NOT NULL UNIQUE,
    customer_name TEXT NULL,
    customer_email TEXT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled')),
    subtotal NUMERIC(10, 2) NOT NULL CHECK (subtotal >= 0),
    total NUMERIC(10, 2) NOT NULL CHECK (total >= 0),
    notes TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Create order_items table
CREATE TABLE IF NOT EXISTS public.order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE RESTRICT,
    product_id UUID NOT NULL REFERENCES public.products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    line_total NUMERIC(10, 2) NOT NULL CHECK (line_total >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Add order reference columns to sales table with idempotency unique constraint
ALTER TABLE public.sales
ADD COLUMN IF NOT EXISTS order_id UUID NULL REFERENCES public.orders(id) ON DELETE SET NULL;

ALTER TABLE public.sales
ADD COLUMN IF NOT EXISTS order_item_id UUID NULL UNIQUE REFERENCES public.order_items(id) ON DELETE SET NULL;

-- 4. Create Indexes
CREATE INDEX IF NOT EXISTS idx_orders_status ON public.orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON public.orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON public.orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON public.order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON public.order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_order_id ON public.sales(order_id);
CREATE INDEX IF NOT EXISTS idx_sales_order_item_id ON public.sales(order_item_id);

-- 5. Documentation comments
COMMENT ON TABLE public.orders IS 'Customer order lifecycle management';
COMMENT ON COLUMN public.orders.order_number IS 'Human-readable unique order identifier (e.g. ORD-20260901-A1B2)';
COMMENT ON COLUMN public.orders.status IS 'Order state: pending, confirmed, completed, cancelled';
COMMENT ON TABLE public.order_items IS 'Snapshot line items associated with an order';
COMMENT ON COLUMN public.sales.order_item_id IS 'Unique link to order item ensuring idempotent sale ledger generation';
