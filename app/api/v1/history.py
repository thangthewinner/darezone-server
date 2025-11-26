from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from typing import Optional
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.schemas.stats import (
    LeaderboardResponse,
    ChallengeStatsResponse,
    UserDashboardResponse,
    ChallengeHistoryItem,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/history", response_model=PaginatedResponse[ChallengeHistoryItem])
async def list_challenge_history(
    status: Optional[str] = Query(
        None,
        description="Filter by status: completed, failed, left, active",
        pattern="^(completed|failed|left|active)$",
    ),
    search: Optional[str] = Query(None, description="Search by challenge name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user=Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    List challenge history with filters
    
    **Filters:**
    - `status`: Filter by challenge status (completed, failed, left, active)
    - `search`: Search by challenge name (case-insensitive)
    
    **Returns:** Paginated list of challenges user is/was a member of
    """
    try:
        # Build query for challenges where user is/was member
        query = (
            supabase.table("challenge_member_stats")
            .select("*", count="exact")
            .eq("user_id", current_user["id"])
        )

        # Filter by status
        if status:
            if status == "left":
                query = query.in_("status", ["left", "kicked"])
            elif status == "active":
                query = query.eq("status", "active").eq("challenge_status", "active")
            elif status in ["completed", "failed"]:
                query = query.eq("challenge_status", status)

        # Search by name
        if search:
            query = query.ilike("challenge_name", f"%{search}%")

        # Order by most recent
        query = query.order("end_date", desc=True)

        # Execute count query
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0

        # Execute paginated query
        offset = (page - 1) * limit
        data_result = query.range(offset, offset + limit - 1).execute()

        # Transform data to match schema
        items = []
        for item in data_result.data:
            items.append(
                ChallengeHistoryItem(
                    id=item["challenge_id"],
                    name=item["challenge_name"],
                    type="group",  # Default, could be fetched from challenge table
                    status=item["challenge_status"],
                    start_date=item["start_date"],
                    end_date=item["end_date"],
                    duration_days=item["duration_days"],
                    member_status=item["status"],
                    completion_rate=item.get("completion_rate"),
                    points_earned=item.get("points_earned"),
                    rank=item.get("points_rank"),
                )
            )

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit if total > 0 else 0,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch challenge history: {str(e)}",
        )


@router.get("/stats/{challenge_id}", response_model=ChallengeStatsResponse)
async def get_challenge_stats(
    challenge_id: str,
    current_user=Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get detailed challenge statistics
    
    **Includes:**
    - Overall stats (avg completion, points, streak)
    - Top 10 performers
    - Per-habit statistics
    - Challenge information
    
    **Authorization:** Must be a member of the challenge
    """
    try:
        # Verify user is a member
        member_check = (
            supabase.table("challenge_members")
            .select("id")
            .eq("challenge_id", challenge_id)
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not member_check.data:
            raise HTTPException(
                status_code=403,
                detail="You must be a member of this challenge to view stats",
            )

        # Call RPC function to get stats
        result = supabase.rpc("get_challenge_stats", {"p_challenge_id": challenge_id}).execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="Challenge not found or no stats available",
            )

        stats_data = result.data

        # Parse and return
        return ChallengeStatsResponse(**stats_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch challenge stats: {str(e)}",
        )


@router.get("/leaderboard/{challenge_id}", response_model=LeaderboardResponse)
async def get_challenge_leaderboard(
    challenge_id: str,
    sort_by: str = Query(
        "points",
        description="Sort by: points, streak, or completion_rate",
        pattern="^(points|streak|completion_rate)$",
    ),
    current_user=Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get challenge leaderboard
    
    **Sorting Options:**
    - `points`: Sort by points earned (default)
    - `streak`: Sort by current streak
    - `completion_rate`: Sort by completion percentage
    
    **Returns:** Ranked list of all members
    
    **Authorization:** Must be a member of the challenge
    """
    try:
        # Verify user is a member
        member_check = (
            supabase.table("challenge_members")
            .select("id")
            .eq("challenge_id", challenge_id)
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not member_check.data:
            raise HTTPException(
                status_code=403,
                detail="You must be a member of this challenge to view leaderboard",
            )

        # Map sort_by to column name
        sort_column = {
            "points": "points_earned",
            "streak": "current_streak",
            "completion_rate": "completion_rate",
        }[sort_by]

        # Get leaderboard from materialized view
        result = (
            supabase.table("challenge_member_stats")
            .select(
                "user_id, display_name, avatar_url, points_earned, "
                "current_streak, completion_rate, points_rank"
            )
            .eq("challenge_id", challenge_id)
            .order(sort_column, desc=True)
            .execute()
        )

        # Add dynamic rank based on sort_by
        leaderboard = []
        for rank, member in enumerate(result.data, start=1):
            leaderboard.append(
                {
                    "user_id": member["user_id"],
                    "display_name": member["display_name"],
                    "avatar_url": member.get("avatar_url"),
                    "points_earned": member["points_earned"],
                    "current_streak": member["current_streak"],
                    "completion_rate": member["completion_rate"],
                    "rank": rank if sort_by != "points" else member["points_rank"],
                }
            )

        return LeaderboardResponse(
            leaderboard=leaderboard,
            sort_by=sort_by,
            total_members=len(leaderboard),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch leaderboard: {str(e)}",
        )


@router.get("/dashboard", response_model=UserDashboardResponse)
async def get_user_dashboard(
    current_user=Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get user dashboard data
    
    **Includes:**
    - Overall user statistics (streaks, points, total check-ins)
    - Active challenges summary
    - Recent completed challenges
    - Achievements (placeholder for future)
    
    **Returns:** Comprehensive dashboard data for the current user
    """
    try:
        # Call RPC function to get dashboard data
        result = supabase.rpc("get_user_dashboard", {"p_user_id": current_user["id"]}).execute()

        if not result.data:
            # Fallback: get basic profile data
            profile = (
                supabase.table("user_profiles")
                .select("current_streak, longest_streak, total_check_ins, total_challenges_completed, points")
                .eq("id", current_user["id"])
                .single()
                .execute()
            )

            return UserDashboardResponse(
                user_stats={
                    "current_streak": profile.data.get("current_streak", 0),
                    "longest_streak": profile.data.get("longest_streak", 0),
                    "total_check_ins": profile.data.get("total_check_ins", 0),
                    "total_challenges_completed": profile.data.get("total_challenges_completed", 0),
                    "points": profile.data.get("points", 0),
                },
                active_challenges=[],
                recent_completions=[],
                achievements=[],
            )

        dashboard_data = result.data

        return UserDashboardResponse(**dashboard_data)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard data: {str(e)}",
        )
