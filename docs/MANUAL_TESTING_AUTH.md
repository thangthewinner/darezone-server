# Manual Authentication Testing Guide

This guide provides step-by-step instructions for manually testing the authentication system with real Supabase tokens.

---

## Prerequisites

1. Supabase project running (already configured in `.env`)
2. At least one test user created in Supabase Auth
3. `curl` or Postman/Insomnia installed
4. Backend server running: `uvicorn app.main:app --reload`

---

## Step 1: Create Test User in Supabase

### Option A: Using Supabase Dashboard

1. Go to https://app.supabase.com/project/fvadyrhrqrqzxgyztyss
2. Navigate to **Authentication** → **Users**
3. Click **Add user** → **Create new user**
4. Enter:
   - Email: `testuser@darezone.com`
   - Password: `TestPassword123!`
5. Click **Create user**

### Option B: Using curl

```bash
curl -X POST 'https://fvadyrhrqrqzxgyztyss.supabase.co/auth/v1/signup' \
  -H 'apikey: YOUR_SUPABASE_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "testuser@darezone.com",
    "password": "TestPassword123!"
  }'
```

---

## Step 2: Create User Profile

The user needs a profile in `user_profiles` table for `/auth/me` to work.

### Using Supabase SQL Editor

```sql
-- Insert user profile (replace USER_ID with actual ID from auth.users)
INSERT INTO user_profiles (id, email, display_name, account_type)
VALUES (
  'USER_ID_HERE',  -- Get from auth.users table
  'testuser@darezone.com',
  'Test User',
  'b2c'
);
```

### Using curl (with service role key)

```bash
curl -X POST 'https://fvadyrhrqrqzxgyztyss.supabase.co/rest/v1/user_profiles' \
  -H 'apikey: YOUR_SERVICE_ROLE_KEY' \
  -H 'Authorization: Bearer YOUR_SERVICE_ROLE_KEY' \
  -H 'Content-Type: application/json' \
  -H 'Prefer: return=representation' \
  -d '{
    "id": "USER_ID_HERE",
    "email": "testuser@darezone.com",
    "display_name": "Test User",
    "account_type": "b2c"
  }'
```

---

## Step 3: Get Auth Token

### Option A: Using Supabase Dashboard

1. Go to **Authentication** → **Users**
2. Click on the test user
3. Scroll down to **Access Token**
4. Click **Generate new JWT** or copy existing one
5. Copy the token (starts with `eyJ...`)

### Option B: Using curl (Login)

```bash
curl -X POST 'https://fvadyrhrqrqzxgyztyss.supabase.co/auth/v1/token?grant_type=password' \
  -H 'apikey: YOUR_SUPABASE_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "testuser@darezone.com",
    "password": "TestPassword123!"
  }'
```

**Save the `access_token` from the response!**

---

## Step 4: Test Authentication Endpoints

### Test 1: Verify Token

```bash
# Set your token
TOKEN="eyJhbGc..."  # Your actual token

# Test verify endpoint
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "valid": true,
  "user_id": "uuid-here",
  "email": "testuser@darezone.com"
}
```

**Status Code:** 200 OK

---

### Test 2: Get Current User

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "id": "uuid-here",
  "email": "testuser@darezone.com",
  "full_name": null,
  "display_name": "Test User",
  "avatar_url": null,
  "bio": null,
  "account_type": "b2c",
  "stats": {
    "current_streak": 0,
    "longest_streak": 0,
    "total_check_ins": 0,
    "total_challenges_completed": 0,
    "points": 0
  },
  "created_at": "2025-11-24T..."
}
```

**Status Code:** 200 OK

---

### Test 3: Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Logged out successfully. Please clear your auth token."
}
```

**Status Code:** 200 OK

---

## Step 5: Test Error Scenarios

### Test 4: Missing Token (401/403)

```bash
curl http://localhost:8000/api/v1/auth/me
```

**Expected:**
- **Status Code:** 403 Forbidden
- **Response:** `{"detail": "Not authenticated"}`

---

### Test 5: Invalid Token (401)

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer invalid_token_12345"
```

**Expected:**
- **Status Code:** 401 Unauthorized
- **Response:** `{"detail": "Invalid authentication credentials"}` or `{"detail": "Could not validate credentials"}`

---

### Test 6: Malformed Authorization Header

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: InvalidFormat"
```

**Expected:**
- **Status Code:** 403 Forbidden

---

### Test 7: Expired Token

Wait for token to expire (default 1 hour), then:

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $EXPIRED_TOKEN"
```

**Expected:**
- **Status Code:** 401 Unauthorized

---

## Step 6: Test in Swagger UI

1. Open http://localhost:8000/docs
2. Click **Authorize** button (top right)
3. Enter: `Bearer YOUR_TOKEN_HERE` (include "Bearer " prefix)
4. Click **Authorize**
5. Try endpoints:
   - `POST /api/v1/auth/verify` → Should return 200
   - `GET /api/v1/auth/me` → Should return profile
   - `POST /api/v1/auth/logout` → Should return success

---

## Step 7: Test from Frontend (React Native)

### Using Expo/React Native App

```typescript
// In your React Native app
import { supabase } from './lib/supabase';

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'testuser@darezone.com',
  password: 'TestPassword123!'
});

if (data.session) {
  const token = data.session.access_token;
  
  // Test backend endpoints
  const response = await fetch('http://YOUR_BACKEND_URL/api/v1/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const profile = await response.json();
  console.log('User profile:', profile);
}
```

---

## Troubleshooting

### Issue: "User profile not found"

**Cause:** User exists in `auth.users` but not in `user_profiles`

**Solution:** Run Step 2 to create user profile

---

### Issue: "Invalid authentication credentials"

**Cause:** Token is invalid, expired, or malformed

**Solutions:**
1. Generate new token (Step 3)
2. Check token hasn't expired (default 1 hour)
3. Ensure you're copying the complete token (starts with `eyJ`)

---

### Issue: "Not authenticated" (403)

**Cause:** No Authorization header sent

**Solution:** Include header: `-H "Authorization: Bearer YOUR_TOKEN"`

---

### Issue: "Failed to retrieve user information" (500)

**Cause:** Database error or RLS policy issue

**Solutions:**
1. Check backend logs for detailed error
2. Verify RLS policies are correct
3. Ensure `SUPABASE_SERVICE_ROLE_KEY` is set in `.env`

---

## Success Criteria

✅ All tests return expected responses  
✅ Valid tokens work correctly  
✅ Invalid tokens are rejected with 401  
✅ Missing tokens are rejected with 403  
✅ User profile data is returned correctly  
✅ Swagger UI authentication works  
✅ Frontend can authenticate and call protected endpoints

---

## Next Steps

After manual testing passes:
1. Proceed to **Story 4: User Management**
2. Implement user profile CRUD operations
3. Add more protected endpoints using the auth system

---

**Last Updated:** 2025-11-24  
**Story:** Story 3 - Authentication System  
**Status:** Manual testing required for full validation
