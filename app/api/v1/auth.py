from fastapi import APIRouter, Depends
from supabase import Client
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_user, get_current_active_user
from app.schemas.auth import TokenVerifyResponse, CurrentUserResponse
from app.schemas.common import SuccessResponse
from typing import Dict, Any

router = APIRouter()


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Verify JWT token and return user information

    This endpoint is primarily for testing and debugging.
    Returns user info if the token is valid.

    Requires:
        - Bearer token in Authorization header

    Returns:
        - valid: True if token is valid
        - user_id: User's unique identifier
        - email: User's email address
    """
    return TokenVerifyResponse(
        valid=True, user_id=current_user["id"], email=current_user["email"]
    )


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get current authenticated user's full profile

    Returns complete user profile including stats and metadata.
    Verifies that user has an active profile in the database.

    Requires:
        - Bearer token in Authorization header
        - User must have a profile in user_profiles table

    Returns:
        Complete user profile with:
        - Basic info (email, name, avatar)
        - Account type (b2c/b2b)
        - Stats (streaks, check-ins, points)
        - Timestamps

    Raises:
        - 401: Invalid or missing token
        - 403: User profile not found
        - 500: Database error
    """
    profile = current_user["profile"]

    return CurrentUserResponse(
        id=profile["id"],
        email=profile["email"],
        full_name=profile.get("full_name"),
        display_name=profile.get("display_name"),
        avatar_url=profile.get("avatar_url"),
        bio=profile.get("bio"),
        account_type=profile.get("account_type", "b2c"),
        stats={
            "current_streak": profile.get("current_streak", 0),
            "longest_streak": profile.get("longest_streak", 0),
            "total_check_ins": profile.get("total_check_ins", 0),
            "total_challenges_completed": profile.get("total_challenges_completed", 0),
            "points": profile.get("points", 0),
        },
        created_at=profile["created_at"],
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Logout current user

    Note: In Supabase, token invalidation is handled client-side.
    The frontend should clear the stored token from AsyncStorage.

    This endpoint can be used to log the logout event or perform
    any server-side cleanup if needed.

    Requires:
        - Bearer token in Authorization header

    Returns:
        - success: True
        - message: Confirmation message
    """
    # Optional: Log logout event or perform cleanup
    # For now, just return success
    # Client should clear token from storage

    return SuccessResponse(
        success=True,
        message="Logged out successfully. Please clear your auth token.",
    )
