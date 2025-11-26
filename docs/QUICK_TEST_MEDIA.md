# 🚀 Quick Test - Media Upload (5 phút)

## Bước 1: Verify Buckets đã tạo

Mở Supabase Dashboard → **Storage** → Bạn sẽ thấy:

```
✅ darezone-photos (public)
✅ darezone-videos (public)
✅ darezone-avatars (public)
```

**Nếu thấy 3 buckets này → PASS! ✅**

---

## Bước 2: Verify RLS Policies

Supabase Dashboard → **Storage** → **Policies**

Bạn sẽ thấy **12 policies**:
- 4 policies cho photos (upload, view, delete, update)
- 4 policies cho videos
- 4 policies cho avatars

**Nếu thấy 12 policies → PASS! ✅**

---

## Bước 3: Start Server

```bash
cd darezone-server
source .venv/bin/activate
python main.py
```

**Server chạy tại:** http://localhost:8000

---

## Bước 4: Get JWT Token

```bash
# Login để lấy token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "your_password"
  }'
```

**Copy `access_token` từ response.**

---

## Bước 5: Test Upload Photo

### Tạo file test

```bash
echo "fake_photo_data" > test_photo.jpg
```

### Upload

```bash
# Thay YOUR_TOKEN bằng token từ bước 4
curl -X POST "http://localhost:8000/api/v1/media/upload?type=photo" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_photo.jpg"
```

**Expected Response:**
```json
{
  "success": true,
  "url": "https://xxx.supabase.co/storage/v1/object/public/darezone-photos/user-id/uuid.jpg",
  "filename": "user-id/uuid.jpg",
  "size": 16,
  "type": "photo",
  "bucket": "darezone-photos"
}
```

**✅ PASS nếu:**
- Status code: 200
- Có `url` field
- `bucket` = "darezone-photos"

**Copy URL để test tiếp!**

---

## Bước 6: Verify URL hoạt động

Mở URL từ bước 5 trong browser:
```
https://xxx.supabase.co/storage/v1/object/public/darezone-photos/...
```

**✅ PASS nếu:** File được tải về (hoặc hiển thị)

---

## Bước 7: Test Delete

```bash
# Thay YOUR_FILE_URL bằng URL từ bước 5
curl -X DELETE "http://localhost:8000/api/v1/media?url=YOUR_FILE_URL" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "File deleted successfully",
  "bucket": "darezone-photos",
  "path": "user-id/uuid.jpg"
}
```

**✅ PASS nếu:** Status code 200

---

## Bước 8: Verify File đã bị xóa

Mở lại URL từ bước 5 → Sẽ thấy **404 Not Found**

**✅ PASS nếu:** File không còn accessible

---

## 🎯 Test Summary

Nếu tất cả 8 bước PASS:

- ✅ Buckets created
- ✅ RLS policies working
- ✅ Upload endpoint working
- ✅ Public URLs accessible
- ✅ Delete endpoint working
- ✅ Ownership check working

**→ Story 10 HOÀN THÀNH! 🎉**

---

## 🐞 Troubleshooting

### Upload fails với 403

**Cause:** RLS policies chưa apply

**Fix:** Chạy lại migration `010_storage_buckets.sql`

---

### URL returns 404

**Cause:** Bucket chưa set public

**Fix:**
```sql
UPDATE storage.buckets 
SET public = true 
WHERE id LIKE 'darezone-%';
```

---

### Cannot delete file (403)

**Cause:** File path không match user_id

**Fix:** Đảm bảo file được upload với token của cùng 1 user

---

## 📱 Next: Test với Mobile App

1. Mở mobile app
2. Chọn ảnh từ thư viện
3. Upload
4. Verify URL hoạt động trong check-in

**Full guide:** `docs/MANUAL_TESTING_MEDIA.md`
