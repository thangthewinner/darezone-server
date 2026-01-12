"""
Comprehensive Feature Tests using Real Test Users
Tests all major features with test1@example.com and test2@example.com
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures_test_users import (
    test_user_1_token,
    test_user_2_token,
    test_user_1_id,
    test_user_2_id,
    get_auth_headers,
    TEST_USER_1,
    TEST_USER_2
)
from datetime import date, timedelta

client = TestClient(app)


class TestUserAuthentication:
    """Test basic authentication with test users"""
    
    def test_user1_can_access_me_endpoint(self, test_user_1_token):
        """Test user 1 can access /auth/me"""
        response = client.get(
            "/api/v1/auth/me",
            headers=get_auth_headers(test_user_1_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER_1["email"]
        assert "id" in data
    
    def test_user2_can_access_me_endpoint(self, test_user_2_token):
        """Test user 2 can access /auth/me"""
        response = client.get(
            "/api/v1/auth/me",
            headers=get_auth_headers(test_user_2_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER_2["email"]


class TestChallengeFeatures:
    """Test challenge creation and management"""
    
    def test_user1_create_individual_challenge(self, test_user_1_token, test_habit_ids):
        """User 1 creates an individual challenge"""
        tomorrow = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=30)
        
        response = client.post(
            "/api/v1/challenges/",
            headers=get_auth_headers(test_user_1_token),
            json={
                "name": "Morning Routine",
                "description": "Wake up early every day",
                "type": "individual",
                "start_date": str(tomorrow),
                "end_date": str(end_date),
                "habit_ids": test_habit_ids[:2],
                "checkin_type": "photo",
                "require_evidence": True,
                "max_members": 1,
                "is_public": False
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Morning Routine"
        assert data["type"] == "individual"
        assert "id" in data
    
    def test_user1_create_group_challenge(self, test_user_1_token, test_habit_ids):
        """User 1 creates a group challenge with invite code"""
        tomorrow = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=30)
        
        response = client.post(
            "/api/v1/challenges/",
            headers=get_auth_headers(test_user_1_token),
            json={
                "name": "Team Fitness",
                "description": "Get fit together",
                "type": "group",
                "start_date": str(tomorrow),
                "end_date": str(end_date),
                "habit_ids": test_habit_ids[:2],
                "checkin_type": "photo",
                "require_evidence": True,
                "max_members": 10,
                "is_public": False
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "group"
        assert "invite_code" in data
        assert len(data["invite_code"]) == 6
        
        # Return for other tests to use
        return data
    
    def test_user2_join_group_challenge(self, test_user_1_token, test_user_2_token, test_habit_ids):
        """User 2 joins User 1's group challenge"""
        # User 1 creates challenge
        tomorrow = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=30)
        
        create_response = client.post(
            "/api/v1/challenges/",
            headers=get_auth_headers(test_user_1_token),
            json={
                "name": "Shared Challenge",
                "description": "Together",
                "type": "group",
                "start_date": str(tomorrow),
                "end_date": str(end_date),
                "habit_ids": test_habit_ids[:1],
                "checkin_type": "photo",
                "max_members": 10,
                "is_public": False
            }
        )
        
        assert create_response.status_code == 201
        challenge = create_response.json()
        invite_code = challenge["invite_code"]
        
        # User 2 joins
        join_response = client.post(
            "/api/v1/challenges/join",
            headers=get_auth_headers(test_user_2_token),
            json={"invite_code": invite_code}
        )
        
        assert join_response.status_code == 200
        assert join_response.json()["name"] == "Shared Challenge"
    
    def test_list_my_challenges(self, test_user_1_token):
        """User 1 lists their challenges"""
        response = client.get(
            "/api/v1/challenges/",
            headers=get_auth_headers(test_user_1_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "challenges" in data
        assert isinstance(data["challenges"], list)


class TestCheckinFeatures:
    """Test check-in submission and viewing"""
    
    def test_submit_checkin_with_photo(self, test_user_1_token, test_habit_ids):
        """User 1 submits check-in with photo"""
        # First create a challenge
        tomorrow = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=30)
        
        challenge_response = client.post(
            "/api/v1/challenges/",
            headers=get_auth_headers(test_user_1_token),
            json={
                "name": "Test Challenge",
                "type": "individual",
                "start_date": str(tomorrow),
                "end_date": str(end_date),
                "habit_ids": test_habit_ids[:1],
                "checkin_type": "photo",
                "max_members": 1
            }
        )
        
        challenge_id = challenge_response.json()["id"]
        habit_id = test_habit_ids[0]
        
        # Submit check-in
        checkin_response = client.post(
            "/api/v1/checkins/",
            headers=get_auth_headers(test_user_1_token),
            json={
                "challenge_id": challenge_id,
                "habit_id": habit_id,
                "photo_url": "https://example.com/photo.jpg",
                "caption": "Done for today!"
            }
        )
        
        assert checkin_response.status_code == 201
        data = checkin_response.json()
        assert "checkin" in data
        assert data["checkin"]["photo_url"] == "https://example.com/photo.jpg"
    
    def test_view_todays_checkins(self, test_user_1_token):
        """User 1 views today's check-ins"""
        response = client.get(
            "/api/v1/checkins/today",
            headers=get_auth_headers(test_user_1_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestFriendshipFeatures:
    """Test friend requests and management"""
    
    def test_send_friend_request(self, test_user_1_token, test_user_2_id):
        """User 1 sends friend request to User 2"""
        response = client.post(
            "/api/v1/friends/request",
            headers=get_auth_headers(test_user_1_token),
            json={"friend_id": test_user_2_id}
        )
        
        # May be 201 (new) or 200 (already exists)
        assert response.status_code in [200, 201]
    
    def test_view_friends_list(self, test_user_1_token):
        """User 1 views friends list"""
        response = client.get(
            "/api/v1/friends",
            headers=get_auth_headers(test_user_1_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestUserProfile:
    """Test user profile operations"""
    
    def test_view_my_profile(self, test_user_1_token):
        """User 1 views own profile"""
        response = client.get(
            "/api/v1/users/me",
            headers=get_auth_headers(test_user_1_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER_1["email"]
        assert "stats" in data
    
    def test_update_my_profile(self, test_user_1_token):
        """User 1 updates profile"""
        response = client.patch(
            "/api/v1/users/me",
            headers=get_auth_headers(test_user_1_token),
            json={
                "display_name": "Updated Test User 1",
                "bio": "This is my test bio"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Test User 1"
        assert data["bio"] == "This is my test bio"
    
    def test_search_users(self, test_user_1_token):
        """User 1 searches for users"""
        response = client.get(
            "/api/v1/users/search?q=test",
            headers=get_auth_headers(test_user_1_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestStatsFeatures:
    """Test statistics and leaderboard"""
    
    def test_view_my_stats(self, test_user_1_token):
        """User 1 views their stats"""
        response = client.get(
            "/api/v1/stats/me",
            headers=get_auth_headers(test_user_1_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "current_streak" in data
        assert "total_check_ins" in data
        assert "points" in data


# Add more test classes for:
# - TestMediaUpload
# - TestNotifications
# - TestHitchReminders
# etc.
