import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client
from typing import List, Dict, Any
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.schemas.user import (
    UserProfile,
    UserUpdate,
    UserPublicProfile,
    UserSearchResult,
    UserStats,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get current user's full profile with statistics

    Returns complete profile including:
    - Basic info (email, name, avatar)
    - Account settings
    - Statistics (streaks, points, challenges)

    Requires authentication.
    """
    profile = current_user["profile"]

    # Get detailed stats
    stats = await get_user_stats_data(current_user["id"], supabase)

    return UserProfile(
        id=profile["id"],
        email=profile["email"],
        full_name=profile.get("full_name"),
        display_name=profile.get("display_name"),
        avatar_url=profile.get("avatar_url"),
        bio=profile.get("bio"),
        account_type=profile.get("account_type", "b2c"),
        organization_id=profile.get("organization_id"),
        stats=stats,
        created_at=profile["created_at"],
        last_seen_at=profile.get("last_seen_at"),
    )


@router.patch("/me", response_model=UserProfile)
async def update_my_profile(
    update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Update current user's profile

    Updatable fields:
    - full_name (1-100 chars)
    - display_name (1-50 chars)
    - bio (max 500 chars)
    - avatar_url

    All fields are optional - only provided fields will be updated.

    Returns the updated profile with stats.
    """
    # Build update dict (only non-None values)
    update_data = {}
    if update.full_name is not None:
        update_data["full_name"] = update.full_name
    if update.display_name is not None:
        update_data["display_name"] = update.display_name
    if update.bio is not None:
        update_data["bio"] = update.bio
    if update.avatar_url is not None:
        update_data["avatar_url"] = update.avatar_url

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update provided",
        )

    try:
        # Update profile in database
        response = (
            supabase.table("user_profiles")
            .update(update_data)
            .eq("id", current_user["id"])
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile",
            )

        # Get updated stats
        stats = await get_user_stats_data(current_user["id"], supabase)

        updated_profile = response.data[0]
        return UserProfile(**updated_profile, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )


