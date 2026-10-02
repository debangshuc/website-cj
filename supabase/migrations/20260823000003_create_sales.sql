-- ============================================================================
-- Migration: 20260823000003_create_sales.sql
-- Description: Create sales table for transactions ledger
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.sales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES public.products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    total NUMERIC(10, 2) NOT NULL CHECK (total >= 0),
    sold_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT check_sales_total_calculation CHECK (total = (quantity * unit_price))
);

-- Documentation comments
COMMENT ON TABLE public.sales IS 'Individual sales transactions and historical inventory ledger';
COMMENT ON COLUMN public.sales.id IS 'Unique sales transaction identifier (UUID)';
COMMENT ON COLUMN public.sales.product_id IS 'Foreign key reference to products.id (RESTRICT on delete)';
COMMENT ON COLUMN public.sales.quantity IS 'Number of physical units sold in this transaction (must be > 0)';
COMMENT ON COLUMN public.sales.unit_price IS 'Historical unit price at transaction time in INR';
COMMENT ON COLUMN public.sales.total IS 'Total transaction revenue (quantity * unit_price)';
COMMENT ON COLUMN public.sales.sold_at IS 'Historical sale timestamp';
COMMENT ON COLUMN public.sales.created_at IS 'Record creation timestamp';
