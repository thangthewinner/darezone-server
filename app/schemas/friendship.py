from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class FriendshipStatus(str, Enum):
    """Friendship status enum matching database"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class FriendshipAction(str, Enum):
    """Actions for responding to friend requests"""

    ACCEPT = "accept"
    REJECT = "reject"
    BLOCK = "block"


class FriendRequestCreate(BaseModel):
    """Schema for sending a friend request"""

    addressee_id: str = Field(..., description="User ID to send friend request to")


class FriendRequestRespond(BaseModel):
    """Schema for responding to a friend request"""

    action: FriendshipAction = Field(
        ..., description="Action: accept, reject, or block"
    )


class FriendshipBase(BaseModel):
    """Base friendship schema"""

    id: str
    requester_id: str
    addressee_id: str
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FriendProfile(BaseModel):
    """Friend user profile with stats"""

    id: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    current_streak: int = 0
    points: int = 0
    active_challenges: int = 0
    friendship_id: str
    friendship_status: FriendshipStatus
    became_friends_at: datetime


class FriendRequest(BaseModel):
    """Pending friend request with requester info"""

    id: str
    requester_id: str
    requester_display_name: str
    requester_avatar_url: Optional[str] = None
    created_at: datetime
    status: FriendshipStatus = FriendshipStatus.PENDING


class FriendshipListResponse(BaseModel):
    """Response for listing friends"""

    friends: list[FriendProfile]
    total: int


class PendingRequestsResponse(BaseModel):
    """Response for listing pending requests"""

    received: list[FriendRequest]
    sent: list[FriendRequest]
    received_count: int
    sent_count: int
