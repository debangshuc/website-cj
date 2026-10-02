-- ============================================================================
-- Migration: 20260901000001_add_category_description_and_is_active.sql
-- Description: Add description and is_active columns to categories table
-- ============================================================================

ALTER TABLE public.categories 
ADD COLUMN IF NOT EXISTS description TEXT NULL;

ALTER TABLE public.categories 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE public.categories 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Create index on is_active for faster active-category filtering
CREATE INDEX IF NOT EXISTS idx_categories_is_active ON public.categories (is_active);

-- Documentation comments
COMMENT ON COLUMN public.categories.description IS 'Optional detailed category description';
COMMENT ON COLUMN public.categories.is_active IS 'Active status flag (TRUE = active, FALSE = deactivated)';
COMMENT ON COLUMN public.categories.updated_at IS 'Timestamp of last category update';
