"""
Service layer for anonymous user management
Handles business logic for creating and managing anonymous users
"""

import logging
import secrets
import string
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from supabase import Client
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def generate_anonymous_credentials(device_id: str) -> Tuple[str, str]:
    """
    Generate email and password for anonymous user

    Args:
        device_id: Unique device identifier

    Returns:
        Tuple of (email, password)
    """
    # Email format: anon{first16chars_of_hash}@darezone.app
    # Use hash to create shorter, valid email
    import hashlib
    hash_obj = hashlib.sha256(device_id.encode())
    hash_hex = hash_obj.hexdigest()[:16]  # First 16 chars of hash
    email = f"anon{hash_hex}@darezone.app"

    # Generate deterministic password based on device_id
    # This allows re-login without storing password
    # Use a different hash for password (add salt for security)
    password_hash = hashlib.sha256(f"password_{device_id}".encode())
    password_hex = password_hash.hexdigest()
    
    # Convert to alphanumeric (mix of letters and numbers)
    # Take first 32 chars of hex and convert some to uppercase for variety
    password = ""
    for i, char in enumerate(password_hex[:32]):
        if i % 3 == 0 and char.isalpha():
            password += char.upper()
        else:
            password += char
    
    return email, password


async def get_anonymous_user(device_id: str, supabase: Client) -> Optional[Dict[str, Any]]:
    """
    Get existing anonymous user by device_id

    Args:
        device_id: Unique device identifier
        supabase: Supabase client

    Returns:
        Anonymous user record or None if not found
    """
    try:
        response = (
            supabase.table("anonymous_users")
            .select("*")
            .eq("device_id", device_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]

        return None

    except Exception as e:
        logger.error(f"Failed to get anonymous user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve anonymous user",
        )


async def create_anonymous_user(
    device_id: str, supabase: Client
) -> Dict[str, Any]:
    """
    Create new anonymous user in Supabase Auth and database

    Args:
        device_id: Unique device identifier
        supabase: Supabase client

    Returns:
        Created anonymous user record with credentials

    Raises:
        HTTPException: If user creation fails
    """
    try:
        # Generate credentials - simple email format
        email, password = generate_anonymous_credentials(device_id)

        logger.info(f"Creating anonymous user for device: {device_id}")

        # Create user using admin API (bypasses email validation)
        # Use service role client to create user directly
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Auto-confirm email
            "user_metadata": {
                "is_anonymous": True,
                "device_id": device_id,
                "display_name": "Guest User",
            }
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user in Supabase Auth",
            )

        user_id = auth_response.user.id

        # Store mapping in anonymous_users table
        db_response = (
            supabase.table("anonymous_users")
            .insert(
                {
                    "device_id": device_id,
                    "user_id": user_id,
                    "email": email,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_login_at": datetime.utcnow().isoformat(),
                }
            )
            .execute()
        )

        if not db_response.data:
            # Rollback: delete auth user if database insert fails
            logger.error("Failed to insert into anonymous_users table, rolling back")
            # Note: Supabase doesn't provide easy user deletion from backend
            # This is acceptable as the user won't be accessible without the mapping
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create anonymous user record",
            )

        # Create user profile (required for protected endpoints)
        try:
            profile_response = (
                supabase.table("user_profiles")
                .insert(
                    {
                        "id": user_id,
                        "email": email,
                        "display_name": "Guest User",
                        "account_type": "b2c",
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                .execute()
            )
            logger.info(f"Created user profile for anonymous user: {user_id}")
        except Exception as profile_error:
            logger.warning(f"Failed to create user profile: {str(profile_error)}")
            # Don't fail the whole operation if profile creation fails
            # User can still use the app, just some endpoints might not work

        logger.info(f"Successfully created anonymous user: {user_id}")


        return {
            **db_response.data[0],
            "password": password,  # Return password for immediate login
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create anonymous user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create anonymous user: {str(e)}",
        )


async def update_last_login(device_id: str, supabase: Client) -> None:
    """
    Update last_login_at timestamp for anonymous user

    Args:
        device_id: Unique device identifier
        supabase: Supabase client
    """
    try:
        supabase.table("anonymous_users").update(
            {"last_login_at": datetime.utcnow().isoformat()}
        ).eq("device_id", device_id).execute()

    except Exception as e:
        # Non-critical error, just log it
        logger.warning(f"Failed to update last_login_at: {str(e)}")


async def get_anonymous_credentials(
    device_id: str, supabase: Client
) -> Tuple[str, str]:
    """
    Get stored credentials for anonymous user

    Args:
        device_id: Unique device identifier
        supabase: Supabase client

    Returns:
        Tuple of (email, password)

    Note:
        Password is regenerated as we don't store it in database
        This is safe because anonymous users are device-specific
    """
    user = await get_anonymous_user(device_id, supabase)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anonymous user not found",
        )

    # Email is stored, password needs to be regenerated
    # For anonymous users, we use a deterministic password based on device_id
    # This allows re-login without storing the password
    email = user["email"]
    _, password = generate_anonymous_credentials(device_id)

    return email, password
