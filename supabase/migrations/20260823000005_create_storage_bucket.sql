-- ============================================================================
-- Migration: 20260823000005_create_storage_bucket.sql
-- Description: Create public product-images storage bucket with size/type constraints
-- ============================================================================

-- Create product-images bucket in Supabase storage schema
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'product-images',
    'product-images',
    true,
    5242880, -- 5 MB limit
    ARRAY['image/jpeg', 'image/png', 'image/webp']
)
ON CONFLICT (id) DO UPDATE SET
    public = true,
    file_size_limit = 5242880,
    allowed_mime_types = ARRAY['image/jpeg', 'image/png', 'image/webp'];

-- Enable RLS and create public read policy for product images
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'storage' AND tablename = 'objects' AND policyname = 'Public Access for Product Images'
    ) THEN
        CREATE POLICY "Public Access for Product Images"
        ON storage.objects FOR SELECT
        USING (bucket_id = 'product-images');
    END IF;
END $$;
