from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from supabase import Client
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.core.config import settings
import uuid
from typing import Literal

router = APIRouter()

# Allowed file types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/avi"}


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    type: Literal["photo", "video", "avatar"] = Query(..., description="Type of media to upload"),
    current_user=Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Upload media file to Supabase Storage
    
    **Supported Types:**
    - **photo**: Images for check-ins (max 10MB, jpg/png/webp)
    - **video**: Videos for check-ins (max 50MB, mp4/mov/avi)
    - **avatar**: Profile pictures (max 5MB, jpg/png/webp)
    
    **Returns:**
    - public_url: URL to access the uploaded file
    - filename: Storage path of the file
    - size: File size in bytes
    - type: Media type (photo/video/avatar)
    """
    # Validate file type based on media type
    if type in ["photo", "avatar"]:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid image type",
                    "allowed_types": list(ALLOWED_IMAGE_TYPES),
                    "received": file.content_type,
                },
            )
        max_size_mb = settings.MAX_AVATAR_SIZE_MB if type == "avatar" else settings.MAX_UPLOAD_SIZE_MB
        max_size = max_size_mb * 1024 * 1024
    elif type == "video":
        if file.content_type not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid video type",
                    "allowed_types": list(ALLOWED_VIDEO_TYPES),
                    "received": file.content_type,
                },
            )
        max_size = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
    else:
        raise HTTPException(status_code=400, detail="Invalid media type")

    # Read file contents
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Validate file size
    file_size = len(contents)
    if file_size > max_size:
        max_size_mb = max_size / 1024 / 1024
        actual_size_mb = file_size / 1024 / 1024
        raise HTTPException(
            status_code=400,
            detail={
                "error": "File too large",
                "max_size_mb": max_size_mb,
                "actual_size_mb": round(actual_size_mb, 2),
            },
        )

    # Generate unique filename with user_id prefix for ownership
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{current_user['id']}/{uuid.uuid4()}.{file_extension}"

    # Determine storage bucket
    if type == "photo":
        bucket = settings.STORAGE_BUCKET_PHOTOS
    elif type == "video":
        bucket = settings.STORAGE_BUCKET_VIDEOS
    else:  # avatar
        bucket = settings.STORAGE_BUCKET_AVATARS

    # Upload to Supabase Storage
    try:
        result = supabase.storage.from_(bucket).upload(
            unique_filename,
            contents,
            {
                "content-type": file.content_type,
                "cache-control": "3600",
                "upsert": "false",  # Don't overwrite existing files
            },
        )

        # Get public URL for the uploaded file
        public_url = supabase.storage.from_(bucket).get_public_url(unique_filename)

        return {
            "success": True,
            "url": public_url,
            "filename": unique_filename,
            "size": file_size,
            "type": type,
            "bucket": bucket,
        }

    except Exception as e:
        error_message = str(e)
        # Handle duplicate file error
        if "duplicate" in error_message.lower() or "already exists" in error_message.lower():
            raise HTTPException(
                status_code=409,
                detail="File already exists. Please try again with a different file.",
            )
        raise HTTPException(status_code=500, detail=f"Upload failed: {error_message}")


@router.delete("")
async def delete_media(
    url: str = Query(..., description="Public URL of the file to delete"),
    current_user=Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Delete a media file from Supabase Storage
    
    **Authorization:**
    - Users can only delete their own files
    - File ownership is verified via user_id in the file path
    
    **URL Format:**
    `https://{project}.supabase.co/storage/v1/object/public/{bucket}/{user_id}/{filename}`
    """
    try:
        # Parse URL to extract bucket and file path
        # Expected format: https://xxx.supabase.co/storage/v1/object/public/{bucket}/{path}
        if "/storage/v1/object/public/" not in url:
            raise ValueError("Invalid storage URL format")

        parts = url.split("/storage/v1/object/public/")
        if len(parts) != 2:
            raise ValueError("Could not parse storage URL")

        bucket_and_path = parts[1].split("/", 1)
        if len(bucket_and_path) != 2:
            raise ValueError("Could not extract bucket and path")

        bucket = bucket_and_path[0]
        file_path = bucket_and_path[1]

        # Verify file ownership (path must start with user_id)
        if not file_path.startswith(current_user["id"]):
            raise HTTPException(
                status_code=403,
                detail="You can only delete your own files",
            )

        # Verify bucket is valid
        valid_buckets = [
            settings.STORAGE_BUCKET_PHOTOS,
            settings.STORAGE_BUCKET_VIDEOS,
            settings.STORAGE_BUCKET_AVATARS,
        ]
        if bucket not in valid_buckets:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid bucket. Must be one of: {valid_buckets}",
            )

        # Delete from Supabase Storage
        result = supabase.storage.from_(bucket).remove([file_path])

        return {
            "success": True,
            "message": "File deleted successfully",
            "bucket": bucket,
            "path": file_path,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
