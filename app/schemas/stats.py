from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime


class LeaderboardEntry(BaseModel):
    """Single entry in leaderboard"""

    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    points_earned: int
    current_streak: int
    completion_rate: float
    rank: int

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "display_name": "John Doe",
                "avatar_url": "https://...",
                "points_earned": 450,
                "current_streak": 15,
                "completion_rate": 95.5,
                "rank": 1,
            }
        }


class LeaderboardResponse(BaseModel):
    """Challenge leaderboard response"""

    leaderboard: List[LeaderboardEntry]
    sort_by: str = Field(..., description="Field used for sorting (points, streak, completion_rate)")
    total_members: int = Field(..., description="Total number of members in challenge")

    class Config:
        json_schema_extra = {
            "example": {
                "leaderboard": [
                    {
                        "user_id": "user-123",
                        "display_name": "John Doe",
                        "points_earned": 450,
                        "current_streak": 15,
                        "completion_rate": 95.5,
                        "rank": 1,
                    }
                ],
                "sort_by": "points",
                "total_members": 10,
            }
        }


class HabitStats(BaseModel):
    """Statistics for a single habit in a challenge"""

    habit_id: str
    habit_name: str
    total_checkins: int
    completion_rate: float


class ChallengeInfo(BaseModel):
    """Basic challenge information"""

    name: str
    start_date: date
    end_date: date
    duration_days: int
    status: str


class ChallengeStatsResponse(BaseModel):
    """Detailed challenge statistics"""

    challenge_id: str
    total_members: int
    active_members: int
    avg_completion_rate: float
    avg_points: float
    avg_streak: float
    total_checkins: int
    challenge_info: ChallengeInfo
    top_performers: List[LeaderboardEntry]
    habit_stats: List[HabitStats]

    class Config:
        json_schema_extra = {
            "example": {
                "challenge_id": "challenge-123",
                "total_members": 10,
                "active_members": 8,
                "avg_completion_rate": 85.5,
                "avg_points": 350.0,
                "avg_streak": 12.5,
                "total_checkins": 450,
                "challenge_info": {
                    "name": "30-Day Fitness",
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-30",
                    "duration_days": 30,
                    "status": "active",
                },
                "top_performers": [],
                "habit_stats": [],
            }
        }


class UserStats(BaseModel):
    """User statistics summary"""

    current_streak: int
    longest_streak: int
    total_check_ins: int
    total_challenges_completed: int
    points: int


class ActiveChallengeSum(BaseModel):
    """Summary of an active challenge"""

    challenge_id: str
    challenge_name: str
    current_streak: int
    points_earned: int
    completion_rate: float
    rank: int
    end_date: date


class RecentCompletion(BaseModel):
    """Recently completed challenge"""

    challenge_id: str
    challenge_name: str
    completion_rate: float
    points_earned: int
    rank: int
    end_date: date


class UserDashboardResponse(BaseModel):
    """User dashboard data"""

    user_stats: UserStats
    active_challenges: List[ActiveChallengeSum]
    recent_completions: List[RecentCompletion]
    achievements: List = Field(default_factory=list, description="Future: achievement system")

    class Config:
        json_schema_extra = {
            "example": {
                "user_stats": {
                    "current_streak": 15,
                    "longest_streak": 30,
                    "total_check_ins": 450,
                    "total_challenges_completed": 5,
                    "points": 2500,
                },
                "active_challenges": [
                    {
                        "challenge_id": "challenge-123",
                        "challenge_name": "30-Day Fitness",
                        "current_streak": 15,
                        "points_earned": 300,
                        "completion_rate": 95.0,
                        "rank": 2,
                        "end_date": "2025-02-15",
                    }
                ],
                "recent_completions": [],
                "achievements": [],
            }
        }


class ChallengeHistoryItem(BaseModel):
    """Single item in challenge history"""

    id: str
    name: str
    type: str
    status: str
    start_date: date
    end_date: date
    duration_days: int
    member_status: str = Field(..., description="User's status in this challenge (active, left, kicked)")
    completion_rate: Optional[float] = None
    points_earned: Optional[int] = None
    rank: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "challenge-123",
                "name": "30-Day Fitness",
                "type": "group",
                "status": "completed",
                "start_date": "2025-01-01",
                "end_date": "2025-01-30",
                "duration_days": 30,
                "member_status": "active",
                "completion_rate": 95.5,
                "points_earned": 450,
                "rank": 2,
            }
        }
