# 📸 Manual Testing Guide - Media Upload & Storage

**Story 10: Media Upload**  
**Purpose:** Test upload/delete for photos, videos, avatars  
**Prerequisites:** 
- Server running (`python main.py`)
- Supabase Storage buckets created (run `010_storage_buckets.sql`)
- JWT token from login

---

## 🔐 Step 1: Get JWT Token

First, login to get an authentication token:

```bash
# Login with test user
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "user": { ... }
}
```

**Action:** Copy the `access_token` value. We'll use it as `$TOKEN` below.

---

## 📷 Test 1: Upload Photo (Success)

### Prepare Test Image

```bash
# Create a small test image (1KB)
echo "fake_image_data" > test_photo.jpg
```

### Upload Photo

```bash
curl -X POST "http://localhost:8000/api/v1/media/upload?type=photo" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_photo.jpg"
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "url": "https://xxx.supabase.co/storage/v1/object/public/darezone-photos/user-id/uuid.jpg",
  "filename": "user-id/uuid.jpg",
  "size": 1024,
  "type": "photo",
  "bucket": "darezone-photos"
}
```

**✅ Verify:**
- Response status is 200
- `url` is accessible (open in browser)
- `bucket` is "darezone-photos"
- `filename` starts with your user_id

---

## 🎥 Test 2: Upload Video (Success)

### Prepare Test Video

```bash
# Create a small test video (1KB)
echo "fake_video_data" > test_video.mp4
```

### Upload Video

```bash
curl -X POST "http://localhost:8000/api/v1/media/upload?type=video" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_video.mp4"
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "url": "https://xxx.supabase.co/storage/v1/object/public/darezone-videos/user-id/uuid.mp4",
  "filename": "user-id/uuid.mp4",
  "size": 1024,
  "type": "video",
  "bucket": "darezone-videos"
}
```

**✅ Verify:**
- Bucket is "darezone-videos"
- File extension is .mp4

---

## 🧑 Test 3: Upload Avatar (Success)

### Upload Avatar

```bash
curl -X POST "http://localhost:8000/api/v1/media/upload?type=avatar" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_photo.jpg"
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "url": "https://xxx.supabase.co/storage/v1/object/public/darezone-avatars/user-id/uuid.jpg",
  "bucket": "darezone-avatars",
  ...
}
```

**✅ Verify:**
- Bucket is "darezone-avatars"

---

## ❌ Test 4: Upload Without Auth (Should Fail)

```bash
curl -X POST "http://localhost:8000/api/v1/media/upload?type=photo" \
  -F "file=@test_photo.jpg"
```

**Expected Response (401 or 403):**
```json
{
  "detail": "Not authenticated" 
}
```

**✅ Verify:** Request is rejected

---

## ❌ Test 5: Upload File Too Large (Should Fail)

### Create Large File

```bash
# Create 12MB file (exceeds 10MB limit for photos)
dd if=/dev/zero of=large_photo.jpg bs=1M count=12
```

### Attempt Upload

```bash
curl -X POST "http://localhost:8000/api/v1/media/upload?type=photo" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@large_photo.jpg"
```

**Expected Response (400 Bad Request):**
```json
{
  "detail": {
    "error": "File too large",
    "max_size_mb": 10,
    "actual_size_mb": 12.0
  }
}
```

**✅ Verify:** 
- Status is 400
- Error message mentions file size

---

## ❌ Test 6: Upload Invalid File Type (Should Fail)

### Create Text File

```bash
echo "This is text" > test_file.txt
```

### Attempt Upload

```bash
curl -X POST "http://localhost:8000/api/v1/media/upload?type=photo" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_file.txt"
```

**Expected Response (400 Bad Request):**
```json
{
  "detail": {
    "error": "Invalid image type",
    "allowed_types": ["image/jpeg", "image/jpg", "image/png", "image/webp"],
    "received": "text/plain"
  }
}
```

**✅ Verify:**
- Status is 400
- Error lists allowed types

---

## 🗑️ Test 7: Delete Own File (Success)

### Get File URL

From a previous upload, copy the `url` value. Example:
```
https://xxx.supabase.co/storage/v1/object/public/darezone-photos/user-id/uuid.jpg
```

### Delete File

```bash
curl -X DELETE "http://localhost:8000/api/v1/media?url=YOUR_FILE_URL_HERE" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "message": "File deleted successfully",
  "bucket": "darezone-photos",
  "path": "user-id/uuid.jpg"
}
```

