from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ChallengeType(str, Enum):
    """Challenge type enum (B2C-only, program type removed)"""

    individual = "individual"
    group = "group"
    # program = "program"  # B2B feature removed


class ChallengeStatus(str, Enum):
    """Challenge status enum"""

    pending = "pending"
    active = "active"
    completed = "completed"
    failed = "failed"
    archived = "archived"


class CheckinType(str, Enum):
    """Check-in evidence type"""

    photo = "photo"
    video = "video"
    caption = "caption"
    any = "any"


class MemberRole(str, Enum):
    """Member role enum"""

    creator = "creator"
    admin = "admin"
    member = "member"


class MemberStatus(str, Enum):
    """Member status enum"""

    pending = "pending"
    active = "active"
    left = "left"
    kicked = "kicked"


# ==================== Challenge Schemas ====================


class ChallengeCreate(BaseModel):
    """Create challenge request"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    type: ChallengeType = ChallengeType.individual
    start_date: date
    end_date: date
    habit_ids: List[str] = Field(..., min_length=1, max_length=4)
    checkin_type: CheckinType = CheckinType.photo
    require_evidence: bool = True
    max_members: int = Field(10, ge=1, le=50)
    is_public: bool = False

    @field_validator("habit_ids")
    @classmethod
    def validate_habit_ids(cls, v):
        """Validate habit IDs list"""
        if not v:
            raise ValueError("At least one habit is required")
        if len(v) > 4:
            raise ValueError("Maximum 4 habits allowed per challenge")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate habit IDs not allowed")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate end date is after start date"""
        if "start_date" in info.data:
            start_date = info.data["start_date"]
            if v <= start_date:
                raise ValueError("End date must be after start date")
            duration = (v - start_date).days
            if duration > 365:
                raise ValueError("Challenge duration cannot exceed 365 days")
        return v


class ChallengeUpdate(BaseModel):
    """Update challenge request - all fields optional"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[ChallengeStatus] = None
    max_members: Optional[int] = Field(None, ge=1, le=50)
    is_public: Optional[bool] = None


class JoinChallengeRequest(BaseModel):
    """Join challenge via invite code"""

    invite_code: str = Field(..., min_length=6, max_length=6)

    @field_validator("invite_code")
    @classmethod
    def validate_invite_code(cls, v):
        """Validate invite code format"""
        if not v.isalnum():
            raise ValueError("Invite code must be alphanumeric")
        return v.upper()


# ==================== Member Schemas ====================


class MemberStats(BaseModel):
    """Member statistics within a challenge"""

    current_streak: int = 0
    longest_streak: int = 0
    total_checkins: int = 0
    points_earned: int = 0
    hitch_count: int = 2


class ChallengeMember(BaseModel):
    """Challenge member with stats"""

    id: str
    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    role: MemberRole
    status: MemberStatus
    stats: MemberStats
    joined_at: datetime
    left_at: Optional[datetime] = None
    last_checkin_at: Optional[datetime] = None


# ==================== Habit Schemas ====================


class HabitBase(BaseModel):
    """Base habit schema"""

    id: str
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class ChallengeHabit(HabitBase):
    """Habit with challenge-specific data"""

    display_order: int = 0
    custom_name: Optional[str] = None
    custom_icon: Optional[str] = None
    custom_description: Optional[str] = None
    total_checkins: int = 0
    completion_rate: float = 0.0


# ==================== Challenge Response Schemas ====================


class ChallengeBase(BaseModel):
    """Base challenge fields"""

    id: str
    name: str
    description: Optional[str] = None
    type: ChallengeType
    status: ChallengeStatus
    start_date: date
    end_date: date
    duration_days: int
    checkin_type: CheckinType
    require_evidence: bool
    is_public: bool
    max_members: int
    member_count: int
    current_streak: int
    created_at: datetime
    created_by: str


class ChallengeList(ChallengeBase):
    """Challenge in list view (summary)"""

    invite_code: Optional[str] = None  # Only for creator
    my_role: Optional[MemberRole] = None
    my_status: Optional[MemberStatus] = None


class ChallengeDetail(ChallengeBase):
    """Challenge detail view with members and habits"""

    invite_code: str  # Visible to all members
    members: List[ChallengeMember] = []
    habits: List[ChallengeHabit] = []
    my_role: MemberRole
    my_status: MemberStatus
    my_stats: MemberStats


# ==================== Progress Schemas ====================


class HabitProgress(BaseModel):
    """Habit completion status for a member"""

    habit_id: str
    habit_name: str
    completed: bool
    checked_in_at: Optional[datetime] = None


class MemberProgress(BaseModel):
    """Member's progress for today"""

    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    habits: List[HabitProgress] = []
    total_completed: int = 0
    completion_percentage: float = 0.0


class ChallengeProgress(BaseModel):
    """Today's progress for all members"""

    challenge_id: str
    date: date
    members: List[MemberProgress] = []
    total_habits: int
    overall_completion: float = 0.0


# ==================== Pagination Schemas ====================


class PaginatedChallenges(BaseModel):
    """Paginated challenge list"""

    challenges: List[ChallengeList]
    total: int
    page: int
    limit: int
    pages: int
