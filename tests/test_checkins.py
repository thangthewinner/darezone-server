import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import date

client = TestClient(app)


class TestCreateCheckin:
    """Test POST /checkins endpoint"""

    def test_create_checkin_success(
        self, test_user_token, test_challenge, test_habit_ids
    ):
        """Should create check-in successfully"""
        checkin_data = {
            "challenge_id": test_challenge["id"],
            "habit_id": test_challenge["habits"][0]["id"],
            "caption": "Morning workout complete!",
            "photo_url": "https://example.com/photo.jpg",
        }

        response = client.post(
            "/api/v1/checkins/",
            json=checkin_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        # Check structure
        assert "checkin" in data
        assert "new_streak" in data
        assert "points_earned" in data
        assert "is_streak_broken" in data
        assert "message" in data

        # Check checkin details
        checkin = data["checkin"]
        assert checkin["challenge_id"] == checkin_data["challenge_id"]
        assert checkin["habit_id"] == checkin_data["habit_id"]
        assert checkin["caption"] == checkin_data["caption"]
        assert checkin["status"] == "completed"

        # Check streak and points
        assert data["new_streak"] >= 1
        assert data["points_earned"] in [10, 20]  # Base or streak multiplier

    def test_create_checkin_duplicate(
        self, test_user_token, test_challenge, test_existing_checkin
    ):
        """Should reject duplicate check-in for same habit today"""
        checkin_data = {
            "challenge_id": test_challenge["id"],
            "habit_id": test_existing_checkin["habit_id"],
            "caption": "Trying to check in again",
        }

        response = client.post(
            "/api/v1/checkins/",
            json=checkin_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        assert "already checked in" in response.json()["detail"].lower()

    def test_create_checkin_no_evidence(self, test_user_token, test_challenge):
        """Should reject check-in without any evidence"""
        checkin_data = {
            "challenge_id": test_challenge["id"],
            "habit_id": test_challenge["habits"][0]["id"],
            # No caption, photo, or video
        }

        response = client.post(
            "/api/v1/checkins/",
            json=checkin_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        assert "evidence" in response.json()["detail"].lower()

    def test_create_checkin_not_member(self, second_user_token, test_challenge):
        """Should reject if not a member of challenge"""
        checkin_data = {
            "challenge_id": test_challenge["id"],
            "habit_id": test_challenge["habits"][0]["id"],
            "caption": "Not my challenge",
        }

        response = client.post(
            "/api/v1/checkins/",
            json=checkin_data,
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403
        assert "not a member" in response.json()["detail"].lower()

    def test_create_checkin_unauthorized(self, test_challenge):
        """Should reject without authentication"""
        checkin_data = {
            "challenge_id": test_challenge["id"],
            "habit_id": "some-habit-id",
            "caption": "Unauthorized",
        }

        response = client.post("/api/v1/checkins/", json=checkin_data)

        assert response.status_code == 403


class TestListCheckins:
    """Test GET /checkins endpoint"""

    def test_list_checkins_success(self, test_user_token):
        """Should return paginated list of my check-ins"""
        response = client.get(
            "/api/v1/checkins/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check pagination structure
        assert "checkins" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data

        assert isinstance(data["checkins"], list)

    def test_list_checkins_with_filter(self, test_user_token, test_challenge):
        """Should filter by challenge_id"""
        response = client.get(
            f"/api/v1/checkins/?challenge_id={test_challenge['id']}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # All checkins should be for specified challenge
        for checkin in data["checkins"]:
            assert checkin["challenge_id"] == test_challenge["id"]

    def test_list_checkins_pagination(self, test_user_token):
        """Should respect pagination parameters"""
        response = client.get(
            "/api/v1/checkins/?page=1&limit=5",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["limit"] == 5
        assert len(data["checkins"]) <= 5

    def test_list_checkins_unauthorized(self):
        """Should reject without authentication"""
        response = client.get("/api/v1/checkins/")

        assert response.status_code == 403


class TestGetCheckin:
    """Test GET /checkins/{id} endpoint"""

    def test_get_checkin_success(self, test_user_token, test_existing_checkin):
        """Should return check-in details"""
        response = client.get(
            f"/api/v1/checkins/{test_existing_checkin['id']}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_existing_checkin["id"]
        assert "challenge_id" in data
        assert "habit_id" in data
        assert "status" in data

    def test_get_checkin_not_member(self, second_user_token, test_existing_checkin):
        """Should reject if not challenge member"""
        response = client.get(
            f"/api/v1/checkins/{test_existing_checkin['id']}",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403

    def test_get_checkin_not_found(self, test_user_token):
        """Should return 404 for non-existent check-in"""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/checkins/{fake_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 404


class TestUpdateCheckin:
    """Test PATCH /checkins/{id} endpoint"""

    def test_update_checkin_success(self, test_user_token, test_existing_checkin):
        """Should update caption"""
        update_data = {"caption": "Updated caption"}

        response = client.patch(
            f"/api/v1/checkins/{test_existing_checkin['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["caption"] == update_data["caption"]

    def test_update_checkin_not_owner(self, second_user_token, test_existing_checkin):
        """Should reject if not owner"""
        update_data = {"caption": "Hacking attempt"}

        response = client.patch(
            f"/api/v1/checkins/{test_existing_checkin['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403

    def test_update_checkin_old_date(self, test_user_token, test_old_checkin):
        """Should reject update for old check-ins"""
        update_data = {"caption": "Too late"}

        response = client.patch(
            f"/api/v1/checkins/{test_old_checkin['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        assert "today" in response.json()["detail"].lower()


class TestDeleteCheckin:
    """Test DELETE /checkins/{id} endpoint"""

    def test_delete_checkin_success(self, test_user_token, test_existing_checkin):
        """Should delete check-in"""
        response = client.delete(
            f"/api/v1/checkins/{test_existing_checkin['id']}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 204

    def test_delete_checkin_not_owner(self, second_user_token, test_existing_checkin):
        """Should reject if not owner"""
        response = client.delete(
            f"/api/v1/checkins/{test_existing_checkin['id']}",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403


class TestTodayProgress:
    """Test GET /checkins/challenges/{id}/today endpoint"""

    def test_get_today_progress_success(self, test_user_token, test_challenge):
        """Should return today's progress"""
        response = client.get(
            f"/api/v1/checkins/challenges/{test_challenge['id']}/today",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # Check structure if data exists
        if data:
            habit_progress = data[0]
            assert "habit_id" in habit_progress
            assert "habit_name" in habit_progress
            assert "members" in habit_progress
            assert "completion_rate" in habit_progress
            assert "total_checkins_today" in habit_progress

            # Check member structure
            if habit_progress["members"]:
                member = habit_progress["members"][0]
                assert "user_id" in member
                assert "user_name" in member
                assert "checked_in_today" in member
                assert isinstance(member["checked_in_today"], bool)

    def test_get_today_progress_not_member(self, second_user_token, test_challenge):
        """Should reject if not member"""
        response = client.get(
            f"/api/v1/checkins/challenges/{test_challenge['id']}/today",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403


class TestCheckinEndpointsDocumentation:
    """Test that check-in endpoints are in OpenAPI schema"""

    def test_checkin_endpoints_in_openapi(self):
        """Check-in endpoints should be in OpenAPI schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        paths = schema.get("paths", {})

        # Check all endpoints exist
        assert "/api/v1/checkins/" in paths
        assert "/api/v1/checkins/{checkin_id}" in paths
        assert "/api/v1/checkins/challenges/{challenge_id}/today" in paths

    def test_checkin_tag_exists(self):
        """Check-ins tag should exist in OpenAPI"""
        response = client.get("/openapi.json")
        schema = response.json()

        paths = schema.get("paths", {})
        checkins_path = paths.get("/api/v1/checkins/", {})
        post_method = checkins_path.get("post", {})
        tags = post_method.get("tags", [])

        assert "Check-ins" in tags


class TestProtectedCheckinRoutes:
    """Test that all check-in endpoints require authentication"""

    def test_all_checkin_endpoints_require_auth(self):
        """All check-in endpoints should be protected"""
        fake_id = "00000000-0000-0000-0000-000000000000"

        endpoints = [
            ("/api/v1/checkins/", "POST"),
            ("/api/v1/checkins/", "GET"),
            (f"/api/v1/checkins/{fake_id}", "GET"),
            (f"/api/v1/checkins/{fake_id}", "PATCH"),
            (f"/api/v1/checkins/{fake_id}", "DELETE"),
            (f"/api/v1/checkins/challenges/{fake_id}/today", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PATCH":
                response = client.patch(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)

            # Should be unauthorized
            assert response.status_code in [
                401,
                403,
            ], f"{method} {endpoint} not protected"
