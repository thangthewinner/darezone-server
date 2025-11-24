import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetMyProfile:
    """Test GET /users/me endpoint"""

    def test_get_my_profile_success(self, test_user_token):
        """Should return full profile with stats"""
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "id" in data
        assert "email" in data
        assert "account_type" in data
        assert "stats" in data
        assert "created_at" in data

        # Check stats structure
        stats = data["stats"]
        assert "current_streak" in stats
        assert "longest_streak" in stats
        assert "total_check_ins" in stats
        assert "points" in stats
        assert "active_challenges" in stats
        assert "friend_count" in stats

        # Check stats are non-negative
        assert stats["current_streak"] >= 0
        assert stats["points"] >= 0

    def test_get_my_profile_unauthorized(self):
        """Should return 403 without token"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403

    def test_get_my_profile_invalid_token(self, invalid_token):
        """Should return 401 with invalid token"""
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert response.status_code == 401


class TestUpdateProfile:
    """Test PATCH /users/me endpoint"""

    def test_update_profile_display_name(self, test_user_token):
        """Should update display_name successfully"""
        update_data = {"display_name": "Updated Test Name"}

        response = client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Test Name"

    def test_update_profile_bio(self, test_user_token):
        """Should update bio successfully"""
        update_data = {"bio": "This is my new bio"}

        response = client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "This is my new bio"

    def test_update_profile_multiple_fields(self, test_user_token):
        """Should update multiple fields at once"""
        update_data = {
            "display_name": "Multi Field Update",
            "full_name": "Test User Full",
            "bio": "Updated bio",
        }

        response = client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Multi Field Update"
        assert data["full_name"] == "Test User Full"
        assert data["bio"] == "Updated bio"

    def test_update_profile_empty_display_name_rejected(self, test_user_token):
        """Should reject empty display_name"""
        update_data = {"display_name": "   "}  # Whitespace only

        response = client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_update_profile_display_name_too_long(self, test_user_token):
        """Should reject display_name longer than 50 chars"""
        update_data = {"display_name": "x" * 51}  # 51 characters

        response = client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_update_profile_bio_too_long(self, test_user_token):
        """Should reject bio longer than 500 chars"""
        update_data = {"bio": "x" * 501}  # 501 characters

        response = client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_update_profile_no_fields(self, test_user_token):
        """Should return error when no fields provided"""
        update_data = {}

        response = client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        assert "No fields to update" in response.json()["detail"]

    def test_update_profile_unauthorized(self):
        """Should reject update without token"""
        update_data = {"display_name": "New Name"}

        response = client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == 403


class TestUserSearch:
    """Test GET /users/search endpoint"""

    def test_search_users_success(self, test_user_token):
        """Should return search results"""
        response = client.get(
            "/api/v1/users/search?q=test",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Results may be empty if no matching users
        if data:
            # Check result structure
            result = data[0]
            assert "id" in result
            assert "display_name" in result
            assert "is_friend" in result
            assert isinstance(result["is_friend"], bool)

    def test_search_users_with_limit(self, test_user_token):
        """Should respect limit parameter"""
        response = client.get(
            "/api/v1/users/search?q=test&limit=5",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_search_users_query_too_short(self, test_user_token):
        """Should reject query shorter than 2 chars"""
        response = client.get(
            "/api/v1/users/search?q=a",  # Only 1 character
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_search_users_query_too_long(self, test_user_token):
        """Should reject query longer than 50 chars"""
        response = client.get(
            f"/api/v1/users/search?q={'x' * 51}",  # 51 characters
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_search_users_missing_query(self, test_user_token):
        """Should require query parameter"""
        response = client.get(
            "/api/v1/users/search",  # No q parameter
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_search_users_unauthorized(self):
        """Should reject search without token"""
        response = client.get("/api/v1/users/search?q=test")

        assert response.status_code == 403


class TestGetUserStats:
    """Test GET /users/me/stats endpoint"""

    def test_get_my_stats_success(self, test_user_token):
        """Should return detailed stats"""
        response = client.get(
            "/api/v1/users/me/stats",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check all required stats fields
        assert "current_streak" in data
        assert "longest_streak" in data
        assert "total_check_ins" in data
        assert "total_challenges_completed" in data
        assert "points" in data
        assert "active_challenges" in data
        assert "friend_count" in data

        # Check all values are non-negative integers
        for value in data.values():
            assert isinstance(value, int)
            assert value >= 0

    def test_get_my_stats_unauthorized(self):
        """Should reject stats request without token"""
        response = client.get("/api/v1/users/me/stats")

        assert response.status_code == 403


class TestUserEndpointsDocumentation:
    """Test that user endpoints are properly documented"""

    def test_user_endpoints_in_openapi(self):
        """User endpoints should be in OpenAPI schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        paths = schema.get("paths", {})

        # Check all user endpoints exist
        assert "/api/v1/users/me" in paths
        assert "/api/v1/users/search" in paths
        assert "/api/v1/users/me/stats" in paths

        # Check methods
        assert "get" in paths["/api/v1/users/me"]
        assert "patch" in paths["/api/v1/users/me"]
        assert "get" in paths["/api/v1/users/search"]

    def test_user_tag_exists(self):
        """Users tag should exist in OpenAPI"""
        response = client.get("/openapi.json")
        schema = response.json()

        paths = schema.get("paths", {})
        me_path = paths.get("/api/v1/users/me", {})
        get_method = me_path.get("get", {})
        tags = get_method.get("tags", [])

        assert "Users" in tags


class TestProtectedUserRoutes:
    """Test that all user endpoints require authentication"""

    def test_all_user_endpoints_require_auth(self):
        """All user endpoints should be protected"""
        endpoints = [
            ("/api/v1/users/me", "GET"),
            ("/api/v1/users/me", "PATCH"),
            ("/api/v1/users/search?q=test", "GET"),
            ("/api/v1/users/me/stats", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "PATCH":
                response = client.patch(endpoint, json={"display_name": "test"})

            # Should be unauthorized
            assert response.status_code in [
                401,
                403,
            ], f"{method} {endpoint} not protected"
