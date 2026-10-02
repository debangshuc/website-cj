-- ============================================================================
-- Migration: 20260901000003_create_customers_and_link_orders.sql
-- Description: Create customers table and link orders.customer_id
-- ============================================================================

-- 1. Create customers table
CREATE TABLE IF NOT EXISTS public.customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NULL UNIQUE,
    phone TEXT NULL,
    address TEXT NULL,
    notes TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Alter orders table to add nullable customer_id foreign key with RESTRICT deletion
ALTER TABLE public.orders
ADD COLUMN IF NOT EXISTS customer_id UUID NULL REFERENCES public.customers(id) ON DELETE RESTRICT;

-- 3. Create Indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON public.customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_is_active ON public.customers(is_active);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON public.customers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON public.orders(customer_id);

-- 4. Documentation comments
COMMENT ON TABLE public.customers IS 'Operational CRM customer records';
COMMENT ON COLUMN public.customers.name IS 'Customer display name';
COMMENT ON COLUMN public.customers.email IS 'Unique contact email (case-insensitive normalized)';
COMMENT ON COLUMN public.customers.is_active IS 'Soft-delete status indicator';
COMMENT ON COLUMN public.orders.customer_id IS 'Nullable link to Customer entity; snapshot name and email remain preserved on Order';
