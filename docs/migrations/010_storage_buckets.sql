-- =====================================================
-- Migration: 010 - Supabase Storage Buckets
-- Story: Story 10 - Media Upload & Storage
-- Purpose: Create storage buckets for photos, videos, avatars
-- =====================================================

-- =====================================================
-- 1. Create Storage Buckets
-- =====================================================

INSERT INTO storage.buckets (id, name, public)
VALUES 
  ('darezone-photos', 'darezone-photos', true),
  ('darezone-videos', 'darezone-videos', true),
  ('darezone-avatars', 'darezone-avatars', true)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 2. Storage Policies - Photos
-- =====================================================

-- Users can upload photos (authenticated users only)
CREATE POLICY "Users can upload photos"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'darezone-photos'
  AND auth.role() = 'authenticated'
);

-- Anyone can view photos (public bucket)
CREATE POLICY "Photos are publicly accessible"
ON storage.objects FOR SELECT
USING (bucket_id = 'darezone-photos');

-- Users can only delete their own photos
-- Path structure: {user_id}/{filename}
CREATE POLICY "Users can delete own photos"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'darezone-photos'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can only update their own photos
CREATE POLICY "Users can update own photos"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'darezone-photos'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- =====================================================
-- 3. Storage Policies - Videos
-- =====================================================

-- Users can upload videos
CREATE POLICY "Users can upload videos"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'darezone-videos'
  AND auth.role() = 'authenticated'
);

-- Anyone can view videos
CREATE POLICY "Videos are publicly accessible"
ON storage.objects FOR SELECT
USING (bucket_id = 'darezone-videos');

-- Users can only delete their own videos
CREATE POLICY "Users can delete own videos"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'darezone-videos'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can only update their own videos
CREATE POLICY "Users can update own videos"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'darezone-videos'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- =====================================================
-- 4. Storage Policies - Avatars
-- =====================================================

-- Users can upload avatars
CREATE POLICY "Users can upload avatars"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'darezone-avatars'
  AND auth.role() = 'authenticated'
);

-- Anyone can view avatars
CREATE POLICY "Avatars are publicly accessible"
ON storage.objects FOR SELECT
USING (bucket_id = 'darezone-avatars');

-- Users can only delete their own avatars
CREATE POLICY "Users can delete own avatars"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'darezone-avatars'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can only update their own avatars
CREATE POLICY "Users can update own avatars"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'darezone-avatars'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- =====================================================
-- 5. Verification Query
-- =====================================================

-- Check buckets created
SELECT id, name, public 
FROM storage.buckets 
WHERE id LIKE 'darezone-%'
ORDER BY name;

-- Check policies created (should see 12 policies total)
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE tablename = 'objects' 
  AND policyname LIKE '%photo%' 
  OR policyname LIKE '%video%'
  OR policyname LIKE '%avatar%'
ORDER BY policyname;
