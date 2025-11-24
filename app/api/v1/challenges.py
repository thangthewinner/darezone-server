import logging
import random
import string
from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client
from typing import List, Dict, Any, Optional
from datetime import date
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.schemas.challenge import (
    ChallengeCreate,
    ChallengeUpdate,
    ChallengeList,
    ChallengeDetail,
    ChallengeMember,
    ChallengeHabit,
    JoinChallengeRequest,
    PaginatedChallenges,
    MemberStats,
    ChallengeProgress,
    MemberProgress,
    HabitProgress,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChallengeDetail, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    challenge: ChallengeCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Create a new challenge

    Workflow:
    1. Validate habits exist
    2. Generate unique invite code
    3. Create challenge record
    4. Link habits to challenge
    5. Auto-add creator as member with 'creator' role

    Returns the complete challenge with invite code.
    """
    try:
        # Validate habits exist
        habits_response = (
            supabase.table("habits")
            .select("id, name, icon, description, category")
            .in_("id", challenge.habit_ids)
            .execute()
        )

        if len(habits_response.data) != len(challenge.habit_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some habit IDs not found",
            )

        # Generate unique invite code
        invite_code = await generate_unique_invite_code(supabase)

        # Create challenge
        challenge_data = {
            "name": challenge.name,
            "description": challenge.description,
            "type": challenge.type.value,
            "status": "pending",
            "start_date": str(challenge.start_date),
            "end_date": str(challenge.end_date),
            "invite_code": invite_code,
            "created_by": current_user["id"],
            "checkin_type": challenge.checkin_type.value,
            "require_evidence": challenge.require_evidence,
            "max_members": challenge.max_members,
            "is_public": challenge.is_public,
            "member_count": 0,
        }

        challenge_response = (
            supabase.table("challenges").insert(challenge_data).execute()
        )

        if not challenge_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create challenge",
            )

        challenge_record = challenge_response.data[0]
        challenge_id = challenge_record["id"]

        # Add habits to challenge
        for idx, habit_id in enumerate(challenge.habit_ids):
            supabase.table("challenge_habits").insert(
                {
                    "challenge_id": challenge_id,
                    "habit_id": habit_id,
                    "display_order": idx,
                }
            ).execute()

        # Add creator as member
        supabase.table("challenge_members").insert(
            {
                "challenge_id": challenge_id,
                "user_id": current_user["id"],
                "role": "creator",
                "status": "active",
                "hitch_count": 2,
            }
        ).execute()

        # Update member count
        supabase.table("challenges").update({"member_count": 1}).eq(
            "id", challenge_id
        ).execute()

        # Get complete challenge details
        return await get_challenge_details(challenge_id, current_user["id"], supabase)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create challenge",
        )


@router.get("/", response_model=PaginatedChallenges)
async def list_challenges(
    status_filter: Optional[str] = Query(
        None, description="Filter by status (pending, active, completed, etc.)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    List my challenges

    Features:
    - Pagination support
    - Filter by status
    - Shows my role and status in each challenge
    - Sorted by created_at DESC
    """
    try:
        # Get my memberships
        memberships_query = (
            supabase.table("challenge_members")
            .select("challenge_id, role, status")
            .eq("user_id", current_user["id"])
        )

        # Apply status filter if provided
        if status_filter:
            memberships_query = memberships_query.eq("status", status_filter)

        memberships_response = memberships_query.execute()
        memberships = memberships_response.data

        if not memberships:
            return PaginatedChallenges(
                challenges=[], total=0, page=page, limit=limit, pages=0
            )

        # Get challenge IDs
        challenge_ids = [m["challenge_id"] for m in memberships]

        # Build membership map
        membership_map = {m["challenge_id"]: m for m in memberships}

        # Get challenges with pagination
        offset = (page - 1) * limit

        challenges_response = (
            supabase.table("challenges")
            .select("*", count="exact")
            .in_("id", challenge_ids)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        challenges = challenges_response.data
        total = challenges_response.count or 0

        # Build response
        challenge_list = []
        for challenge in challenges:
            membership = membership_map.get(challenge["id"])
            challenge_list.append(
                ChallengeList(
                    **challenge,
                    invite_code=challenge["invite_code"]
                    if membership and membership["role"] == "creator"
                    else None,
                    my_role=membership["role"] if membership else None,
                    my_status=membership["status"] if membership else None,
                )
            )

        pages = (total + limit - 1) // limit if total > 0 else 0

        return PaginatedChallenges(
            challenges=challenge_list, total=total, page=page, limit=limit, pages=pages
        )

    except Exception as e:
        logger.error(f"Failed to list challenges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list challenges",
        )


@router.get("/{challenge_id}", response_model=ChallengeDetail)
async def get_challenge(
    challenge_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get challenge details

    Returns complete challenge information including:
    - All members with stats
    - All habits
    - My membership info

    Access: Only challenge members can view details (enforced by RLS)
    """
    try:
        return await get_challenge_details(challenge_id, current_user["id"], supabase)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get challenge",
        )


@router.post("/join", response_model=ChallengeDetail)
async def join_challenge(
    request: JoinChallengeRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Join a challenge via invite code

    Workflow:
    1. Find challenge by invite code
    2. Validate not already a member
    3. Check max members limit
    4. Add member with 'member' role
    5. Increment member count
    6. Send notification to creator

    Returns the challenge details.
    """
    try:
        # Find challenge by invite code
        challenge_response = (
            supabase.table("challenges")
            .select("*")
            .eq("invite_code", request.invite_code)
            .single()
            .execute()
        )

        if not challenge_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite code"
            )

        challenge = challenge_response.data

        # Check if already a member
        existing_response = (
            supabase.table("challenge_members")
            .select("id, status")
            .eq("challenge_id", challenge["id"])
            .eq("user_id", current_user["id"])
            .execute()
        )

        if existing_response.data:
            existing_member = existing_response.data[0]
            if existing_member["status"] == "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Already a member of this challenge",
                )
            elif existing_member["status"] == "left":
                # Rejoin: update status to active
                supabase.table("challenge_members").update(
                    {"status": "active", "hitch_count": 2}
                ).eq("id", existing_member["id"]).execute()

                return await get_challenge_details(
                    challenge["id"], current_user["id"], supabase
                )

        # Check max members limit
        if challenge["member_count"] >= challenge["max_members"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge is full",
            )

        # Add member
        supabase.table("challenge_members").insert(
            {
                "challenge_id": challenge["id"],
                "user_id": current_user["id"],
                "role": "member",
                "status": "active",
                "hitch_count": 2,
            }
        ).execute()

        # Increment member count
        new_count = challenge["member_count"] + 1
        supabase.table("challenges").update({"member_count": new_count}).eq(
            "id", challenge["id"]
        ).execute()

        # Send notification to creator
        await send_member_joined_notification(
            supabase, challenge["created_by"], current_user, challenge["name"]
        )

        return await get_challenge_details(
            challenge["id"], current_user["id"], supabase
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to join challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join challenge",
        )


@router.post("/{challenge_id}/leave", response_model=Dict[str, str])
async def leave_challenge(
    challenge_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Leave a challenge

    Rules:
    - Creator cannot leave (must delete challenge instead)
    - Sets status to 'left'
    - Preserves stats for history
    - Decrements member count
    - Notifies other active members

    Returns success message.
    """
    try:
        # Get membership
        membership_response = (
            supabase.table("challenge_members")
            .select("id, role, status")
            .eq("challenge_id", challenge_id)
            .eq("user_id", current_user["id"])
            .single()
            .execute()
        )

        if not membership_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not a member of this challenge",
            )

        membership = membership_response.data

        # Check if creator
        if membership["role"] == "creator":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Creator cannot leave challenge. Delete the challenge instead.",
            )

        # Check if already left
        if membership["status"] == "left":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already left this challenge",
            )

        # Update status to left
        from datetime import datetime

        supabase.table("challenge_members").update(
            {"status": "left", "left_at": datetime.utcnow().isoformat()}
        ).eq("id", membership["id"]).execute()

        # Decrement member count
        challenge_response = (
            supabase.table("challenges")
            .select("member_count, name, created_by")
            .eq("id", challenge_id)
            .single()
            .execute()
        )

        if challenge_response.data:
            challenge = challenge_response.data
            new_count = max(0, challenge["member_count"] - 1)
            supabase.table("challenges").update({"member_count": new_count}).eq(
                "id", challenge_id
            ).execute()

            # Notify creator
            await send_member_left_notification(
                supabase, challenge["created_by"], current_user, challenge["name"]
            )

        return {"message": "Successfully left challenge"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to leave challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave challenge",
        )


@router.patch("/{challenge_id}", response_model=ChallengeDetail)
async def update_challenge(
    challenge_id: str,
    update: ChallengeUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Update challenge details

    Permissions:
    - Only creator or admin can update
    - Can change: name, description, status, max_members, is_public

    Returns updated challenge details.
    """
    try:
        # Check membership and role
        membership_response = (
            supabase.table("challenge_members")
            .select("role")
            .eq("challenge_id", challenge_id)
            .eq("user_id", current_user["id"])
            .single()
            .execute()
        )

        if not membership_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this challenge",
            )

        role = membership_response.data["role"]
        if role not in ["creator", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only creator or admin can update challenge",
            )

        # Build update data
        update_data = {}
        if update.name is not None:
            update_data["name"] = update.name
        if update.description is not None:
            update_data["description"] = update.description
        if update.status is not None:
            update_data["status"] = update.status.value
        if update.max_members is not None:
            update_data["max_members"] = update.max_members
        if update.is_public is not None:
            update_data["is_public"] = update.is_public

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update provided",
            )

        # Update challenge
        update_response = (
            supabase.table("challenges")
            .update(update_data)
            .eq("id", challenge_id)
            .execute()
        )

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update challenge",
            )

        return await get_challenge_details(challenge_id, current_user["id"], supabase)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update challenge",
        )


