-- ============================================================================
-- Migration: 20260823000002_create_products.sql
-- Description: Create products table with domain constraints and soft delete
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    category_id UUID NOT NULL REFERENCES public.categories(id) ON DELETE RESTRICT,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    units_sold INTEGER NOT NULL DEFAULT 0 CHECK (units_sold >= 0),
    image_path TEXT NULL,
    description TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Documentation comments
COMMENT ON TABLE public.products IS 'Accessory inventory products catalog';
COMMENT ON COLUMN public.products.id IS 'Unique product identifier (UUID)';
COMMENT ON COLUMN public.products.name IS 'Display title of the product';
COMMENT ON COLUMN public.products.sku IS 'Unique product SKU identifier (e.g. PST-ANM-001)';
COMMENT ON COLUMN public.products.category_id IS 'Foreign key reference to categories.id (RESTRICT on delete)';
COMMENT ON COLUMN public.products.price IS 'Current product selling price in INR (must be >= 0)';
COMMENT ON COLUMN public.products.stock IS 'Available physical stock inventory (must be >= 0)';
COMMENT ON COLUMN public.products.units_sold IS 'Lifetime physical units sold count (must be >= 0)';
COMMENT ON COLUMN public.products.image_path IS 'Storage asset path or URL for product thumbnail';
COMMENT ON COLUMN public.products.description IS 'Optional detailed product description';
COMMENT ON COLUMN public.products.is_active IS 'Soft deletion flag (TRUE = active catalog item, FALSE = soft deleted)';
COMMENT ON COLUMN public.products.created_at IS 'Timestamp of product creation';
COMMENT ON COLUMN public.products.updated_at IS 'Timestamp of last product update';
