# Story 3: Authentication System

**Phase:** 1 - Core Backend  
**Points:** 3 (3 days)  
**Priority:** 🔥 CRITICAL  
**Dependencies:** [Story 2: Project Structure](./story-2-project-structure.md)

---

## 📖 Description

Implement Supabase Auth integration với JWT token verification, user authentication middleware, và protected route system.

---

## 🎯 Goals

- [ ] Supabase Auth fully integrated
- [ ] JWT token verification working
- [ ] Protected routes enforced
- [ ] User context available in requests
- [ ] Auth errors handled properly

---

## ✅ Acceptance Criteria

### 1. Auth Dependencies Setup
- [ ] Supabase client configured with auth
- [ ] Security helper functions created
- [ ] Token verification middleware working

### 2. Authentication Endpoints
- [ ] `POST /auth/verify` - Verify token (for testing)
- [ ] `GET /auth/me` - Get current user
- [ ] Proper error responses (401, 403)

### 3. Middleware & Dependencies
- [ ] `get_current_user()` dependency
- [ ] `get_current_active_user()` dependency
- [ ] Token extraction from Authorization header
- [ ] User claims extracted from JWT

### 4. RLS Context
- [ ] User ID passed to Supabase queries
- [ ] RLS policies enforced automatically
- [ ] Service role used correctly

### 5. Error Handling
- [ ] Invalid token → 401 Unauthorized
- [ ] Missing token → 401 Unauthorized
- [ ] Expired token → 401 Token expired
- [ ] Consistent error format

---

## 🛠️ Technical Implementation

