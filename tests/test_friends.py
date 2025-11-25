import pytest
from fastapi.testclient import TestClient
from app.main import app
from supabase import Client

client = TestClient(app)


@pytest.fixture(scope="module")
def user1_setup(supabase_client: Client):
    """Create first test user"""
    email = "friend_test_user1@darezone.test"
    password = "TestPass123!@#"

    # Cleanup first
    try:
        profiles = supabase_client.table("user_profiles").select("id").eq("email", email).execute()
        if profiles.data:
            user_id = profiles.data[0]["id"]
            supabase_client.table("friendships").delete().eq("requester_id", user_id).execute()
            supabase_client.table("friendships").delete().eq("addressee_id", user_id).execute()
            supabase_client.table("user_profiles").delete().eq("id", user_id).execute()
    except Exception:
        pass

    # Create user via signup
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "full_name": "Friend Test User One",
            "display_name": "FriendUser1",
        },
    )

    if response.status_code != 201:
        pytest.skip(f"Failed to create user1: {response.text}")

    data = response.json()
    yield {
        "token": data["access_token"],
        "id": data["user"]["id"],
        "email": email,
    }

    # Cleanup
    try:
        supabase_client.table("friendships").delete().eq("requester_id", data["user"]["id"]).execute()
        supabase_client.table("friendships").delete().eq("addressee_id", data["user"]["id"]).execute()
        supabase_client.table("user_profiles").delete().eq("id", data["user"]["id"]).execute()
    except Exception:
        pass


@pytest.fixture(scope="module")
def user2_setup(supabase_client: Client):
    """Create second test user"""
    email = "friend_test_user2@darezone.test"
    password = "TestPass123!@#"

    # Cleanup first
    try:
        profiles = supabase_client.table("user_profiles").select("id").eq("email", email).execute()
        if profiles.data:
            user_id = profiles.data[0]["id"]
            supabase_client.table("friendships").delete().eq("requester_id", user_id).execute()
            supabase_client.table("friendships").delete().eq("addressee_id", user_id).execute()
            supabase_client.table("user_profiles").delete().eq("id", user_id).execute()
    except Exception:
        pass

    # Create user via signup
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "full_name": "Friend Test User Two",
            "display_name": "FriendUser2",
        },
    )

    if response.status_code != 201:
        pytest.skip(f"Failed to create user2: {response.text}")

    data = response.json()
    yield {
        "token": data["access_token"],
        "id": data["user"]["id"],
        "email": email,
    }

    # Cleanup
    try:
        supabase_client.table("friendships").delete().eq("requester_id", data["user"]["id"]).execute()
        supabase_client.table("friendships").delete().eq("addressee_id", data["user"]["id"]).execute()
        supabase_client.table("user_profiles").delete().eq("id", data["user"]["id"]).execute()
    except Exception:
        pass


@pytest.fixture(scope="module")
def friendship_id(user1_setup, user2_setup):
    """Create a pending friendship and return its ID"""
    response = client.post(
        "/api/v1/friends/request",
        json={"addressee_id": user2_setup["id"]},
        headers={"Authorization": f"Bearer {user1_setup['token']}"},
    )
    
    if response.status_code == 201:
        return response.json()["id"]
    return None


