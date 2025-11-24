import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client
from typing import List, Dict, Any, Optional
from datetime import date
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.schemas.checkin import (
    CheckinCreate,
    CheckinUpdate,
    Checkin,
    CheckinCreateResponse,
    CheckinWithUser,
    HabitCheckinProgress,
    MemberCheckinStatus,
    PaginatedCheckins,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/", response_model=CheckinCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_checkin(
    checkin: CheckinCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Create daily check-in with automatic streak/points calculation

    Workflow:
    1. Validates user is challenge member
    2. Checks no duplicate check-in today
    3. Calculates streak based on last check-in
    4. Awards points (10 base, 20 for streak continuation)
    5. Updates member and user stats atomically

    Uses RPC function to ensure data consistency.
    """
    try:
        # Validate at least one evidence provided
        if not checkin.photo_url and not checkin.video_url and not checkin.caption:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one evidence (photo/video/caption) required",
            )

        # Call RPC function for atomic check-in creation
        result = supabase.rpc(
            "create_checkin_with_streak_update",
            {
                "p_challenge_id": checkin.challenge_id,
                "p_habit_id": checkin.habit_id,
                "p_user_id": current_user["id"],
                "p_photo_url": checkin.photo_url,
                "p_video_url": checkin.video_url,
                "p_caption": checkin.caption,
            },
        ).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create check-in",
            )

        rpc_result = result.data[0]

        # Get created check-in details
        checkin_response = (
            supabase.table("check_ins")
            .select("*")
            .eq("id", rpc_result["checkin_id"])
            .single()
            .execute()
        )

        if not checkin_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Check-in created but failed to retrieve",
            )

        # Build response message
        message = "Check-in successful! "
        if rpc_result["is_streak_broken"]:
            message += "Your streak was reset. "
        else:
            message += f"Current streak: {rpc_result['new_streak']} days! "
        message += f"Earned {rpc_result['points_earned']} points."

        return CheckinCreateResponse(
            checkin=Checkin(**checkin_response.data),
            new_streak=rpc_result["new_streak"],
            points_earned=rpc_result["points_earned"],
            is_streak_broken=rpc_result["is_streak_broken"],
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already checked in for this habit today",
            )
        elif "not an active member" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this challenge",
            )
        else:
            logger.error(f"Failed to create check-in: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create check-in: {str(e)}",
            )


@router.get("/", response_model=PaginatedCheckins)
async def list_my_checkins(
    challenge_id: Optional[str] = Query(None, description="Filter by challenge ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    List my check-ins with optional challenge filter

    Features:
    - Pagination support
    - Filter by challenge_id
    - Sorted by checkin_date DESC
    - Includes user display name and avatar
    """
    try:
        # Build base query
        query = (
            supabase.table("check_ins")
            .select("*, user_profiles!inner(display_name, avatar_url)", count="exact")
            .eq("user_id", current_user["id"])
            .order("checkin_date", desc=True)
        )

        # Apply challenge filter if provided
        if challenge_id:
            query = query.eq("challenge_id", challenge_id)

        # Execute query to get count
        count_result = query.execute()
        total = count_result.count or 0

        # Get paginated data
        offset = (page - 1) * limit
        data_result = query.range(offset, offset + limit - 1).execute()

        # Format response
        checkins = []
        for item in data_result.data:
            user_profile = item.get("user_profiles", {})
            checkins.append(
                CheckinWithUser(
                    **item,
                    user_display_name=user_profile.get("display_name") or "User",
                    user_avatar_url=user_profile.get("avatar_url"),
                    is_you=True,
                )
            )

        pages = (total + limit - 1) // limit if total > 0 else 0

        return PaginatedCheckins(
            checkins=checkins, total=total, page=page, limit=limit, pages=pages
        )

    except Exception as e:
        logger.error(f"Failed to list check-ins: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list check-ins",
        )


@router.get("/{checkin_id}", response_model=Checkin)
async def get_checkin(
    checkin_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get check-in details

    Access Control:
    - Only accessible by challenge members
    - Enforced via membership verification
    """
    try:
        # Get check-in
        checkin_response = (
            supabase.table("check_ins")
            .select("*")
            .eq("id", checkin_id)
            .single()
            .execute()
        )

        if not checkin_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found"
            )

        checkin_data = checkin_response.data

        # Verify user is challenge member
        member_check = (
            supabase.table("challenge_members")
            .select("id")
            .eq("challenge_id", checkin_data["challenge_id"])
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this challenge",
            )

        return Checkin(**checkin_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get check-in: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get check-in",
        )


@router.patch("/{checkin_id}", response_model=Checkin)
async def update_checkin(
    checkin_id: str,
    update: CheckinUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Update check-in (edit caption only)

    Rules:
    - Only owner can edit
    - Only within same day (today)
    - Only caption can be updated
    """
    try:
        # Get check-in
        checkin_response = (
            supabase.table("check_ins")
            .select("*")
            .eq("id", checkin_id)
            .single()
            .execute()
        )

        if not checkin_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found"
            )

        checkin_data = checkin_response.data

        # Verify ownership
        if checkin_data["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not your check-in"
            )

        # Verify same day
        if str(checkin_data["checkin_date"]) != str(date.today()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only edit check-ins from today",
            )

        # Update caption
        update_data = {}
        if update.caption is not None:
            update_data["caption"] = update.caption
        update_data["updated_at"] = "NOW()"

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update provided",
            )

        update_response = (
            supabase.table("check_ins")
            .update(update_data)
            .eq("id", checkin_id)
            .execute()
        )

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update check-in",
            )

        return Checkin(**update_response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update check-in: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update check-in",
        )


