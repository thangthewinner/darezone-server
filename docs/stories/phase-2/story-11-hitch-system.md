# Story 11: Hitch Reminder System

**Phase:** 2 - Social Features  
**Points:** 3 (3 days)  
**Priority:** 🟡 MEDIUM  
**Dependencies:** [Story 10: Media Upload](./story-10-media-upload.md)

---

## 📖 Description

Implement hitch reminder system với rate limiting, notification sending, và hitch count management.

---

## 🎯 Goals

- [ ] Members can send hitch reminders
- [ ] Hitch count decrements correctly
- [ ] Rate limiting enforced (1 per habit per day)
- [ ] Notifications sent to targets
- [ ] Hitch log tracked

---

## ✅ Acceptance Criteria

### 1. Send Hitch API
- [ ] `POST /hitch` - Send hitch reminder
- [ ] Validates sender has hitch_count > 0
- [ ] Decrements hitch_count
- [ ] Creates hitch_log entry
- [ ] Sends notification to target users
- [ ] Rate limit: 1 hitch per habit per target per day

### 2. RPC Function
- [ ] `send_hitch_reminder()` - Atomic hitch sending
- [ ] Updates all stats in single transaction
- [ ] Returns hitches_sent and remaining_hitches

### 3. Validation
- [ ] Sender and targets in same challenge
- [ ] Targets haven't checked in today
- [ ] Sender has hitches remaining
- [ ] Not duplicate within 24h

---

## 🛠️ Implementation

### RPC Function

```sql
-- migrations/008_hitch_system.sql

CREATE OR REPLACE FUNCTION send_hitch_reminder(
  p_challenge_id UUID,
  p_habit_id UUID,
  p_sender_id UUID,
  p_target_ids UUID[]
)
RETURNS TABLE (
  hitches_sent INTEGER,
  remaining_hitches INTEGER
) AS $$
DECLARE
  v_sender_record RECORD;
  v_target_id UUID;
  v_hitches_sent INTEGER := 0;
  v_habit_name TEXT;
BEGIN
  -- Get sender's membership
  SELECT * INTO v_sender_record
  FROM challenge_members
  WHERE challenge_id = p_challenge_id
    AND user_id = p_sender_id
    AND status = 'active';
  
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Sender is not an active member';
  END IF;
  
  IF v_sender_record.hitch_count <= 0 THEN
    RAISE EXCEPTION 'No hitches remaining';
  END IF;
  
  -- Get habit name
  SELECT name INTO v_habit_name
  FROM habits WHERE id = p_habit_id;
  
  -- Send hitch to each target
  FOREACH v_target_id IN ARRAY p_target_ids
  LOOP
    -- Check if already sent hitch today
    IF NOT EXISTS (
      SELECT 1 FROM hitch_log
      WHERE habit_id = p_habit_id
        AND sender_id = p_sender_id
        AND target_id = v_target_id
        AND created_at::date = CURRENT_DATE
    ) THEN
      -- Log hitch
      INSERT INTO hitch_log (
        challenge_id, habit_id, sender_id, target_id
      ) VALUES (
        p_challenge_id, p_habit_id, p_sender_id, v_target_id
      );
      
      -- Create notification
      INSERT INTO notifications (
        user_id, type, title, body, data, action_url
      ) VALUES (
        v_target_id,
        'hitch_reminder',
        'Reminder: Check-in needed!',
        format('Your friend reminded you to check in for "%s"', v_habit_name),
        jsonb_build_object(
          'challenge_id', p_challenge_id,
          'habit_id', p_habit_id,
          'sender_id', p_sender_id
        ),
        format('/challenges/%s', p_challenge_id)
      );
      
      v_hitches_sent := v_hitches_sent + 1;
    END IF;
  END LOOP;
  
  -- Decrement sender's hitch count
  UPDATE challenge_members
  SET hitch_count = hitch_count - 1
  WHERE challenge_id = p_challenge_id
    AND user_id = p_sender_id;
  
  RETURN QUERY SELECT 
    v_hitches_sent,
    v_sender_record.hitch_count - 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### app/schemas/hitch.py

```python
from pydantic import BaseModel, Field
from typing import List

class HitchRequest(BaseModel):
    """Send hitch reminder"""
    challenge_id: str
    habit_id: str
    target_user_ids: List[str] = Field(..., min_items=1, max_items=10)

class HitchResponse(BaseModel):
    """Hitch send result"""
    success: bool
    hitches_sent: int
    remaining_hitches: int
    message: str
```

### app/api/v1/hitch.py

```python
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.schemas.hitch import HitchRequest, HitchResponse

router = APIRouter()

@router.post("", response_model=HitchResponse)
async def send_hitch(
    request: HitchRequest,
    current_user = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Send hitch reminder to members
    
    - Decrements sender's hitch_count
    - Sends notification to targets
    - Rate limit: 1 per habit per target per day
    """
    try:
        result = supabase.rpc('send_hitch_reminder', {
            'p_challenge_id': request.challenge_id,
            'p_habit_id': request.habit_id,
            'p_sender_id': current_user['id'],
            'p_target_ids': request.target_user_ids
        }).execute()
        
        if not result.data:
            raise HTTPException(500, "Failed to send hitch")
        
        data = result.data[0]
        
        return HitchResponse(
            success=True,
            hitches_sent=data['hitches_sent'],
            remaining_hitches=data['remaining_hitches'],
            message=f"Sent {data['hitches_sent']} reminders. {data['remaining_hitches']} hitches remaining."
        )
        
    except Exception as e:
        error_msg = str(e)
        if "No hitches remaining" in error_msg:
            raise HTTPException(400, "You have no hitches remaining")
        elif "not an active member" in error_msg:
            raise HTTPException(403, "You are not a member of this challenge")
        else:
            raise HTTPException(500, f"Failed to send hitch: {error_msg}")
```

---

## 📦 Files

```
app/api/v1/hitch.py
app/schemas/hitch.py
migrations/008_hitch_system.sql
tests/test_hitch.py
```

---

## 🧪 Testing

```python
def test_send_hitch_success()
def test_send_hitch_no_hitches_remaining()
def test_send_hitch_rate_limit()
def test_hitch_count_decrements()
def test_notification_sent()
```

---

## ✅ Definition of Done

- [ ] RPC function working
- [ ] Hitch endpoint functional
- [ ] Rate limiting enforced
- [ ] Notifications sent
- [ ] Hitch count updates
- [ ] Tests pass

---

**Next:** [Story 12: History & Stats](./story-12-history-stats.md)
