"""
Tests for Notification System (Story 9)
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from supabase import Client

client = TestClient(app)


def test_list_notifications_empty(test_user_token):
    """Test listing notifications when user has none"""
    response = client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "pages" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 0


def test_list_notifications_unauthorized():
    """Test that listing notifications requires authentication"""
    response = client.get("/api/v1/notifications")

    assert response.status_code == 403


def test_get_unread_count(test_user_token):
    """Test getting unread notification count"""
    response = client.get(
        "/api/v1/notifications/unread/count",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "count" in data
    assert isinstance(data["count"], int)
    assert data["count"] >= 0


def test_get_unread_count_unauthorized():
    """Test that unread count requires authentication"""
    response = client.get("/api/v1/notifications/unread/count")

    assert response.status_code == 403


def test_register_push_token_valid(test_user_token):
    """Test registering a valid Expo push token"""
    response = client.post(
        "/api/v1/notifications/register-push-token",
        json={
            "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
            "device_type": "mobile",
        },
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "registered" in data["message"].lower()


def test_register_push_token_invalid_format(test_user_token):
    """Test that invalid push token format is rejected"""
    response = client.post(
        "/api/v1/notifications/register-push-token",
        json={
            "token": "invalid-token-format",
            "device_type": "mobile",
        },
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_register_push_token_unauthorized():
    """Test that registering push token requires authentication"""
    response = client.post(
        "/api/v1/notifications/register-push-token",
        json={
            "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
        },
    )

    assert response.status_code == 403


def test_unregister_push_token(test_user_token):
    """Test unregistering push token"""
    # First register a token
    client.post(
        "/api/v1/notifications/register-push-token",
        json={
            "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
        },
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    # Then unregister it
    response = client.delete(
        "/api/v1/notifications/push-token",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "unregistered" in data["message"].lower()


def test_mark_notifications_read(test_user_token, supabase_client: Client):
    """Test marking notifications as read"""
    # Create a test notification directly in DB
    notification = (
        supabase_client.table("notifications")
        .insert(
            {
                "user_id": get_user_id_from_token(test_user_token),
                "type": "friend_request",
                "title": "Test Notification",
                "body": "This is a test",
                "is_read": False,
            }
        )
        .execute()
    )

    notification_id = notification.data[0]["id"]

    # Mark as read
    response = client.post(
        "/api/v1/notifications/mark-read",
        json={"notification_ids": [notification_id]},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "marked" in data["message"].lower()

    # Verify it was marked as read
    updated = (
        supabase_client.table("notifications")
        .select("is_read")
        .eq("id", notification_id)
        .single()
        .execute()
    )

    assert updated.data["is_read"] is True

    # Cleanup
    supabase_client.table("notifications").delete().eq("id", notification_id).execute()


def test_mark_all_notifications_read(test_user_token, supabase_client: Client):
    """Test marking all notifications as read"""
    user_id = get_user_id_from_token(test_user_token)

    # Create multiple test notifications
    notifications = (
        supabase_client.table("notifications")
        .insert(
            [
                {
                    "user_id": user_id,
                    "type": "friend_request",
                    "title": "Test 1",
                    "body": "Body 1",
                    "is_read": False,
                },
                {
                    "user_id": user_id,
                    "type": "friend_accepted",
                    "title": "Test 2",
                    "body": "Body 2",
                    "is_read": False,
                },
            ]
        )
        .execute()
    )

    notification_ids = [n["id"] for n in notifications.data]

    # Mark all as read
    response = client.post(
        "/api/v1/notifications/mark-all-read",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Verify they were marked as read
    updated = (
        supabase_client.table("notifications")
        .select("is_read")
        .in_("id", notification_ids)
        .execute()
    )

    for notif in updated.data:
        assert notif["is_read"] is True

    # Cleanup
    for notif_id in notification_ids:
        supabase_client.table("notifications").delete().eq("id", notif_id).execute()


def test_delete_notification(test_user_token, supabase_client: Client):
    """Test deleting a notification"""
    # Create a test notification
    notification = (
        supabase_client.table("notifications")
        .insert(
            {
                "user_id": get_user_id_from_token(test_user_token),
                "type": "friend_request",
                "title": "Test Notification",
                "body": "This will be deleted",
            }
        )
        .execute()
    )

    notification_id = notification.data[0]["id"]

    # Delete it
    response = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 204

    # Verify it was deleted
    check = (
        supabase_client.table("notifications")
        .select("id")
        .eq("id", notification_id)
        .execute()
    )

    assert len(check.data) == 0


def test_delete_notification_not_found(test_user_token):
    """Test deleting a non-existent notification"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"

    response = client.delete(
        f"/api/v1/notifications/{fake_uuid}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404


def test_list_notifications_with_pagination(test_user_token, supabase_client: Client):
    """Test pagination of notifications"""
    user_id = get_user_id_from_token(test_user_token)

    # Create multiple notifications
    notifications = []
    for i in range(5):
        notif = (
            supabase_client.table("notifications")
            .insert(
                {
                    "user_id": user_id,
                    "type": "friend_request",
                    "title": f"Test {i}",
                    "body": f"Body {i}",
                }
            )
            .execute()
        )
        notifications.append(notif.data[0]["id"])

    # Test pagination
    response = client.get(
        "/api/v1/notifications?page=1&limit=2",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) <= 2
    assert data["limit"] == 2
    assert data["page"] == 1

    # Cleanup
    for notif_id in notifications:
        supabase_client.table("notifications").delete().eq("id", notif_id).execute()


def test_list_notifications_unread_only(test_user_token, supabase_client: Client):
    """Test filtering to unread notifications only"""
    user_id = get_user_id_from_token(test_user_token)

    # Create read and unread notifications
    notifications = (
        supabase_client.table("notifications")
        .insert(
            [
                {
                    "user_id": user_id,
                    "type": "friend_request",
                    "title": "Unread",
                    "body": "Not read yet",
                    "is_read": False,
                },
                {
                    "user_id": user_id,
                    "type": "friend_accepted",
                    "title": "Read",
                    "body": "Already read",
                    "is_read": True,
                },
            ]
        )
        .execute()
    )

    notification_ids = [n["id"] for n in notifications.data]

    # Get only unread
    response = client.get(
        "/api/v1/notifications?unread_only=true",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # All returned notifications should be unread
    for notif in data["items"]:
        assert notif["is_read"] is False

    # Cleanup
    for notif_id in notification_ids:
        supabase_client.table("notifications").delete().eq("id", notif_id).execute()


def test_notification_types():
    """Test that all notification types are supported"""
    from app.schemas.notification import NotificationType

    expected_types = [
        "friend_request",
        "friend_accepted",
        "challenge_invite",
        "challenge_started",
        "challenge_completed",
        "hitch_reminder",
        "streak_milestone",
        "member_joined",
        "member_left",
    ]

    for type_name in expected_types:
        assert hasattr(NotificationType, type_name.upper())


# Helper function
def get_user_id_from_token(token: str) -> str:
    """Extract user ID from test token"""
    # Get user info via API
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()["user"]["id"]
