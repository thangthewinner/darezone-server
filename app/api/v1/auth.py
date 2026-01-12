from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_user, get_current_active_user
from app.schemas.auth import TokenVerifyResponse, CurrentUserResponse
from app.schemas.anonymous import AnonymousLoginRequest, AnonymousLoginResponse
from app.schemas.common import SuccessResponse
from app.services import anonymous_service
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/anonymous-login", response_model=AnonymousLoginResponse)
async def anonymous_login(
    request: AnonymousLoginRequest,
    supabase: Client = Depends(get_supabase_client),
):
    """
    Create or login anonymous user based on device ID

    This endpoint enables users to use the app without traditional registration.
    Each device gets a unique anonymous account that persists across app sessions.

    **Flow:**
    1. Check if device_id already has an anonymous user
    2. If exists: Return existing user's token
    3. If new: Create new anonymous user and return token

    **Device ID:**
    - Must be a valid UUID v4 format
    - Generated once per device and stored locally
    - Used to identify the same user across app sessions

    **Anonymous User:**
    - Email format: anon_{device_id}@darezone.app
    - Secure random password (not exposed to client)
    - Can be upgraded to real account later

    Args:
        request: Contains device_id (UUID)
        supabase: Supabase client

    Returns:
        AnonymousLoginResponse with:
        - access_token: JWT token for API authentication
        - user_id: Unique user identifier
        - is_anonymous: Always True
        - created_at: User creation timestamp
        - is_new_user: True if newly created, False if existing

    Raises:
        400: Invalid device_id format
        500: Failed to create/retrieve user

    Example:
        ```
        POST /api/v1/auth/anonymous-login
        {
            "device_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        ```
    """
    try:
        device_id = request.device_id
        logger.info(f"Anonymous login request for device: {device_id}")

        # Check if anonymous user already exists
        existing_user = await anonymous_service.get_anonymous_user(device_id, supabase)

        if existing_user:
            # Existing user - sign in and update last_login
            logger.info(f"Existing anonymous user found: {existing_user['user_id']}")

            # Get credentials (email stored, password regenerated)
            email, password = await anonymous_service.get_anonymous_credentials(
                device_id, supabase
            )

            # Sign in with Supabase Auth
            auth_response = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate access token",
                )

            # Update last login timestamp
            await anonymous_service.update_last_login(device_id, supabase)

            return AnonymousLoginResponse(
                access_token=auth_response.session.access_token,
                token_type="bearer",
                user_id=existing_user["user_id"],
                is_anonymous=True,
                created_at=existing_user["created_at"],
                is_new_user=False,
            )

        else:
            # New user - create anonymous account
            logger.info(f"Creating new anonymous user for device: {device_id}")

            new_user = await anonymous_service.create_anonymous_user(device_id, supabase)

            # Sign in to get access token
            email = new_user["email"]
            password = new_user["password"]

            auth_response = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate access token for new user",
                )

            return AnonymousLoginResponse(
                access_token=auth_response.session.access_token,
                token_type="bearer",
                user_id=new_user["user_id"],
                is_anonymous=True,
                created_at=new_user["created_at"],
                is_new_user=True,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Anonymous login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anonymous login failed: {str(e)}",
        )


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
