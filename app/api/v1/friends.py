import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client
from typing import Dict, Any, List
from postgrest.exceptions import APIError
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.schemas.friendship import (
    FriendRequestCreate,
    FriendRequestRespond,
    FriendshipBase,
    FriendProfile,
    FriendRequest,
    FriendshipListResponse,
    PendingRequestsResponse,
    FriendshipStatus,
    FriendshipAction,
)
from app.schemas.common import SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/request", response_model=FriendshipBase, status_code=status.HTTP_201_CREATED
)
async def send_friend_request(
    request: FriendRequestCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Send a friend request to another user

    Validations:
    - Addressee must exist
    - Cannot send to self
    - No duplicate requests
    - Creates notification for addressee
    """
    user_id = current_user["id"]
    addressee_id = request.addressee_id

    # Validate: Cannot send to self
    if user_id == addressee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send friend request to yourself",
        )

    # Validate: Addressee exists
    try:
        addressee_response = (
            supabase.table("user_profiles")
            .select("id, display_name")
            .eq("id", addressee_id)
            .single()
            .execute()
        )

        if not addressee_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    except APIError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check for existing friendship in either direction
    existing_check = (
        supabase.table("friendships")
        .select("id, status, requester_id, addressee_id")
        .or_(
            f"and(requester_id.eq.{user_id},addressee_id.eq.{addressee_id}),"
            f"and(requester_id.eq.{addressee_id},addressee_id.eq.{user_id})"
        )
        .execute()
    )

    if existing_check.data:
        existing = existing_check.data[0]
        if existing["status"] == "accepted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already friends with this user",
            )
        elif existing["status"] == "pending":
            if existing["requester_id"] == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Friend request already sent",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This user has already sent you a friend request",
                )
        elif existing["status"] == "blocked":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot send friend request to this user",
            )

    # Create friendship record
    try:
        friendship_response = (
            supabase.table("friendships")
            .insert(
                {
                    "requester_id": user_id,
                    "addressee_id": addressee_id,
                    "status": "pending",
                }
            )
            .execute()
        )

        friendship = friendship_response.data[0]

        # Create notification for addressee
        try:
            supabase.table("notifications").insert(
                {
                    "user_id": addressee_id,
                    "type": "friend_request",
                    "title": "New friend request",
                    "message": f"{current_user['profile'].get('display_name', 'Someone')} sent you a friend request",
                    "data": {
                        "friendship_id": friendship["id"],
                        "requester_id": user_id,
                    },
                }
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to create notification: {str(e)}")

        return FriendshipBase(**friendship)

    except APIError as e:
        logger.error(f"Failed to create friendship: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send friend request",
        )


@router.post("/requests/{friendship_id}/respond", response_model=FriendshipBase)
async def respond_to_friend_request(
    friendship_id: str,
    response: FriendRequestRespond,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Respond to a friend request

    Actions:
    - accept: Accept the request, become friends
    - reject: Reject the request
    - block: Block the user

    Only the addressee can respond to a request.
    """
    user_id = current_user["id"]

    # Get the friendship record
    try:
        friendship_response = (
            supabase.table("friendships")
            .select("*")
            .eq("id", friendship_id)
            .single()
            .execute()
        )

        if not friendship_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friend request not found",
            )

        friendship = friendship_response.data

        # Validate: Only addressee can respond
        if friendship["addressee_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only respond to requests sent to you",
            )

        # Validate: Request must be pending
        if friendship["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot respond to {friendship['status']} request",
            )

        # Update friendship status based on action
        new_status = response.action.value
        updated_friendship = (
            supabase.table("friendships")
            .update({"status": new_status})
            .eq("id", friendship_id)
            .execute()
        )

        # If accepted, create notification for requester
        if response.action == FriendshipAction.ACCEPT:
            try:
                supabase.table("notifications").insert(
                    {
                        "user_id": friendship["requester_id"],
                        "type": "friend_accepted",
                        "title": "Friend request accepted",
                        "message": f"{current_user['profile'].get('display_name', 'Someone')} accepted your friend request",
                        "data": {
                            "friendship_id": friendship["id"],
                            "user_id": user_id,
                        },
                    }
                ).execute()
            except Exception as e:
                logger.warning(f"Failed to create notification: {str(e)}")

        return FriendshipBase(**updated_friendship.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to respond to friend request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to respond to friend request",
        )


