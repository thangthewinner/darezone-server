# Story 10: Media Upload & Storage

**Phase:** 2 - Social Features  
**Points:** 3 (3 days)  
**Priority:** 🟡 MEDIUM  
**Dependencies:** [Story 9: Notifications](./story-9-notifications.md)

---

## 📖 Description

Implement media upload to Supabase Storage for photos, videos, và avatars với validation và size limits.

---

## 🎯 Goals

- [ ] Photos uploaded to Supabase Storage
- [ ] Videos uploaded với size limit
- [ ] Avatars handled separately
- [ ] File validation (type, size)
- [ ] Public URLs returned

---

## ✅ Acceptance Criteria

### 1. Upload Endpoints
- [ ] `POST /media/upload` - Upload photo/video/avatar
- [ ] Validates file type (jpg, png, mp4, mov)
- [ ] Validates file size (10MB photos, 50MB videos)
- [ ] Returns public URL
- [ ] Stores in appropriate bucket

### 2. Storage Buckets
- [ ] `darezone-photos` bucket created
- [ ] `darezone-videos` bucket created
- [ ] `darezone-avatars` bucket created
- [ ] Public access configured
- [ ] Storage policies set

### 3. File Management
- [ ] `DELETE /media` - Delete file by URL
- [ ] Only owner can delete
- [ ] Orphaned files cleanup (optional)

### 4. Integration
- [ ] Check-ins use uploaded photo/video URLs
- [ ] Profile updates use uploaded avatar URLs
- [ ] URLs work in mobile app

---

## 🛠️ Implementation

### Setup Storage Buckets

```sql
-- Run in Supabase SQL Editor

-- Create buckets
INSERT INTO storage.buckets (id, name, public)
VALUES 
  ('darezone-photos', 'darezone-photos', true),
  ('darezone-videos', 'darezone-videos', true),
  ('darezone-avatars', 'darezone-avatars', true);

-- Storage policies
CREATE POLICY "Users can upload photos"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'darezone-photos'
  AND auth.role() = 'authenticated'
);

CREATE POLICY "Users can delete own photos"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'darezone-photos'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Similar for videos and avatars
```

### app/api/v1/media.py

```python
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from supabase import Client
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.core.config import settings
import uuid
from typing import Literal

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo"}
MAX_IMAGE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024  # 50MB

@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    type: Literal["photo", "video", "avatar"] = Query(...),
    current_user = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Upload media to Supabase Storage
    
    - photo: max 10MB, jpg/png
    - video: max 50MB, mp4/mov
    - avatar: max 5MB, jpg/png
    """
    # Validate file type
    if type in ["photo", "avatar"]:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(400, f"Invalid image type. Allowed: {ALLOWED_IMAGE_TYPES}")
        max_size = MAX_IMAGE_SIZE if type == "photo" else 5 * 1024 * 1024
    elif type == "video":
        if file.content_type not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(400, f"Invalid video type. Allowed: {ALLOWED_VIDEO_TYPES}")
        max_size = MAX_VIDEO_SIZE
    else:
        raise HTTPException(400, "Invalid type")
    
    # Read file
    contents = await file.read()
    
    # Validate size
    if len(contents) > max_size:
        raise HTTPException(400, f"File too large. Max: {max_size / 1024 / 1024}MB")
    
    # Generate unique filename
    ext = file.filename.split('.')[-1]
    filename = f"{current_user['id']}/{uuid.uuid4()}.{ext}"
    
    # Determine bucket
    bucket = f"darezone-{type}s" if type != "avatar" else "darezone-avatars"
    
    # Upload to Supabase Storage
    try:
        result = supabase.storage.from_(bucket).upload(
            filename,
            contents,
            {
                "content-type": file.content_type,
                "cache-control": "3600"
            }
        )
        
        # Get public URL
        public_url = supabase.storage.from_(bucket).get_public_url(filename)
        
        return {
            "success": True,
            "url": public_url,
            "filename": filename,
            "size": len(contents),
            "type": type
        }
        
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.delete("")
async def delete_media(
    url: str = Query(...),
    current_user = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete media file"""
    # Extract bucket and path from URL
    # URL format: https://xxx.supabase.co/storage/v1/object/public/bucket/path
    try:
        parts = url.split('/storage/v1/object/public/')
        if len(parts) != 2:
            raise ValueError("Invalid URL format")
        
        bucket_and_path = parts[1].split('/', 1)
        bucket = bucket_and_path[0]
        path = bucket_and_path[1]
        
        # Verify ownership (path starts with user_id)
        if not path.startswith(current_user['id']):
            raise HTTPException(403, "Not your file")
        
        # Delete from storage
        supabase.storage.from_(bucket).remove([path])
        
        return {"success": True, "message": "File deleted"}
        
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {str(e)}")
```

### Update config

```python
# app/core/config.py
class Settings(BaseSettings):
    # ... existing ...
    
    # Storage
    STORAGE_BUCKET_PHOTOS: str = "darezone-photos"
    STORAGE_BUCKET_VIDEOS: str = "darezone-videos"
    STORAGE_BUCKET_AVATARS: str = "darezone-avatars"
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_VIDEO_SIZE_MB: int = 50
```

---

## 📦 Files

```
app/api/v1/media.py
tests/test_media.py
```

---

## 🧪 Testing

```python
def test_upload_photo_success()
def test_upload_video_success()
def test_upload_file_too_large()
def test_upload_invalid_type()
def test_delete_own_file()
def test_delete_other_user_file()  # Should fail
```

---

## ✅ Definition of Done

- [ ] Storage buckets created
- [ ] Upload endpoint working
- [ ] File validation enforced
- [ ] Public URLs accessible
- [ ] Delete endpoint working
- [ ] Tests pass
- [ ] Mobile app integration working

---

**Next:** [Story 11: Hitch System](./story-11-hitch-system.md)