@router.get("/{user_id}", response_model=UserPublicProfile)
async def get_user_profile(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get public profile of another user

    Access Control:
    - Can view if you are friends (status = 'accepted')
    - Can view if in same active challenge
    - Cannot view strangers

    Returns limited public information (no email).

    Raises:
        403: If no relationship exists
        404: If user not found
    """
    # Check if viewing own profile
    if user_id == current_user["id"]:
        # Redirect to /me endpoint logic
        profile = current_user["profile"]
        stats = await get_user_stats_data(user_id, supabase)
        return UserPublicProfile(
            id=profile["id"],
            display_name=profile.get("display_name") or "You",
            avatar_url=profile.get("avatar_url"),
            bio=profile.get("bio"),
            stats=stats,
            is_you=True,
        )

    # Check access permission
    has_access = await check_user_access(current_user["id"], user_id, supabase)

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view profiles of friends or challenge members",
        )

    # Get user profile (public fields only)
    try:
        profile_response = (
            supabase.table("user_profiles")
            .select("id, display_name, avatar_url, bio")
            .eq("id", user_id)
            .single()
            .execute()
        )

        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        profile = profile_response.data

        # Get stats
        stats = await get_user_stats_data(user_id, supabase)

        return UserPublicProfile(
            id=profile["id"],
            display_name=profile.get("display_name") or "User",
            avatar_url=profile.get("avatar_url"),
            bio=profile.get("bio"),
            stats=stats,
            is_you=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile",
        )


@router.get("/search", response_model=List[UserSearchResult])
async def search_users(
    q: str = Query(..., min_length=2, max_length=50, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results to return"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Search users by display name or email

    Features:
    - Case-insensitive search
    - Searches both display_name and email
    - Excludes current user from results
    - Shows friendship status
    - Maximum 20 results (configurable)

    Query must be at least 2 characters.

    Returns list of matching users with friendship status.
    """
    try:
        # Build case-insensitive search pattern
        search_pattern = f"%{q}%"

        # Search users
        response = (
            supabase.table("user_profiles")
            .select("id, display_name, avatar_url, email")
            .or_(f"display_name.ilike.{search_pattern},email.ilike.{search_pattern}")
            .neq("id", current_user["id"])
            .limit(limit)
            .execute()
        )

        users = response.data

        if not users:
            return []

        # Get friendship status for all results
        user_ids = [u["id"] for u in users]

        # Query friendships
        friendships_response = (
            supabase.table("friendships")
            .select("requester_id, addressee_id, status")
            .or_(
                f"and(requester_id.eq.{current_user['id']},addressee_id.in.({','.join(user_ids)})),"
                f"and(addressee_id.eq.{current_user['id']},requester_id.in.({','.join(user_ids)}))"
            )
            .execute()
        )

        # Build friendship status map
        friendship_map = {}
        for friendship in friendships_response.data:
            other_id = (
                friendship["addressee_id"]
                if friendship["requester_id"] == current_user["id"]
                else friendship["requester_id"]
            )
            friendship_map[other_id] = friendship["status"]

        # Build search results
        results = []
        for user in users:
            friendship_status = friendship_map.get(user["id"])
            results.append(
                UserSearchResult(
                    id=user["id"],
                    display_name=user.get("display_name") or "User",
                    avatar_url=user.get("avatar_url"),
                    is_friend=friendship_status == "accepted",
                    friendship_status=friendship_status,
                    active_challenge_id=None,  # TODO: Implement in challenge story
                )
            )

        return results

    except Exception as e:
        logger.error(f"User search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


@router.get("/me/stats", response_model=UserStats)
async def get_my_stats(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get detailed statistics for current user

    Returns:
    - current_streak: Current consecutive days
    - longest_streak: Best streak ever
    - total_check_ins: Total check-ins completed
    - total_challenges_completed: Completed challenges count
    - points: Total points earned
    - active_challenges: Current active challenges count
    - friend_count: Number of accepted friends
    """
    return await get_user_stats_data(current_user["id"], supabase)


# ==================== Helper Functions ====================


async def get_user_stats_data(user_id: str, supabase: Client) -> UserStats:
    """
    Get comprehensive user statistics from database

    Combines data from:
    - user_profiles (streaks, check-ins, points)
    - challenge_members (active challenges)
    - friendships (friend count)
    """
    try:
        # Get profile stats
        profile_response = (
            supabase.table("user_profiles")
            .select(
                "current_streak, longest_streak, total_check_ins, "
                "total_challenges_completed, points"
            )
            .eq("id", user_id)
            .single()
            .execute()
        )

        if not profile_response.data:
            return UserStats()

        profile_data = profile_response.data

        # Count active challenges
        active_challenges_response = (
            supabase.table("challenge_members")
            .select("challenge_id", count="exact")
            .eq("user_id", user_id)
            .eq("status", "active")
            .execute()
        )

        active_challenges_count = active_challenges_response.count or 0

        # Count accepted friends
        friends_response = (
            supabase.table("friendships")
            .select("id", count="exact")
            .eq("status", "accepted")
            .or_(f"requester_id.eq.{user_id},addressee_id.eq.{user_id}")
            .execute()
        )

        friend_count = friends_response.count or 0

        return UserStats(
            current_streak=profile_data.get("current_streak", 0),
            longest_streak=profile_data.get("longest_streak", 0),
            total_check_ins=profile_data.get("total_check_ins", 0),
            total_challenges_completed=profile_data.get(
                "total_challenges_completed", 0
            ),
            points=profile_data.get("points", 0),
            active_challenges=active_challenges_count,
            friend_count=friend_count,
        )

    except Exception as e:
        logger.error(f"Failed to get user stats: {str(e)}")
        return UserStats()


async def check_user_access(
    current_user_id: str, target_user_id: str, supabase: Client
) -> bool:
    """
    Check if current user can view target user's profile

    Returns True if:
    - They are friends (status = 'accepted')
    - They are in the same active challenge

    Returns False otherwise.
    """
    try:
        # Check if friends
        friendship_response = (
            supabase.table("friendships")
            .select("id")
            .eq("status", "accepted")
            .or_(
                f"and(requester_id.eq.{current_user_id},addressee_id.eq.{target_user_id}),"
                f"and(addressee_id.eq.{current_user_id},requester_id.eq.{target_user_id})"
            )
            .execute()
        )

        if friendship_response.data:
            return True

        # Check if in same challenge
        # Get current user's active challenges
        my_challenges_response = (
            supabase.table("challenge_members")
            .select("challenge_id")
            .eq("user_id", current_user_id)
            .eq("status", "active")
            .execute()
        )

        if not my_challenges_response.data:
            return False

        challenge_ids = [c["challenge_id"] for c in my_challenges_response.data]

        # Check if target user is in any of those challenges
        shared_challenge_response = (
            supabase.table("challenge_members")
            .select("id")
            .eq("user_id", target_user_id)
            .in_("challenge_id", challenge_ids)
            .eq("status", "active")
            .execute()
        )

        return bool(shared_challenge_response.data)

    except Exception as e:
        logger.error(f"Failed to check user access: {str(e)}")
        return False
