"""
Security and authentication helpers
Supabase Auth integration with JWT verification
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from app.core.dependencies import get_supabase_client
from app.core.exceptions import unauthorized_exception

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme for Swagger docs
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client),
) -> Dict[str, Any]:
    """
    Verify JWT token and return current user

    Args:
        credentials: Bearer token from Authorization header
        supabase: Supabase client instance

    Returns:
        Dict containing user ID, email, and metadata

    Raises:
        HTTPException: 401 if token invalid or expired
    """
    token = credentials.credentials

    try:
        # Verify token with Supabase Auth
        response = supabase.auth.get_user(token)

        if not response or not response.user:
            logger.warning("Invalid token: no user found")
            raise unauthorized_exception("Invalid authentication credentials")

        user = response.user

        # Return user data
        return {
            "id": user.id,
            "email": user.email,
            "user_metadata": user.user_metadata or {},
            "app_metadata": user.app_metadata or {},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise unauthorized_exception("Could not validate credentials")


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
) -> Dict[str, Any]:
    """
    Get current user and verify they have active profile in database
    Auto-creates profile if it doesn't exist

    Args:
        current_user: User from JWT token
        supabase: Supabase client instance

    Returns:
        Dict containing user auth data + profile data

    Raises:
        HTTPException: 500 if database error
    """
    try:
        # Check if user profile exists
        response = (
            supabase.table("user_profiles")
            .select("*")
            .eq("id", current_user["id"])
            .execute()
        )

        # If profile doesn't exist, create it
        if not response.data or len(response.data) == 0:
            logger.info(f"Creating profile for user {current_user['id']}")
            
            # Create new profile
            new_profile = {
                "id": current_user["id"],
                "email": current_user["email"],
                "display_name": current_user.get("user_metadata", {}).get("display_name") or current_user["email"].split("@")[0],
                "account_type": "b2c",  # Default to B2C
            }
            
            create_response = (
                supabase.table("user_profiles")
                .insert(new_profile)
                .execute()
            )
            
            if not create_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user profile",
                )
            
            profile = create_response.data[0]
        else:
            profile = response.data[0]

        # Combine auth user + profile data
        return {**current_user, "profile": profile}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information",
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    supabase: Client = Depends(get_supabase_client),
) -> Optional[Dict[str, Any]]:
    """
    Get current user if token present, None otherwise
    For optional authentication endpoints

    Args:
        credentials: Optional bearer token
        supabase: Supabase client instance

    Returns:
        User dict if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        return None
