from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserStats(BaseModel):
    """User statistics"""

    current_streak: int = 0
    longest_streak: int = 0
    total_check_ins: int = 0
    total_challenges_completed: int = 0
    points: int = 0
    active_challenges: int = 0
    friend_count: int = 0


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)


class UserUpdate(BaseModel):
    """User profile update - all fields optional"""

    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None

    @field_validator("display_name", "full_name")
    @classmethod
    def validate_not_empty(cls, v):
        """Ensure strings are not just whitespace"""
        if v is not None and not v.strip():
            raise ValueError("Cannot be empty or whitespace only")
        return v.strip() if v else v


class UserProfile(UserBase):
    """Full user profile response"""

    id: str
    avatar_url: Optional[str] = None
    account_type: str = "b2c"
    organization_id: Optional[str] = None
    stats: Optional[UserStats] = None
    created_at: datetime
    last_seen_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserPublicProfile(BaseModel):
    """Public user profile (visible to friends/challenge members)"""

    id: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    stats: UserStats
    is_you: bool = False


class UserSearchResult(BaseModel):
    """User search result with friendship status"""

    id: str
    display_name: str
    avatar_url: Optional[str] = None
    is_friend: bool = False
    friendship_status: Optional[str] = None
    active_challenge_id: Optional[str] = None