@router.delete("/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkin(
    checkin_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Delete check-in

    Rules:
    - Only owner can delete
    - TODO: Revert streak/points if same day
    - For now, just deletes the check-in

    Note: Proper revert logic should be implemented in future iterations
    """
    try:
        # Get check-in
        checkin_response = (
            supabase.table("check_ins")
            .select("*")
            .eq("id", checkin_id)
            .single()
            .execute()
        )

        if not checkin_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found"
            )

        checkin_data = checkin_response.data

        # Verify ownership
        if checkin_data["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not your check-in"
            )

        # TODO: Implement revert logic for same-day deletions
        # - Recalculate streak
        # - Deduct points
        # - Update member/user stats
        # For Phase 1, we'll just delete the check-in

        # Delete check-in
        supabase.table("check_ins").delete().eq("id", checkin_id).execute()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete check-in: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete check-in",
        )


@router.get(
    "/challenges/{challenge_id}/today", response_model=List[HabitCheckinProgress]
)
async def get_today_checkins(
    challenge_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get today's check-in status for all habits and members

    Used for "Who's checked in?" UI

    Returns:
    - List of habits with member completion status
    - Completion rate per habit
    - Real-time accurate data

    Access: Only challenge members can view
    """
    try:
        # Verify user is challenge member
        member_check = (
            supabase.table("challenge_members")
            .select("id")
            .eq("challenge_id", challenge_id)
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this challenge",
            )

        # Get challenge habits
        habits_response = (
            supabase.table("challenge_habits")
            .select("habit_id, habits!inner(name, icon)")
            .eq("challenge_id", challenge_id)
            .order("display_order")
            .execute()
        )

        habits = habits_response.data

        # Get active members
        members_response = (
            supabase.table("challenge_members")
            .select("user_id, user_profiles!inner(display_name, avatar_url)")
            .eq("challenge_id", challenge_id)
            .eq("status", "active")
            .order("joined_at")
            .execute()
        )

        members = members_response.data

        # Get today's check-ins
        today = date.today()
        checkins_response = (
            supabase.table("check_ins")
            .select("habit_id, user_id, created_at, photo_url")
            .eq("challenge_id", challenge_id)
            .eq("checkin_date", str(today))
            .execute()
        )

        checkins = checkins_response.data

        # Build checkin map: {habit_id}_{user_id} -> checkin
        checkin_map = {}
        for checkin in checkins:
            key = f"{checkin['habit_id']}_{checkin['user_id']}"
            checkin_map[key] = checkin

        # Build progress for each habit
        progress_list = []

        for habit in habits:
            habit_id = habit["habit_id"]
            habit_data = habit.get("habits", {})

            member_statuses = []
            checked_count = 0

            for member in members:
                user_id = member["user_id"]
                user_profile = member.get("user_profiles", {})
                key = f"{habit_id}_{user_id}"
                checkin = checkin_map.get(key)

                is_checked_in = checkin is not None
                if is_checked_in:
                    checked_count += 1

                member_statuses.append(
                    MemberCheckinStatus(
                        user_id=user_id,
                        user_name=user_profile.get("display_name") or "User",
                        user_avatar_url=user_profile.get("avatar_url"),
                        is_you=user_id == current_user["id"],
                        checked_in_today=is_checked_in,
                        checkin_time=checkin.get("created_at") if checkin else None,
                        photo_url=checkin.get("photo_url") if checkin else None,
                    )
                )

            # Calculate completion rate
            total_members = len(members)
            completion_rate = (
                (checked_count / total_members * 100) if total_members > 0 else 0
            )

            progress_list.append(
                HabitCheckinProgress(
                    habit_id=habit_id,
                    habit_name=habit_data.get("name") or "Unknown Habit",
                    habit_icon=habit_data.get("icon"),
                    members=member_statuses,
                    completion_rate=round(completion_rate, 2),
                    total_checkins_today=checked_count,
                )
            )

        return progress_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get today's check-ins: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get today's check-ins",
        )
