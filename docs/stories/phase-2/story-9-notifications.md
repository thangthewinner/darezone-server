# Story 9: Notification System

**Phase:** 2 - Social Features  
**Points:** 3 (3 days)  
**Priority:** 🟡 MEDIUM  
**Dependencies:** [Story 8: Friendship](./story-8-friendship.md)

---

## 📖 Description

Implement notification system: create, list, mark as read, delete notifications. Support 9 notification types.

---

## 🎯 Goals

- [ ] Notifications created for key events
- [ ] Users can list their notifications
- [ ] Mark as read functionality
- [ ] Push notifications ready (Expo integration)
- [ ] Unread count API

---

## ✅ Acceptance Criteria

### 1. Notification Types Supported
- [ ] `friend_request` - New friend request
- [ ] `friend_accepted` - Request accepted
- [ ] `challenge_invite` - Challenge invitation
- [ ] `challenge_started` - Challenge began
- [ ] `challenge_completed` - Challenge finished
- [ ] `hitch_reminder` - Hitch from friend
- [ ] `streak_milestone` - Streak achievement
- [ ] `member_joined` - New member in challenge
- [ ] `member_left` - Member left challenge

### 2. Core APIs
- [ ] `GET /notifications` - List my notifications (paginated)
- [ ] `GET /notifications/unread/count` - Unread count
- [ ] `POST /notifications/mark-read` - Batch mark as read
- [ ] `DELETE /notifications/{id}` - Delete notification

### 3. Auto-creation
- [ ] Notifications auto-created on events
- [ ] Integrated with challenge/friend flows
- [ ] Background worker for scheduled notifications

### 4. Push Notifications
- [ ] Expo Push Token registration
- [ ] Send push via Expo API
- [ ] Push notification payload format

---

## 🛠️ Implementation

### app/schemas/notification.py

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    FRIEND_REQUEST = "friend_request"
    FRIEND_ACCEPTED = "friend_accepted"
    CHALLENGE_INVITE = "challenge_invite"
    CHALLENGE_STARTED = "challenge_started"
    CHALLENGE_COMPLETED = "challenge_completed"
    HITCH_REMINDER = "hitch_reminder"
    STREAK_MILESTONE = "streak_milestone"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"

class NotificationCreate(BaseModel):
    """Internal use: Create notification"""
    user_id: str
    type: NotificationType
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None

class Notification(BaseModel):
    """Notification response"""
    id: str
    type: NotificationType
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MarkNotificationRead(BaseModel):
    """Mark notifications as read"""
    notification_ids: List[str]

class PushTokenRegister(BaseModel):
    """Register Expo push token"""
    token: str
    device_type: str = "mobile"
```

### app/api/v1/notifications.py

```python
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.schemas.notification import *
from app.schemas.common import PaginationParams, PaginatedResponse, SuccessResponse

router = APIRouter()

@router.get("", response_model=PaginatedResponse[Notification])
async def list_notifications(
    unread_only: bool = False,
    pagination: PaginationParams = Depends(),
    current_user = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """List my notifications"""
    query = supabase.table('notifications')\
        .select('*', count='exact')\
        .eq('user_id', current_user['id'])\
        .order('created_at', desc=True)
    
    if unread_only:
        query = query.eq('is_read', False)
    
    count_result = query.execute()
    data_result = query.range(
        pagination.offset,
        pagination.offset + pagination.limit - 1
    ).execute()
    
    return PaginatedResponse.create(
        items=[Notification(**n) for n in data_result.data],
        total=count_result.count or 0,
        page=pagination.page,
        limit=pagination.limit
    )

@router.get("/unread/count")
async def get_unread_count(
    current_user = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get unread notification count"""
    result = supabase.table('notifications')\
        .select('id', count='exact')\
        .eq('user_id', current_user['id'])\
        .eq('is_read', False)\
        .execute()
    
    return {"count": result.count or 0}

@router.post("/mark-read", response_model=SuccessResponse)
async def mark_notifications_read(
    request: MarkNotificationRead,
    current_user = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Mark notifications as read"""
    supabase.table('notifications')\
        .update({"is_read": True, "read_at": "now()"})\
        .in_('id', request.notification_ids)\
        .eq('user_id', current_user['id'])\
        .execute()
    
    return SuccessResponse(
        success=True,
        message=f"Marked {len(request.notification_ids)} notifications as read"
    )

@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: str,
    current_user = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete notification"""
    supabase.table('notifications')\
        .delete()\
        .eq('id', notification_id)\
        .eq('user_id', current_user['id'])\
        .execute()

@router.post("/register-push-token", response_model=SuccessResponse)
async def register_push_token(
    request: PushTokenRegister,
    current_user = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Register Expo push notification token"""
    # Store in user_profiles or separate push_tokens table
    supabase.table('user_profiles')\
        .update({"push_token": request.token})\
        .eq('id', current_user['id'])\
        .execute()
    
    return SuccessResponse(success=True, message="Push token registered")
```

### Helper: Create Notification

```python
# app/services/notification_service.py

async def create_notification(
    supabase: Client,
    user_id: str,
    type: str,
    title: str,
    body: str,
    data: dict = None,
    action_url: str = None,
    send_push: bool = True
):
    """Create and optionally send push notification"""
    # Create in database
    notification = supabase.table('notifications').insert({
        "user_id": user_id,
        "type": type,
        "title": title,
        "body": body,
        "data": data or {},
        "action_url": action_url
    }).execute()
    
    # Send push notification
    if send_push:
        await send_push_notification(supabase, user_id, title, body, data)
    
    return notification.data[0]

async def send_push_notification(
    supabase: Client,
    user_id: str,
    title: str,
    body: str,
    data: dict = None
):
    """Send Expo push notification"""
    from app.core.config import settings
    import httpx
    
    if not settings.EXPO_ACCESS_TOKEN:
        return
    
    # Get user's push token
    user = supabase.table('user_profiles')\
        .select('push_token')\
        .eq('id', user_id)\
        .single()\
        .execute()
    
    if not user.data or not user.data.get('push_token'):
        return
    
    # Send via Expo API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://exp.host/--/api/v2/push/send",
            headers={
                "Authorization": f"Bearer {settings.EXPO_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "to": user.data['push_token'],
                "title": title,
                "body": body,
                "data": data or {},
                "sound": "default",
                "priority": "high"
            }
        )
        return response.json()
```

---

## 📦 Files

```
app/api/v1/notifications.py
app/schemas/notification.py
app/services/notification_service.py
tests/test_notifications.py
```

---

## 🧪 Testing

```python
def test_list_notifications()
def test_unread_count()
def test_mark_as_read()
def test_push_notification_sent()
```

---

## ✅ Definition of Done

- [ ] All notification endpoints working
- [ ] Notifications created on events
- [ ] Push notifications sent successfully
- [ ] Unread count accurate
- [ ] Tests pass
- [ ] Integrated with challenge/friend flows

---

**Next:** [Story 10: Media Upload](./story-10-media-upload.md)
