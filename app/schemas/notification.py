from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Notification type enum matching database"""

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
    """Schema for creating notification (internal use)"""

    user_id: str = Field(..., description="User ID to send notification to")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(
        ..., min_length=1, max_length=200, description="Notification title"
    )
    body: str = Field(
        ..., min_length=1, max_length=500, description="Notification body"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional data payload"
    )
    action_url: Optional[str] = Field(default=None, description="Deep link URL")


class Notification(BaseModel):
    """Notification response schema"""

    id: str
    user_id: str
    type: NotificationType
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MarkNotificationsRead(BaseModel):
    """Mark multiple notifications as read"""

    notification_ids: List[str] = Field(
        ..., min_items=1, description="List of notification IDs to mark as read"
    )


class UnreadCountResponse(BaseModel):
    """Unread notification count response"""

    count: int = Field(..., ge=0, description="Number of unread notifications")


class PushTokenRegister(BaseModel):
    """Register Expo push notification token"""

    token: str = Field(..., min_length=1, description="Expo push token")
    device_type: str = Field(
        default="mobile", description="Device type (mobile, tablet, etc.)"
    )
