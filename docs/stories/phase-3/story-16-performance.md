# Story 16: Performance Optimization

**Phase:** 3 - B2B & Advanced  
**Points:** 3 (3 days)  
**Priority:** 🟡 MEDIUM  
**Dependencies:** [Story 15: Analytics](./story-15-analytics.md)

---

## 📖 Description

Optimize database queries, add caching, implement connection pooling, và load testing.

---

## 🎯 Goals

- [ ] API response time < 200ms (p95)
- [ ] Database queries optimized
- [ ] Caching implemented (optional Redis)
- [ ] Load tested for 100 concurrent users

---

## ✅ Acceptance Criteria

### 1. Query Optimization
- [ ] Identify slow queries (>500ms)
- [ ] Add missing indexes
- [ ] Optimize N+1 queries
- [ ] Use select() to limit fields

### 2. Caching (Optional)
- [ ] Redis setup
- [ ] Cache user profiles (TTL: 5min)
- [ ] Cache challenge lists (TTL: 1min)
- [ ] Cache invalidation on updates

### 3. Connection Pooling
- [ ] Supabase connection pool configured
- [ ] Max connections set appropriately

### 4. Load Testing
- [ ] Load test with Locust/K6
- [ ] 100 concurrent users
- [ ] All endpoints < 200ms p95
- [ ] No errors under load

---

## 🛠️ Implementation

### Add Missing Indexes

```sql
-- migrations/010_performance_indexes.sql

-- Frequently queried patterns
CREATE INDEX IF NOT EXISTS idx_checkins_user_date 
ON check_ins(user_id, checkin_date DESC);

CREATE INDEX IF NOT EXISTS idx_challenge_members_user_status 
ON challenge_members(user_id, status) 
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread 
ON notifications(user_id, created_at DESC) 
WHERE is_read = false;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_challenges_status_created 
ON challenges(status, created_at DESC);
```

### Caching Layer (Optional)

```python
# app/core/cache.py
import redis
import json
from typing import Optional

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_get(key: str) -> Optional[dict]:
    value = redis_client.get(key)
    return json.loads(value) if value else None

def cache_set(key: str, value: dict, ttl: int = 300):
    redis_client.setex(key, ttl, json.dumps(value))

def cache_delete(key: str):
    redis_client.delete(key)

# Usage in endpoints
@router.get("/users/me")
async def get_my_profile(current_user = Depends(get_current_active_user)):
    # Try cache first
    cache_key = f"user_profile:{current_user['id']}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    # Query database
    profile = ...  # get from DB
    
    # Cache result
    cache_set(cache_key, profile, ttl=300)
    return profile
```

### Load Testing

```python
# locustfile.py
from locust import HttpUser, task, between

class DareZoneUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_profile(self):
        self.client.get("/api/v1/users/me", headers=self.headers)
    
    @task(2)
    def list_challenges(self):
        self.client.get("/api/v1/challenges", headers=self.headers)
    
    @task(1)
    def create_checkin(self):
        self.client.post("/api/v1/checkins", 
            headers=self.headers,
            json={
                "challenge_id": "...",
                "habit_id": "...",
                "caption": "Test checkin"
            })
```

```bash
# Run load test
locust -f locustfile.py --host=https://your-api.com
```

---

## 📦 Files

```
migrations/010_performance_indexes.sql
app/core/cache.py (optional)
locustfile.py
tests/test_performance.py
```

---

## 🧪 Testing

```python
def test_query_performance():
    """Ensure queries < 200ms"""
    import time
    start = time.time()
    # Make API call
    duration = time.time() - start
    assert duration < 0.2

def test_cache_hit():
    """Verify cache working"""
    # First call (miss)
    # Second call (hit) should be faster
    pass
```

---

## ✅ Definition of Done

- [ ] All indexes added
- [ ] Slow queries optimized
- [ ] Load test passes (100 concurrent users)
- [ ] p95 response time < 200ms
- [ ] No errors under load
- [ ] Caching working (if implemented)
- [ ] Documentation updated

---

**Next:** [Story 17: Scheduled Jobs](./story-17-scheduled-jobs.md)
