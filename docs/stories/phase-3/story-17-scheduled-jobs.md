# Story 17: Scheduled Jobs & Automation

**Phase:** 3 - B2B & Advanced  
**Points:** 2 (2 days)  
**Priority:** 🟡 MEDIUM  
**Dependencies:** [Story 16: Performance](./story-16-performance.md)

---

## 📖 Description

Implement scheduled jobs cho auto-complete challenges, refresh stats, cleanup, và daily reminders.

---

## 🎯 Goals

- [ ] Auto-complete expired challenges
- [ ] Refresh materialized views
- [ ] Cleanup expired notifications
- [ ] Send daily reminder notifications

---

## ✅ Acceptance Criteria

### 1. Daily Jobs
- [ ] Auto-complete challenges (midnight UTC)
- [ ] Refresh stats views (hourly)
- [ ] Send streak reminders (8am local time)
- [ ] Cleanup expired notifications (daily)

### 2. Implementation Options
- [ ] Supabase Edge Functions (recommended)
- [ ] GitHub Actions cron
- [ ] Railway Cron Jobs
- [ ] Celery worker (advanced)

### 3. Monitoring
- [ ] Job execution logs
- [ ] Failure alerts
- [ ] Execution time tracking

---

## 🛠️ Implementation

### Option A: Supabase Edge Functions

```typescript
// supabase/functions/daily-jobs/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )
  
  try {
    // 1. Auto-complete expired challenges
    await supabase.rpc('auto_complete_challenges')
    
    // 2. Refresh stats
    await supabase.rpc('refresh_challenge_stats')
    
    // 3. Cleanup old notifications (>30 days)
    await supabase
      .from('notifications')
      .delete()
      .lt('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString())
    
    return new Response(JSON.stringify({ success: true }), {
      headers: { 'Content-Type': 'application/json' }
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
})
```

```bash
# Deploy edge function
supabase functions deploy daily-jobs

# Setup cron trigger in Supabase Dashboard
# Cron: 0 0 * * * (daily at midnight)
```

### Option B: GitHub Actions Cron

```yaml
# .github/workflows/daily-jobs.yml

name: Daily Jobs

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
  workflow_dispatch:  # Manual trigger

jobs:
  run-jobs:
    runs-on: ubuntu-latest
    steps:
      - name: Auto-complete challenges
        run: |
          curl -X POST https://your-api.com/admin/jobs/auto-complete \
            -H "Authorization: Bearer ${{ secrets.ADMIN_TOKEN }}"
      
      - name: Refresh stats
        run: |
          curl -X POST https://your-api.com/admin/jobs/refresh-stats \
            -H "Authorization: Bearer ${{ secrets.ADMIN_TOKEN }}"
```

### SQL Functions

```sql
-- migrations/011_scheduled_jobs.sql

CREATE OR REPLACE FUNCTION auto_complete_challenges()
RETURNS void AS $$
BEGIN
  -- Update challenges that passed end_date
  UPDATE challenges
  SET status = CASE
    WHEN (
      SELECT AVG(completion_rate)
      FROM challenge_member_stats
      WHERE challenge_id = challenges.id
    ) >= 80 THEN 'completed'
    ELSE 'failed'
  END
  WHERE status = 'active'
    AND end_date < CURRENT_DATE;
  
  -- Send notifications to members
  INSERT INTO notifications (user_id, type, title, body, data)
  SELECT 
    cm.user_id,
    'challenge_completed',
    'Challenge Completed!',
    format('Your challenge "%s" has ended', c.name),
    jsonb_build_object('challenge_id', c.id, 'status', c.status)
  FROM challenges c
  JOIN challenge_members cm ON cm.challenge_id = c.id
  WHERE c.status IN ('completed', 'failed')
    AND c.end_date = CURRENT_DATE - INTERVAL '1 day';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Admin Endpoints

```python
# app/api/v1/admin_jobs.py

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.core.dependencies import get_supabase_client
from app.core.security import get_admin_user

router = APIRouter()

@router.post("/admin/jobs/auto-complete")
async def trigger_auto_complete(
    admin = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Manually trigger auto-complete job"""
    try:
        supabase.rpc('auto_complete_challenges').execute()
        return {"success": True, "message": "Challenges auto-completed"}
    except Exception as e:
        raise HTTPException(500, f"Job failed: {str(e)}")

@router.post("/admin/jobs/refresh-stats")
async def trigger_refresh_stats(
    admin = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Manually trigger stats refresh"""
    try:
        supabase.rpc('refresh_challenge_stats').execute()
        return {"success": True, "message": "Stats refreshed"}
    except Exception as e:
        raise HTTPException(500, f"Job failed: {str(e)}")
```

---

## 📦 Files

```
supabase/functions/daily-jobs/index.ts
.github/workflows/daily-jobs.yml
migrations/011_scheduled_jobs.sql
app/api/v1/admin_jobs.py
```

---

## 🧪 Testing

```python
def test_auto_complete_expired_challenges()
def test_refresh_stats()
def test_cleanup_old_notifications()
def test_manual_job_trigger()
```

---

## ✅ Definition of Done

- [ ] Daily jobs running automatically
- [ ] Challenges auto-complete correctly
- [ ] Stats refresh hourly
- [ ] Old data cleaned up
- [ ] Job logs accessible
- [ ] Manual trigger endpoints working
- [ ] Monitoring setup

---

**Next:** [Story 18: Production Hardening](./story-18-production-hardening.md)
