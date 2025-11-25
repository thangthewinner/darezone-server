import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client
from typing import Dict, Any
from datetime import datetime
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.schemas.notification import (
    Notification,
    MarkNotificationsRead,
    UnreadCountResponse,
    PushTokenRegister,
)
from app.schemas.common import PaginationParams, PaginatedResponse, SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse[Notification])
async def list_notifications(
    unread_only: bool = Query(False, description="Filter to unread notifications only"),
    pagination: PaginationParams = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    List my notifications

    Returns paginated list of notifications for the current user.
    Can filter to show only unread notifications.

    Query Parameters:
    - unread_only: If true, only return unread notifications
    - page: Page number (default: 1)
    - limit: Items per page (default: 20)
    """
    user_id = current_user["id"]

    try:
        # Build query
        query = (
            supabase.table("notifications")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )

        if unread_only:
            query = query.eq("is_read", False)

        # Execute query with pagination
        response = query.range(
            pagination.offset, pagination.offset + pagination.limit - 1
        ).execute()

        # Get total count
        total = response.count if response.count is not None else 0

        # Convert to Notification models
        notifications = [Notification(**n) for n in response.data]

        return PaginatedResponse.create(
            items=notifications,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
        )

    except Exception as e:
        logger.error(f"Failed to list notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications",
        )


@router.get("/unread/count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get unread notification count

    Returns the number of unread notifications for the current user.
    Useful for displaying notification badges in the UI.
    """
    user_id = current_user["id"]

    try:
        response = (
            supabase.table("notifications")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )

        count = response.count if response.count is not None else 0

        return UnreadCountResponse(count=count)

    except Exception as e:
        logger.error(f"Failed to get unread count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count",
        )


@router.post("/mark-read", response_model=SuccessResponse)
async def mark_notifications_read(
    request: MarkNotificationsRead,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Mark notifications as read

    Marks multiple notifications as read in a single request.
    Only the owner of the notifications can mark them as read.

    Request Body:
    - notification_ids: List of notification IDs to mark as read
    """
    user_id = current_user["id"]

    try:
        # Update notifications
        response = (
            supabase.table("notifications")
            .update({"is_read": True, "read_at": datetime.utcnow().isoformat()})
            .in_("id", request.notification_ids)
            .eq("user_id", user_id)
            .execute()
        )

        # Count how many were updated
        updated_count = len(response.data) if response.data else 0

        return SuccessResponse(
            success=True,
            message=f"Marked {updated_count} notification(s) as read",
        )

    except Exception as e:
        logger.error(f"Failed to mark notifications as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read",
        )


@router.post("/mark-all-read", response_model=SuccessResponse)
async def mark_all_notifications_read(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Mark all notifications as read

    Marks all unread notifications as read for the current user.
    Convenient endpoint for "mark all as read" functionality.
    """
    user_id = current_user["id"]

    try:
        response = (
            supabase.table("notifications")
            .update({"is_read": True, "read_at": datetime.utcnow().isoformat()})
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )

        updated_count = len(response.data) if response.data else 0

        return SuccessResponse(
            success=True,
            message=f"Marked all {updated_count} notification(s) as read",
        )

    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read",
        )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Delete notification

    Deletes a specific notification. Only the owner of the notification can delete it.

    Path Parameters:
    - notification_id: ID of the notification to delete
    """
    user_id = current_user["id"]

    try:
        # Check if notification exists and belongs to user
        check_response = (
            supabase.table("notifications")
            .select("id")
            .eq("id", notification_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not check_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        # Delete notification
        supabase.table("notifications").delete().eq("id", notification_id).eq(
            "user_id", user_id
        ).execute()

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification",
        )


@router.post("/register-push-token", response_model=SuccessResponse)
async def register_push_token(
    request: PushTokenRegister,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Register Expo push notification token

    Registers or updates the user's Expo push token for receiving push notifications.

    Request Body:
    - token: Expo push token (format: ExponentPushToken[...])
    - device_type: Device type (default: "mobile")
    """
    user_id = current_user["id"]

    try:
        # Validate token format
        if not request.token.startswith("ExponentPushToken["):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Expo push token format",
            )

        # Update user profile with push token
        response = (
            supabase.table("user_profiles")
            .update({"push_token": request.token})
            .eq("id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )

        return SuccessResponse(
            success=True,
            message="Push token registered successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register push token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register push token",
        )


@router.delete("/push-token", response_model=SuccessResponse)
async def unregister_push_token(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Unregister push notification token

    Removes the user's push token, disabling push notifications.
    Useful when user logs out or disables notifications.
    """
    user_id = current_user["id"]

    try:
        response = (
            supabase.table("user_profiles")
            .update({"push_token": None})
            .eq("id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )

        return SuccessResponse(
            success=True,
            message="Push token unregistered successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister push token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister push token",
        )
