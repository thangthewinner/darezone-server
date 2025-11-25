"""
Notification Service
Handles creating notifications and sending push notifications via Expo
"""

import logging
from typing import Dict, Any, Optional
from supabase import Client
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


async def create_notification(
    supabase: Client,
    user_id: str,
    type: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    action_url: Optional[str] = None,
    send_push: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Create a notification in the database and optionally send push notification

    Args:
        supabase: Supabase client
        user_id: User ID to receive notification
        type: Notification type (must match notification_type enum)
        title: Notification title
        body: Notification body
        data: Optional JSON data payload
        action_url: Optional deep link URL
        send_push: Whether to send push notification (default: True)

    Returns:
        Created notification dict or None if failed
    """
    try:
        # Create notification in database
        notification_response = (
            supabase.table("notifications")
            .insert(
                {
                    "user_id": user_id,
                    "type": type,
                    "title": title,
                    "body": body,
                    "data": data or {},
                    "action_url": action_url,
                }
            )
            .execute()
        )

        if not notification_response.data:
            logger.error(f"Failed to create notification for user {user_id}")
            return None

        notification = notification_response.data[0]

        # Send push notification if enabled
        if send_push:
            await send_push_notification(supabase, user_id, title, body, data)

        return notification

    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        return None


async def send_push_notification(
    supabase: Client,
    user_id: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Send push notification via Expo Push API

    Args:
        supabase: Supabase client
        user_id: User ID to send push to
        title: Notification title
        body: Notification body
        data: Optional data payload

    Returns:
        Expo API response or None if failed
    """
    try:
        # Check if Expo is configured
        expo_token = getattr(settings, "EXPO_ACCESS_TOKEN", None)
        if not expo_token:
            logger.debug("Expo push notifications not configured, skipping")
            return None

        # Get user's push token
        user_response = (
            supabase.table("user_profiles")
            .select("push_token")
            .eq("id", user_id)
            .single()
            .execute()
        )

        if not user_response.data or not user_response.data.get("push_token"):
            logger.debug(f"No push token found for user {user_id}")
            return None

        push_token = user_response.data["push_token"]

        # Validate Expo push token format
        if not push_token.startswith("ExponentPushToken["):
            logger.warning(f"Invalid Expo push token format for user {user_id}")
            return None

        # Send via Expo Push API
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://exp.host/--/api/v2/push/send",
                headers={
                    "Authorization": f"Bearer {expo_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": push_token,
                    "title": title,
                    "body": body,
                    "data": data or {},
                    "sound": "default",
                    "priority": "high",
                    "badge": 1,
                },
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Push notification sent to user {user_id}")
                return result
            else:
                logger.error(
                    f"Failed to send push notification: {response.status_code} - {response.text}"
                )
                return None

    except httpx.TimeoutException:
        logger.error(f"Timeout sending push notification to user {user_id}")
        return None
    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return None


def create_notification_sync(
    supabase: Client,
    user_id: str,
    type: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    action_url: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Create notification synchronously (for use in non-async contexts)
    Does NOT send push notification

    Args:
        supabase: Supabase client
        user_id: User ID to receive notification
        type: Notification type
        title: Notification title
        body: Notification body
        data: Optional JSON data payload
        action_url: Optional deep link URL

    Returns:
        Created notification dict or None if failed
    """
    try:
        notification_response = (
            supabase.table("notifications")
            .insert(
                {
                    "user_id": user_id,
                    "type": type,
                    "title": title,
                    "body": body,
                    "data": data or {},
                    "action_url": action_url,
                }
            )
            .execute()
        )

        if not notification_response.data:
            logger.error(f"Failed to create notification for user {user_id}")
            return None

        return notification_response.data[0]

    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        return None