### Step 1: Update app/core/security.py

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from typing import Optional, Dict, Any
from app.core.dependencies import get_supabase_client
from app.core.exceptions import unauthorized_exception
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
) -> Dict[str, Any]:
    """
    Verify JWT token and return current user
    
    Raises:
        HTTPException: 401 if token invalid
    """
    token = credentials.credentials
    
    try:
        # Verify token with Supabase
        response = supabase.auth.get_user(token)
        
        if not response or not response.user:
            logger.warning("Invalid token: no user found")
            raise unauthorized_exception("Invalid authentication credentials")
        
        user = response.user
        
        # Return user data
        return {
            "id": user.id,
            "email": user.email,
            "user_metadata": user.user_metadata or {},
            "app_metadata": user.app_metadata or {},
        }
        
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise unauthorized_exception("Could not validate credentials")

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
) -> Dict[str, Any]:
    """
    Get current user and verify they have active profile
    
    Raises:
        HTTPException: 403 if user inactive/banned
    """
    try:
        # Check if user profile exists and is active
        response = supabase.table('user_profiles')\
            .select('*')\
            .eq('id', current_user['id'])\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User profile not found. Please complete setup."
            )
        
        profile = response.data
        
        # Combine auth user + profile
        return {
            **current_user,
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

# Optional: Get user without raising exception
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[Dict[str, Any]]:
    """
    Get current user if token present, None otherwise
    For optional authentication endpoints
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        return None
```

### Step 2: Create app/api/v1/auth.py

```python
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_user, get_current_active_user
from app.schemas.auth import TokenVerifyResponse, CurrentUserResponse
from app.schemas.common import SuccessResponse
from typing import Dict, Any

router = APIRouter()

@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Verify JWT token (for testing)
    
    Returns user info if token valid
    """
    return TokenVerifyResponse(
        valid=True,
        user_id=current_user["id"],
        email=current_user["email"]
    )

@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get current authenticated user's full profile
    
    Requires: Bearer token in Authorization header
    """
    profile = current_user["profile"]
    
    return CurrentUserResponse(
        id=profile["id"],
        email=profile["email"],
        full_name=profile.get("full_name"),
        display_name=profile.get("display_name"),
        avatar_url=profile.get("avatar_url"),
        account_type=profile.get("account_type", "b2c"),
        stats={
            "current_streak": profile.get("current_streak", 0),
            "total_check_ins": profile.get("total_check_ins", 0),
            "points": profile.get("points", 0),
        },
        created_at=profile["created_at"]
    )

@router.post("/logout", response_model=SuccessResponse)
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Logout current user (invalidate token)
    
    Note: Supabase handles token invalidation
    Frontend should clear stored token
    """
    # Optional: Log logout event
    # In Supabase, token invalidation is handled client-side
    
    return SuccessResponse(
        success=True,
        message="Logged out successfully"
    )
```

### Step 3: Create app/schemas/auth.py

```python
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime

class TokenVerifyResponse(BaseModel):
    """Token verification response"""
    valid: bool
    user_id: str
    email: EmailStr

class CurrentUserResponse(BaseModel):
    """Current user full profile"""
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    account_type: str = "b2c"
    stats: Dict[str, int]
    created_at: datetime
```

### Step 4: Create app/schemas/common.py

```python
from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List

class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    details: Optional[dict] = None
```

### Step 5: Update app/api/v1/__init__.py

```python
from fastapi import APIRouter
from .router import router as base_router
from .auth import router as auth_router

router = APIRouter()
router.include_router(base_router)
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
```

### Step 6: Create tests/test_auth.py

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Mock Supabase token (you'll need to generate real ones for testing)
VALID_TOKEN = "eyJhbGc..."  # Get from Supabase auth
INVALID_TOKEN = "invalid_token_12345"

def test_verify_token_valid():
    """Test token verification with valid token"""
    response = client.post(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"}
    )
    assert response.status_code == 200
    assert response.json()["valid"] == True

def test_verify_token_invalid():
    """Test token verification with invalid token"""
    response = client.post(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {INVALID_TOKEN}"}
    )
    assert response.status_code == 401

def test_verify_token_missing():
    """Test token verification without token"""
    response = client.post("/api/v1/auth/verify")
    assert response.status_code == 403  # HTTPBearer returns 403 by default

def test_get_current_user():
    """Test get current user endpoint"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "stats" in data

def test_get_current_user_unauthorized():
    """Test get current user without auth"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403
```

### Step 7: Create Test Utility for Getting Tokens

```python
# tests/conftest.py
import pytest
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def supabase_client():
    """Get Supabase client for tests"""
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )

@pytest.fixture
def test_user_token(supabase_client):
    """
    Create test user and return auth token
    
    Usage in tests:
        def test_something(test_user_token):
            headers = {"Authorization": f"Bearer {test_user_token}"}
    """
    # Create test user
    email = f"test_{os.urandom(8).hex()}@example.com"
    password = "TestPassword123!"
    
    # Sign up
    response = supabase_client.auth.sign_up({
        "email": email,
        "password": password
    })
    
    # Return token
    token = response.session.access_token
    
    yield token
    
    # Cleanup: delete user after test
    # (Requires admin API or manual cleanup)
```

---

## 📦 Files to Create

```
app/
├── core/
│   └── security.py              # ✅ Update with auth functions
├── api/v1/
│   ├── __init__.py              # ✅ Update to include auth router
│   └── auth.py                  # 🆕 Auth endpoints
├── schemas/
│   ├── auth.py                  # 🆕 Auth DTOs
│   └── common.py                # 🆕 Common DTOs
tests/
├── conftest.py                  # 🆕 Test fixtures
└── test_auth.py                 # 🆕 Auth tests
```

---

## 🧪 Testing Checklist

### Manual Testing

```bash
# 1. Get token from frontend or Supabase
# Frontend: After login, console.log(session.access_token)
# Or use Supabase Dashboard → Authentication → Users → [user] → Copy JWT

# 2. Test verify endpoint
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Expected: {"valid":true,"user_id":"...","email":"..."}

# 3. Test get current user
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Expected: Full user profile with stats

# 4. Test without token
curl http://localhost:8000/api/v1/auth/me

# Expected: 403 Forbidden

# 5. Test with invalid token
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer invalid_token_123"

# Expected: 401 Unauthorized
```

### Integration Testing

```python
# Full auth flow test
def test_full_auth_flow(supabase_client):
    # 1. Create user
    email = "testuser@example.com"
    password = "SecurePass123!"
    
    auth_response = supabase_client.auth.sign_up({
        "email": email,
        "password": password
    })
    
    assert auth_response.user is not None
    token = auth_response.session.access_token
    
    # 2. Create profile
    profile_data = {
        "id": auth_response.user.id,
        "email": email,
        "display_name": "Test User"
    }
    
    profile_response = supabase_client.table('user_profiles')\
        .insert(profile_data)\
        .execute()
    
    assert profile_response.data is not None
    
    # 3. Verify token works
    response = client.post(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    
    # 4. Get user profile
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == email
```

---

## 📝 Notes

### Token Flow

```
Frontend Login
      ↓
Supabase Auth (email/password)
      ↓
Returns JWT token
      ↓
Frontend stores in AsyncStorage
      ↓
Frontend sends in Authorization header: "Bearer {token}"
      ↓
Backend extracts token
      ↓
Supabase verifies token
      ↓
Backend gets user info
      ↓
Request proceeds with user context
```

### Security Considerations

1. **Never log tokens** - They're secrets
2. **Token expiration** - Supabase handles this (default 1 hour)
3. **Refresh tokens** - Frontend handles with Supabase client
4. **Service role key** - Only use server-side, never expose

### Common Issues

**Issue**: "Invalid token" even with valid token
```python
# Solution: Check token hasn't expired
# Frontend should auto-refresh before expiry
# Supabase client handles this automatically
```

**Issue**: "User profile not found"
```python
# Solution: Profile created after signup?
# Check user_profiles table has entry for user
# May need signup webhook to auto-create profile
```

**Issue**: CORS error when testing from mobile
```python
# Solution: Add mobile origin to ALLOWED_ORIGINS
ALLOWED_ORIGINS=["http://localhost:19006","exp://YOUR_IP:8081"]
```

---

## ✅ Definition of Done

- [ ] Auth endpoints implemented and working
- [ ] Token verification works with real Supabase tokens
- [ ] Protected routes return 401 without valid token
- [ ] `get_current_user` dependency extracts user correctly
- [ ] Error responses follow standard format
- [ ] All tests pass (manual + automated)
- [ ] Swagger docs updated with auth info
- [ ] Security best practices followed
- [ ] Code reviewed and merged

---

**Previous:** [Story 2: Project Structure](./story-2-project-structure.md)  
**Next:** [Story 4: User Management](./story-4-user-management.md)