class TestFriendRequest:
    """Test sending friend requests"""

    def test_send_friend_request_success(self, user1_setup, user2_setup):
        """Test successfully sending a friend request"""
        response = client.post(
            "/api/v1/friends/request",
            json={"addressee_id": user2_setup["id"]},
            headers={"Authorization": f"Bearer {user1_setup['token']}"},
        )

        assert response.status_code == 201, f"Failed: {response.text}"
        data = response.json()

        assert data["requester_id"] == user1_setup["id"]
        assert data["addressee_id"] == user2_setup["id"]
        assert data["status"] == "pending"
        assert "id" in data

    def test_send_friend_request_to_self(self, user1_setup):
        """Test that sending request to self is rejected"""
        response = client.post(
            "/api/v1/friends/request",
            json={"addressee_id": user1_setup["id"]},
            headers={"Authorization": f"Bearer {user1_setup['token']}"},
        )

        assert response.status_code == 400
        assert "yourself" in response.json()["detail"].lower()

    def test_send_duplicate_friend_request(self, user1_setup, user2_setup, friendship_id):
        """Test that duplicate requests are rejected"""
        response = client.post(
            "/api/v1/friends/request",
            json={"addressee_id": user2_setup["id"]},
            headers={"Authorization": f"Bearer {user1_setup['token']}"},
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_send_friend_request_user_not_found(self, user1_setup):
        """Test sending request to non-existent user"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            "/api/v1/friends/request",
            json={"addressee_id": fake_uuid},
            headers={"Authorization": f"Bearer {user1_setup['token']}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_send_friend_request_unauthorized(self, user2_setup):
        """Test sending request without authentication"""
        response = client.post(
            "/api/v1/friends/request",
            json={"addressee_id": user2_setup["id"]},
        )

        assert response.status_code == 403


class TestFriendRequestsListing:
    """Test listing pending friend requests"""

    def test_list_friend_requests_received(self):
        """Test listing received friend requests"""
        response = client.get(
            "/api/v1/friends/requests",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["received_count"] >= 1
        assert len(data["received"]) >= 1
        assert data["received"][0]["requester_id"] == user1_id
        assert data["received"][0]["requester_display_name"] == "TestUser1"

    def test_list_friend_requests_sent(self):
        """Test listing sent friend requests"""
        response = client.get(
            "/api/v1/friends/requests",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["sent_count"] >= 1
        assert len(data["sent"]) >= 1


class TestRespondToFriendRequest:
    """Test responding to friend requests"""

    def test_respond_not_addressee(self):
        """Test that only addressee can respond"""
        response = client.post(
            f"/api/v1/friends/requests/{friendship_id}/respond",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 403
        assert "respond to requests sent to you" in response.json()["detail"]

    def test_accept_friend_request(self):
        """Test accepting a friend request"""
        response = client.post(
            f"/api/v1/friends/requests/{friendship_id}/respond",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()

        assert data["status"] == "accepted"
        assert data["id"] == friendship_id

    def test_respond_to_non_pending_request(self):
        """Test that responding to non-pending request fails"""
        response = client.post(
            f"/api/v1/friends/requests/{friendship_id}/respond",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 400
        assert "pending" in response.json()["detail"].lower()

    def test_respond_to_nonexistent_request(self):
        """Test responding to non-existent request"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/api/v1/friends/requests/{fake_uuid}/respond",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 404


class TestListFriends:
    """Test listing friends"""

    def test_list_accepted_friends(self):
        """Test listing accepted friends"""
        response = client.get(
            "/api/v1/friends",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        assert len(data["friends"]) >= 1

        friend = data["friends"][0]
        assert friend["id"] == user2_id
        assert friend["display_name"] == "TestUser2"
        assert friend["friendship_status"] == "accepted"

    def test_list_friends_from_addressee_side(self):
        """Test listing friends from addressee perspective"""
        response = client.get(
            "/api/v1/friends",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        friend = data["friends"][0]
        assert friend["id"] == user1_id

    def test_list_friends_with_filter(self):
        """Test listing friends with status filter"""
        response = client.get(
            "/api/v1/friends?status_filter=accepted",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        for friend in data["friends"]:
            assert friend["friendship_status"] == "accepted"

    def test_list_friends_unauthorized(self):
        """Test listing friends without authentication"""
        response = client.get("/api/v1/friends")

        assert response.status_code == 403


class TestUserSearch:
    """Test user search with friendship status"""

    def test_search_users_by_name(self):
        """Test searching users by display name"""
        response = client.get(
            "/api/v1/users/search?q=TestUser2",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 1
        user = next((u for u in data if u["id"] == user2_id), None)
        assert user is not None
        assert user["is_friend"] is True
        assert user["friendship_status"] == "accepted"

    def test_search_users_by_email(self):
        """Test searching users by email"""
        response = client.get(
            f"/api/v1/users/search?q={TEST_USER_2_EMAIL}",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 1
        user = next((u for u in data if u["id"] == user2_id), None)
        assert user is not None

    def test_search_excludes_current_user(self):
        """Test that search excludes current user"""
        response = client.get(
            "/api/v1/users/search?q=TestUser",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        user_ids = [u["id"] for u in data]
        assert user1_id not in user_ids

    def test_search_min_length(self):
        """Test that search requires minimum query length"""
        response = client.get(
            "/api/v1/users/search?q=T",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 422


class TestRemoveFriend:
    """Test removing friends"""

    def test_remove_friend_success(self):
        """Test successfully removing a friend"""
        response = client.delete(
            f"/api/v1/friends/{user2_id}",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()

        assert data["success"] is True
        assert "removed" in data["message"].lower()

    def test_remove_friend_from_addressee_side(self):
        """Test that addressee can also remove friend"""
        # First create a new friendship
        client.post(
            "/api/v1/friends/request",
            json={"addressee_id": user2_id},
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        # Get the new friendship and accept it
        requests_response = client.get(
            "/api/v1/friends/requests",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        new_friendship_id = requests_response.json()["received"][0]["id"]

        client.post(
            f"/api/v1/friends/requests/{new_friendship_id}/respond",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        # Now remove from addressee side
        response = client.delete(
            f"/api/v1/friends/{user1_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 200

    def test_remove_friend_not_found(self):
        """Test removing non-existent friendship"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.delete(
            f"/api/v1/friends/{fake_uuid}",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 404

    def test_remove_self_as_friend(self):
        """Test that removing self is rejected"""
        response = client.delete(
            f"/api/v1/friends/{user1_id}",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 400
        assert "yourself" in response.json()["detail"].lower()

    def test_remove_friend_unauthorized(self):
        """Test removing friend without authentication"""
        response = client.delete(f"/api/v1/friends/{user2_id}")

        assert response.status_code == 403


class TestRejectAndBlockActions:
    """Test reject and block actions"""

    def test_reject_friend_request(self):
        """Test rejecting a friend request"""
        # Send new request
        client.post(
            "/api/v1/friends/request",
            json={"addressee_id": user2_id},
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        # Get friendship ID
        requests_response = client.get(
            "/api/v1/friends/requests",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        reject_friendship_id = requests_response.json()["received"][0]["id"]

        # Reject it
        response = client.post(
            f"/api/v1/friends/requests/{reject_friendship_id}/respond",
            json={"action": "reject"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    def test_block_friend_request(self):
        """Test blocking a user"""
        # Send new request
        client.post(
            "/api/v1/friends/request",
            json={"addressee_id": user2_id},
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        # Get friendship ID
        requests_response = client.get(
            "/api/v1/friends/requests",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        block_friendship_id = requests_response.json()["received"][0]["id"]

        # Block it
        response = client.post(
            f"/api/v1/friends/requests/{block_friendship_id}/respond",
            json={"action": "block"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blocked"

    def test_cannot_send_request_when_blocked(self):
        """Test that sending request to blocker fails"""
        response = client.post(
            "/api/v1/friends/request",
            json={"addressee_id": user2_id},
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        assert response.status_code == 403