@router.get("/", response_model=FriendshipListResponse)
async def list_friends(
    status_filter: str = Query(
        "accepted", description="Filter by status: accepted, pending, all"
    ),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    List user's friends

    Filters:
    - accepted: Only accepted friends (default)
    - pending: Only pending requests
    - all: All friendships
    """
    user_id = current_user["id"]

    try:
        # Build query to get friendships where user is either requester or addressee
        query = supabase.table("friendships").select(
            "id, requester_id, addressee_id, status, created_at, updated_at"
        )

        # Filter by user
        query = query.or_(f"requester_id.eq.{user_id},addressee_id.eq.{user_id}")

        # Filter by status
        if status_filter == "accepted":
            query = query.eq("status", "accepted")
        elif status_filter == "pending":
            query = query.eq("status", "pending")

        friendships_response = query.execute()

        if not friendships_response.data:
            return FriendshipListResponse(friends=[], total=0)

        # Get friend profiles
        friend_ids = []
        friendship_map = {}

        for friendship in friendships_response.data:
            # Determine who the friend is (the other person)
            friend_id = (
                friendship["addressee_id"]
                if friendship["requester_id"] == user_id
                else friendship["requester_id"]
            )
            friend_ids.append(friend_id)
            friendship_map[friend_id] = friendship

        # Fetch friend profiles
        profiles_response = (
            supabase.table("user_profiles")
            .select("id, display_name, avatar_url, bio, current_streak, points")
            .in_("id", friend_ids)
            .execute()
        )

        # Count active challenges for each friend
        friends = []
        for profile in profiles_response.data:
            friend_id = profile["id"]
            friendship = friendship_map[friend_id]

            # Count active challenges
            active_challenges_response = (
                supabase.table("challenge_members")
                .select("id", count="exact")
                .eq("user_id", friend_id)
                .in_(
                    "challenge_id",
                    supabase.table("challenges").select("id").eq("status", "active"),
                )
                .execute()
            )

            active_challenges = active_challenges_response.count or 0

            friends.append(
                FriendProfile(
                    id=profile["id"],
                    display_name=profile.get("display_name")
                    or profile.get("email", "User"),
                    avatar_url=profile.get("avatar_url"),
                    bio=profile.get("bio"),
                    current_streak=profile.get("current_streak", 0),
                    points=profile.get("points", 0),
                    active_challenges=active_challenges,
                    friendship_id=friendship["id"],
                    friendship_status=FriendshipStatus(friendship["status"]),
                    became_friends_at=friendship["created_at"],
                )
            )

        return FriendshipListResponse(friends=friends, total=len(friends))

    except Exception as e:
        logger.error(f"Failed to list friends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve friends list",
        )


@router.get("/requests", response_model=PendingRequestsResponse)
async def list_friend_requests(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    List pending friend requests

    Returns:
    - received: Requests sent to you (you need to respond)
    - sent: Requests you sent (waiting for response)
    """
    user_id = current_user["id"]

    try:
        # Get received requests (where user is addressee)
        received_response = (
            supabase.table("friendships")
            .select("id, requester_id, created_at")
            .eq("addressee_id", user_id)
            .eq("status", "pending")
            .execute()
        )

        received_requests = []
        if received_response.data:
            # Get requester profiles
            requester_ids = [r["requester_id"] for r in received_response.data]
            profiles_response = (
                supabase.table("user_profiles")
                .select("id, display_name, avatar_url")
                .in_("id", requester_ids)
                .execute()
            )

            profile_map = {p["id"]: p for p in profiles_response.data}

            for request in received_response.data:
                profile = profile_map.get(request["requester_id"], {})
                received_requests.append(
                    FriendRequest(
                        id=request["id"],
                        requester_id=request["requester_id"],
                        requester_display_name=profile.get("display_name", "User"),
                        requester_avatar_url=profile.get("avatar_url"),
                        created_at=request["created_at"],
                    )
                )

        # Get sent requests (where user is requester)
        sent_response = (
            supabase.table("friendships")
            .select("id, addressee_id, created_at")
            .eq("requester_id", user_id)
            .eq("status", "pending")
            .execute()
        )

        sent_requests = []
        if sent_response.data:
            # Get addressee profiles
            addressee_ids = [r["addressee_id"] for r in sent_response.data]
            profiles_response = (
                supabase.table("user_profiles")
                .select("id, display_name, avatar_url")
                .in_("id", addressee_ids)
                .execute()
            )

            profile_map = {p["id"]: p for p in profiles_response.data}

            for request in sent_response.data:
                profile = profile_map.get(request["addressee_id"], {})
                sent_requests.append(
                    FriendRequest(
                        id=request["id"],
                        requester_id=request["addressee_id"],
                        requester_display_name=profile.get("display_name", "User"),
                        requester_avatar_url=profile.get("avatar_url"),
                        created_at=request["created_at"],
                    )
                )

        return PendingRequestsResponse(
            received=received_requests,
            sent=sent_requests,
            received_count=len(received_requests),
            sent_count=len(sent_requests),
        )

    except Exception as e:
        logger.error(f"Failed to list friend requests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve friend requests",
        )


@router.delete("/{user_id}", response_model=SuccessResponse)
async def remove_friend(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Remove a friend

    Either party can remove the friendship.
    Deletes the friendship record completely.
    """
    current_user_id = current_user["id"]

    # Validate: Cannot remove self
    if current_user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself as a friend",
        )

    try:
        # Find friendship in either direction
        friendship_response = (
            supabase.table("friendships")
            .select("id, status")
            .or_(
                f"and(requester_id.eq.{current_user_id},addressee_id.eq.{user_id}),"
                f"and(requester_id.eq.{user_id},addressee_id.eq.{current_user_id})"
            )
            .execute()
        )

        if not friendship_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friendship not found",
            )

        friendship = friendship_response.data[0]

        # Delete the friendship
        supabase.table("friendships").delete().eq("id", friendship["id"]).execute()

        return SuccessResponse(
            success=True,
            message="Friend removed successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove friend: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove friend",
        )