@router.get("/{challenge_id}/members", response_model=List[ChallengeMember])
async def get_challenge_members(
    challenge_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get challenge members list

    Returns list of all members with their stats and status.

    Access: Only challenge members can view members list.
    """
    try:
        # Verify membership
        await verify_challenge_membership(challenge_id, current_user["id"], supabase)

        # Get members
        members = await get_challenge_members_list(challenge_id, supabase)

        return members

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get challenge members",
        )


@router.get("/{challenge_id}/progress", response_model=ChallengeProgress)
async def get_challenge_progress(
    challenge_id: str,
    target_date: Optional[date] = Query(
        None, description="Target date (default: today)"
    ),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get today's progress for all members

    Shows:
    - Which habits each member has completed
    - Overall completion percentage
    - Individual member progress

    Used for "Who's checked in?" UI

    Access: Only challenge members can view progress.
    """
    try:
        # Verify membership
        await verify_challenge_membership(challenge_id, current_user["id"], supabase)

        # Use today if no date provided
        if target_date is None:
            from datetime import datetime

            target_date = datetime.utcnow().date()

        # Get challenge habits
        habits_response = (
            supabase.table("challenge_habits")
            .select("habit_id, habits(name)")
            .eq("challenge_id", challenge_id)
            .execute()
        )

        habits = habits_response.data
        total_habits = len(habits)
        habit_map = {h["habit_id"]: h["habits"]["name"] for h in habits}

        # Get active members
        members_response = (
            supabase.table("challenge_members")
            .select("user_id, user_profiles(display_name, avatar_url)")
            .eq("challenge_id", challenge_id)
            .eq("status", "active")
            .execute()
        )

        members = members_response.data

        # Get check-ins for target date
        checkins_response = (
            supabase.table("checkins")
            .select("user_id, habit_id, created_at")
            .eq("challenge_id", challenge_id)
            .eq("date", str(target_date))
            .eq("status", "completed")
            .execute()
        )

        checkins = checkins_response.data

        # Build checkin map: user_id -> {habit_id: checkin}
        checkin_map: Dict[str, Dict[str, Any]] = {}
        for checkin in checkins:
            user_id = checkin["user_id"]
            if user_id not in checkin_map:
                checkin_map[user_id] = {}
            checkin_map[user_id][checkin["habit_id"]] = checkin

        # Build member progress
        member_progress_list = []
        total_completed = 0

        for member in members:
            user_id = member["user_id"]
            user_checkins = checkin_map.get(user_id, {})

            habit_progress = []
            completed_count = 0

            for habit_id, habit_name in habit_map.items():
                checkin = user_checkins.get(habit_id)
                is_completed = checkin is not None

                if is_completed:
                    completed_count += 1

                habit_progress.append(
                    HabitProgress(
                        habit_id=habit_id,
                        habit_name=habit_name,
                        completed=is_completed,
                        checked_in_at=checkin["created_at"] if checkin else None,
                    )
                )

            completion_pct = (
                (completed_count / total_habits * 100) if total_habits > 0 else 0
            )

            member_progress_list.append(
                MemberProgress(
                    user_id=user_id,
                    display_name=member["user_profiles"]["display_name"] or "User",
                    avatar_url=member["user_profiles"].get("avatar_url"),
                    habits=habit_progress,
                    total_completed=completed_count,
                    completion_percentage=round(completion_pct, 2),
                )
            )

            total_completed += completed_count

        # Calculate overall completion
        max_possible = len(members) * total_habits
        overall_completion = (
            (total_completed / max_possible * 100) if max_possible > 0 else 0
        )

        return ChallengeProgress(
            challenge_id=challenge_id,
            date=target_date,
            members=member_progress_list,
            total_habits=total_habits,
            overall_completion=round(overall_completion, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get challenge progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get challenge progress",
        )


# ==================== Helper Functions ====================


async def generate_unique_invite_code(supabase: Client, max_attempts: int = 10) -> str:
    """
    Generate a unique 6-character invite code

    Uses alphanumeric characters (excluding confusing ones like 0, O, I, 1)
    Retries if code already exists
    """
    # Characters without confusing ones
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace("0", "").replace("O", "").replace("I", "").replace("1", "")

    for _ in range(max_attempts):
        code = "".join(random.choices(chars, k=6))

        # Check if code exists
        existing = (
            supabase.table("challenges").select("id").eq("invite_code", code).execute()
        )

        if not existing.data:
            return code

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to generate unique invite code",
    )


async def get_challenge_details(
    challenge_id: str, user_id: str, supabase: Client
) -> ChallengeDetail:
    """
    Get complete challenge details including members and habits

    Raises 404 if challenge not found or user is not a member
    """
    # Get challenge
    challenge_response = (
        supabase.table("challenges")
        .select("*")
        .eq("id", challenge_id)
        .single()
        .execute()
    )

    if not challenge_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found"
        )

    challenge = challenge_response.data

    # Get my membership
    my_membership_response = (
        supabase.table("challenge_members")
        .select(
            "role, status, current_streak, longest_streak, total_checkins, points_earned, hitch_count"
        )
        .eq("challenge_id", challenge_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not my_membership_response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this challenge",
        )

    my_membership = my_membership_response.data

    # Get all members
    members = await get_challenge_members_list(challenge_id, supabase)

    # Get habits
    habits_response = (
        supabase.table("challenge_habits")
        .select(
            "habit_id, display_order, custom_name, custom_icon, custom_description, "
            "total_checkins, completion_rate, habits(id, name, icon, description, category)"
        )
        .eq("challenge_id", challenge_id)
        .order("display_order")
        .execute()
    )

    habits = []
    for h in habits_response.data:
        habit_data = h["habits"]
        habits.append(
            ChallengeHabit(
                id=habit_data["id"],
                name=h.get("custom_name") or habit_data["name"],
                icon=h.get("custom_icon") or habit_data.get("icon"),
                description=h.get("custom_description")
                or habit_data.get("description"),
                category=habit_data.get("category"),
                display_order=h["display_order"],
                custom_name=h.get("custom_name"),
                custom_icon=h.get("custom_icon"),
                custom_description=h.get("custom_description"),
                total_checkins=h.get("total_checkins", 0),
                completion_rate=float(h.get("completion_rate", 0)),
            )
        )

    return ChallengeDetail(
        **challenge,
        members=members,
        habits=habits,
        my_role=my_membership["role"],
        my_status=my_membership["status"],
        my_stats=MemberStats(
            current_streak=my_membership.get("current_streak", 0),
            longest_streak=my_membership.get("longest_streak", 0),
            total_checkins=my_membership.get("total_checkins", 0),
            points_earned=my_membership.get("points_earned", 0),
            hitch_count=my_membership.get("hitch_count", 2),
        ),
    )


async def get_challenge_members_list(
    challenge_id: str, supabase: Client
) -> List[ChallengeMember]:
    """Get list of challenge members with stats"""
    members_response = (
        supabase.table("challenge_members")
        .select(
            "id, user_id, role, status, current_streak, longest_streak, "
            "total_checkins, points_earned, hitch_count, joined_at, left_at, "
            "last_checkin_at, user_profiles(display_name, avatar_url)"
        )
        .eq("challenge_id", challenge_id)
        .order("joined_at")
        .execute()
    )

    members = []
    for m in members_response.data:
        members.append(
            ChallengeMember(
                id=m["id"],
                user_id=m["user_id"],
                display_name=m["user_profiles"]["display_name"] or "User",
                avatar_url=m["user_profiles"].get("avatar_url"),
                role=m["role"],
                status=m["status"],
                stats=MemberStats(
                    current_streak=m.get("current_streak", 0),
                    longest_streak=m.get("longest_streak", 0),
                    total_checkins=m.get("total_checkins", 0),
                    points_earned=m.get("points_earned", 0),
                    hitch_count=m.get("hitch_count", 2),
                ),
                joined_at=m["joined_at"],
                left_at=m.get("left_at"),
                last_checkin_at=m.get("last_checkin_at"),
            )
        )

    return members


async def verify_challenge_membership(
    challenge_id: str, user_id: str, supabase: Client
) -> None:
    """
    Verify user is a member of the challenge

    Raises 403 if not a member
    """
    membership_response = (
        supabase.table("challenge_members")
        .select("id")
        .eq("challenge_id", challenge_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not membership_response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this challenge",
        )


async def send_member_joined_notification(
    supabase: Client, creator_id: str, joined_user: Dict, challenge_name: str
) -> None:
    """Send notification when new member joins"""
    try:
        display_name = joined_user["profile"].get("display_name") or "A user"
        supabase.table("notifications").insert(
            {
                "user_id": creator_id,
                "type": "member_joined",
                "title": "New Member!",
                "body": f"{display_name} joined your challenge '{challenge_name}'",
                "data": {"challenge_name": challenge_name},
            }
        ).execute()
    except Exception as e:
        logger.warning(f"Failed to send notification: {str(e)}")


async def send_member_left_notification(
    supabase: Client, creator_id: str, left_user: Dict, challenge_name: str
) -> None:
    """Send notification when member leaves"""
    try:
        display_name = left_user["profile"].get("display_name") or "A user"
        supabase.table("notifications").insert(
            {
                "user_id": creator_id,
                "type": "member_left",
                "title": "Member Left",
                "body": f"{display_name} left your challenge '{challenge_name}'",
                "data": {"challenge_name": challenge_name},
            }
        ).execute()
    except Exception as e:
        logger.warning(f"Failed to send notification: {str(e)}")
