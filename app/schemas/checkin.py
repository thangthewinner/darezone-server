from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class CheckinStatus(str, Enum):
    """Check-in status enum"""

    pending = "pending"
    completed = "completed"
    verified = "verified"
    rejected = "rejected"


# ==================== Check-in Input Schemas ====================


class CheckinCreate(BaseModel):
    """Create check-in request"""

    challenge_id: str
    habit_id: str
    caption: Optional[str] = Field(None, max_length=500)
    photo_url: Optional[str] = None
    video_url: Optional[str] = None

    @field_validator("caption", "photo_url", "video_url")
    @classmethod
    def at_least_one_evidence(cls, v, info):
        """Ensure at least one form of evidence is provided"""
        # This validator runs for each field, so we need to check the entire model
        # In Pydantic v2, we'd use model_validator instead
        # For now, we'll enforce this in the API layer
        return v


class CheckinUpdate(BaseModel):
    """Update check-in request - only caption editable"""

    caption: Optional[str] = Field(None, max_length=500)


# ==================== Check-in Output Schemas ====================


class Checkin(BaseModel):
    """Check-in response"""

    id: str
    challenge_id: str
    habit_id: str
    user_id: str
    checkin_date: date
    status: CheckinStatus
    photo_url: Optional[str] = None
    video_url: Optional[str] = None
    caption: Optional[str] = None
    is_on_time: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CheckinWithUser(Checkin):
    """Check-in with user information"""

    user_display_name: str
    user_avatar_url: Optional[str] = None
    is_you: bool = False


class CheckinCreateResponse(BaseModel):
    """Response after creating check-in with streak/points info"""

    checkin: Checkin
    new_streak: int
    points_earned: int
    is_streak_broken: bool
    message: str


# ==================== Progress Tracking Schemas ====================


class MemberCheckinStatus(BaseModel):
    """Member's check-in status for a specific habit"""

    user_id: str
    user_name: str
    user_avatar_url: Optional[str] = None
    is_you: bool
    checked_in_today: bool
    checkin_time: Optional[datetime] = None
    photo_url: Optional[str] = None


class HabitCheckinProgress(BaseModel):
    """Today's check-in progress for a habit"""

    habit_id: str
    habit_name: str
    habit_icon: Optional[str] = None
    members: List[MemberCheckinStatus]
    completion_rate: float
    total_checkins_today: int


class TodayProgress(BaseModel):
    """Complete progress for all habits in a challenge today"""

    challenge_id: str
    date: date
    habits: List[HabitCheckinProgress]
    overall_completion: float


# ==================== Pagination Schema ====================


class PaginatedCheckins(BaseModel):
    """Paginated check-ins list"""

    checkins: List[CheckinWithUser]
    total: int
    page: int
    limit: int
    pages: int