**✅ Verify:**
- Status is 200
- File is no longer accessible (404 if you visit URL)

---

## ❌ Test 8: Delete Other User's File (Should Fail)

Attempt to delete a file that belongs to another user:

```bash
# URL with different user_id
curl -X DELETE "http://localhost:8000/api/v1/media?url=https://xxx.supabase.co/storage/v1/object/public/darezone-photos/other-user-id/file.jpg" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (403 Forbidden):**
```json
{
  "detail": "You can only delete your own files"
}
```

**✅ Verify:**
- Status is 403
- Error message about ownership

---

## ❌ Test 9: Delete Invalid URL (Should Fail)

```bash
curl -X DELETE "http://localhost:8000/api/v1/media?url=https://invalid-url.com/file.jpg" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (400 Bad Request):**
```json
{
  "detail": "Invalid storage URL format"
}
```

**✅ Verify:** Status is 400

---

## ❌ Test 10: Delete Without Auth (Should Fail)

```bash
curl -X DELETE "http://localhost:8000/api/v1/media?url=https://xxx.supabase.co/storage/v1/object/public/darezone-photos/user-id/file.jpg"
```

**Expected Response (401 or 403):**
```json
{
  "detail": "Not authenticated"
}
```

**✅ Verify:** Request is rejected

---

## 📊 Test Summary Checklist

After running all tests, verify:

- [x] Photo upload works (10MB limit)
- [x] Video upload works (50MB limit)
- [x] Avatar upload works (5MB limit)
- [x] Public URLs are accessible
- [x] Files rejected without auth
- [x] Large files rejected (>10MB photos)
- [x] Invalid file types rejected (txt, pdf, etc.)
- [x] Users can delete own files
- [x] Users cannot delete others' files
- [x] Invalid URLs rejected

---

## 🐞 Troubleshooting

### Issue: "Upload failed: Bucket not found"

**Cause:** Storage buckets not created

**Solution:**
```bash
# Run migration in Supabase SQL Editor
cat docs/migrations/010_storage_buckets.sql
# Copy & paste into Supabase, run
```

---

### Issue: "403 Forbidden" on upload

**Cause:** RLS policies not applied

**Solution:** Check Supabase Dashboard → Storage → Policies. Should see:
- "Users can upload photos"
- "Users can upload videos"
- "Users can upload avatars"

---

### Issue: File uploads but URL returns 404

**Cause:** Bucket not set to public

**Solution:** 
```sql
UPDATE storage.buckets 
SET public = true 
WHERE id IN ('darezone-photos', 'darezone-videos', 'darezone-avatars');
```

---

### Issue: Cannot delete file

**Cause:** File path doesn't match user_id

**Solution:** Verify file path starts with your user_id:
```
✅ Correct: user-123/abc.jpg
❌ Wrong: abc.jpg
```

---

## 🎯 Integration Test: Upload + Use in Check-in

### 1. Upload Photo

```bash
curl -X POST "http://localhost:8000/api/v1/media/upload?type=photo" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_photo.jpg"
```

**Save the `url` from response.**

### 2. Create Check-in with Photo

```bash
curl -X POST "http://localhost:8000/api/v1/checkins" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id": "your-challenge-id",
    "habit_id": "your-habit-id",
    "photo_url": "URL_FROM_STEP_1",
    "evidence_text": "Completed today!"
  }'
```

**✅ Verify:** Check-in created with photo_url

### 3. Update Profile Avatar

```bash
curl -X PUT "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "avatar_url": "AVATAR_URL_FROM_UPLOAD"
  }'
```

**✅ Verify:** Profile updated with new avatar

---

## 📱 Mobile App Testing

### React Native Upload Example

```typescript
const uploadPhoto = async (fileUri: string) => {
  const formData = new FormData();
  formData.append('file', {
    uri: fileUri,
    type: 'image/jpeg',
    name: 'photo.jpg',
  });

  const response = await fetch(
    'http://localhost:8000/api/v1/media/upload?type=photo',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    }
  );

  const data = await response.json();
  console.log('Uploaded URL:', data.url);
  return data.url;
};
```

---

## ✅ Story 10 Complete!

All media upload endpoints tested and working:
- ✅ Upload photos (max 10MB)
- ✅ Upload videos (max 50MB)
- ✅ Upload avatars (max 5MB)
- ✅ File validation (type & size)
- ✅ Delete with ownership check
- ✅ Public URLs accessible
- ✅ Integration with check-ins & profiles

**Next:** Story 11 - Hitch System 🚀
