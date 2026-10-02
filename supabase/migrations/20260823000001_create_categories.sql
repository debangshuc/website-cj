-- ============================================================================
-- Migration: 20260823000001_create_categories.sql
-- Description: Create categories table for accessory inventory
-- ============================================================================

-- Ensure UUID extensions are enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create categories table
CREATE TABLE IF NOT EXISTS public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Documentation comments
COMMENT ON TABLE public.categories IS 'Product categories (Poster, Keychain, Sticker, Accessory)';
COMMENT ON COLUMN public.categories.id IS 'Unique category identifier (UUID)';
COMMENT ON COLUMN public.categories.name IS 'Unique category display name';
COMMENT ON COLUMN public.categories.created_at IS 'Timestamp of category creation';
