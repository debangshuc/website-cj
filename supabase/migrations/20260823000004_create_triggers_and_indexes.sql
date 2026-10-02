-- ============================================================================
-- Migration: 20260823000004_create_triggers_and_indexes.sql
-- Description: Create updated_at trigger and query performance indexes
-- ============================================================================

-- Function to automatically update updated_at timestamp on row change
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to maintain updated_at on public.products
DROP TRIGGER IF EXISTS set_products_updated_at ON public.products;
CREATE TRIGGER set_products_updated_at
    BEFORE UPDATE ON public.products
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_products_category_id ON public.products (category_id);
CREATE INDEX IF NOT EXISTS idx_products_is_active ON public.products (is_active);
CREATE INDEX IF NOT EXISTS idx_products_sku ON public.products (sku);
CREATE INDEX IF NOT EXISTS idx_sales_product_id ON public.sales (product_id);
CREATE INDEX IF NOT EXISTS idx_sales_sold_at ON public.sales (sold_at DESC);
