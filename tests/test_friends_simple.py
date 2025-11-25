"""
Simple friendship system tests
Tests core functionality to validate Story 8 implementation
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_send_friend_request(test_user_token, supabase_client):
    """Test AC1: Send friend request"""
    # Create a second user
    second_email = "friend_test_2@darezone.test"
    
    # Cleanup
    try:
        profiles = supabase_client.table("user_profiles").select("id").eq("email", second_email).execute()
        if profiles.data:
            user_id = profiles.data[0]["id"]
            supabase_client.table("friendships").delete().eq("requester_id", user_id).execute()
            supabase_client.table("friendships").delete().eq("addressee_id", user_id).execute()
            supabase_client.table("user_profiles").delete().eq("id", user_id).execute()
    except Exception:
        pass
    
    # Create second user
    response2 = client.post(
        "/api/v1/auth/signup",
        json={
            "email": second_email,
            "password": "TestPass123!",
            "display_name": "Friend Test 2",
        },
    )
    
    if response2.status_code != 201:
        pytest.skip(f"Failed to create second user: {response2.text}")
    
    user2_id = response2.json()["user"]["id"]
    
    # Test: Send friend request
    response = client.post(
        "/api/v1/friends/request",
        json={"addressee_id": user2_id},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["addressee_id"] == user2_id
    
    # Cleanup
    try:
        supabase_client.table("friendships").delete().eq("addressee_id", user2_id).execute()
        supabase_client.table("user_profiles").delete().eq("id", user2_id).execute()
    except Exception:
        pass


def test_list_friends(test_user_token):
    """Test AC3: List friends"""
    response = client.get(
        "/api/v1/friends",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "friends" in data
    assert "total" in data
    assert isinstance(data["friends"], list)


def test_search_users(test_user_token):
    """Test AC4: Search users"""
    response = client.get(
        "/api/v1/users/search?q=test",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_friend_requests(test_user_token):
    """Test listing pending requests"""
    response = client.get(
        "/api/v1/friends/requests",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "received" in data
    assert "sent" in data
    assert "received_count" in data
    assert "sent_count" in data


def test_friendship_endpoints_unauthorized():
    """Test that endpoints require authentication"""
    # Send request
    response = client.post(
        "/api/v1/friends/request",
        json={"addressee_id": "some-uuid"},
    )
    assert response.status_code == 403
    
    # List friends
    response = client.get("/api/v1/friends")
    assert response.status_code == 403
    
    # Search (already tested in users, but verify)
    response = client.get("/api/v1/users/search?q=test")
    assert response.status_code == 403
