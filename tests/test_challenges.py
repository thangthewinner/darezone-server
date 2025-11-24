import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import date, timedelta

client = TestClient(app)


class TestChallengeCreation:
    """Test POST /challenges endpoint"""

    def test_create_challenge_success(self, test_user_token, test_habit_ids):
        """Should create challenge with valid data"""
        tomorrow = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=30)

        challenge_data = {
            "name": "30 Day Fitness Challenge",
            "description": "Get fit together!",
            "type": "group",
            "start_date": str(tomorrow),
            "end_date": str(end_date),
            "habit_ids": test_habit_ids[:2],  # Use 2 habits
            "checkin_type": "photo",
            "require_evidence": True,
            "max_members": 10,
            "is_public": False,
        }

        response = client.post(
            "/api/v1/challenges/",
            json=challenge_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        # Check challenge fields
        assert "id" in data
        assert data["name"] == challenge_data["name"]
        assert data["description"] == challenge_data["description"]
        assert data["type"] == challenge_data["type"]
        assert data["status"] == "pending"
        assert "invite_code" in data
        assert len(data["invite_code"]) == 6
        assert data["member_count"] == 1  # Creator auto-added

        # Check creator is a member
        assert data["my_role"] == "creator"
        assert data["my_status"] == "active"
        assert data["my_stats"]["hitch_count"] == 2

        # Check habits linked
        assert len(data["habits"]) == 2

        # Check members list
        assert len(data["members"]) == 1
        assert data["members"][0]["role"] == "creator"

    def test_create_challenge_invalid_habits(self, test_user_token):
        """Should reject non-existent habit IDs"""
        tomorrow = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=30)

        challenge_data = {
            "name": "Test Challenge",
            "type": "individual",
            "start_date": str(tomorrow),
            "end_date": str(end_date),
            "habit_ids": ["00000000-0000-0000-0000-000000000000"],  # Invalid ID
        }

        response = client.post(
            "/api/v1/challenges/",
            json=challenge_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        assert "habit" in response.json()["detail"].lower()

    def test_create_challenge_too_many_habits(self, test_user_token, test_habit_ids):
        """Should reject more than 4 habits"""
        tomorrow = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=30)

        # Assuming we have at least 5 habit IDs
        challenge_data = {
            "name": "Test Challenge",
            "type": "individual",
            "start_date": str(tomorrow),
            "end_date": str(end_date),
            "habit_ids": test_habit_ids[:5]
            if len(test_habit_ids) >= 5
            else ["id1", "id2", "id3", "id4", "id5"],
        }

        response = client.post(
            "/api/v1/challenges/",
            json=challenge_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_create_challenge_invalid_date_range(self, test_user_token, test_habit_ids):
        """Should reject end_date before start_date"""
        tomorrow = date.today() + timedelta(days=1)
        yesterday = date.today() - timedelta(days=1)

        challenge_data = {
            "name": "Test Challenge",
            "type": "individual",
            "start_date": str(tomorrow),
            "end_date": str(yesterday),  # Before start_date
            "habit_ids": test_habit_ids[:1],
        }

        response = client.post(
            "/api/v1/challenges/",
            json=challenge_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_create_challenge_unauthorized(self, test_habit_ids):
        """Should reject without authentication"""
        tomorrow = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=30)

        challenge_data = {
            "name": "Test Challenge",
            "type": "individual",
            "start_date": str(tomorrow),
            "end_date": str(end_date),
            "habit_ids": test_habit_ids[:1],
        }

        response = client.post("/api/v1/challenges/", json=challenge_data)

        assert response.status_code == 403


class TestChallengeList:
    """Test GET /challenges endpoint"""

    def test_list_challenges_success(self, test_user_token):
        """Should return paginated list of my challenges"""
        response = client.get(
            "/api/v1/challenges/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check pagination structure
        assert "challenges" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data

        assert isinstance(data["challenges"], list)
        assert data["page"] == 1
        assert data["limit"] == 20

    def test_list_challenges_pagination(self, test_user_token):
        """Should respect pagination parameters"""
        response = client.get(
            "/api/v1/challenges/?page=1&limit=5",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["limit"] == 5
        assert len(data["challenges"]) <= 5

    def test_list_challenges_status_filter(self, test_user_token):
        """Should filter by status"""
        response = client.get(
            "/api/v1/challenges/?status_filter=active",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        # Should return only active challenges (or empty list)

    def test_list_challenges_unauthorized(self):
        """Should reject without authentication"""
        response = client.get("/api/v1/challenges/")

        assert response.status_code == 403


class TestJoinChallenge:
    """Test POST /challenges/join endpoint"""

    def test_join_challenge_success(
        self, test_user_token, second_user_token, test_challenge
    ):
        """Should join challenge via valid invite code"""
        # Second user joins challenge created by first user
        join_data = {"invite_code": test_challenge["invite_code"]}

        response = client.post(
            "/api/v1/challenges/join",
            json=join_data,
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check membership
        assert data["my_role"] == "member"
        assert data["my_status"] == "active"
        assert data["member_count"] == 2  # Creator + new member

    def test_join_challenge_invalid_code(self, test_user_token):
        """Should reject invalid invite code"""
        join_data = {"invite_code": "XXXXXX"}

        response = client.post(
            "/api/v1/challenges/join",
            json=join_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 404
        assert "invalid" in response.json()["detail"].lower()

    def test_join_challenge_already_member(self, test_user_token, test_challenge):
        """Should reject if already a member"""
        # Creator tries to join own challenge
        join_data = {"invite_code": test_challenge["invite_code"]}

        response = client.post(
            "/api/v1/challenges/join",
            json=join_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_join_challenge_unauthorized(self, test_challenge):
        """Should reject without authentication"""
        join_data = {"invite_code": test_challenge["invite_code"]}

        response = client.post("/api/v1/challenges/join", json=join_data)

        assert response.status_code == 403


class TestLeaveChallenge:
    """Test POST /challenges/{id}/leave endpoint"""

    def test_leave_challenge_success(
        self, test_user_token, second_user_token, test_challenge_with_member
    ):
        """Should leave challenge successfully"""
        challenge_id = test_challenge_with_member["id"]

        response = client.post(
            f"/api/v1/challenges/{challenge_id}/leave",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

    def test_leave_challenge_as_creator(self, test_user_token, test_challenge):
        """Should reject creator leaving"""
        challenge_id = test_challenge["id"]

        response = client.post(
            f"/api/v1/challenges/{challenge_id}/leave",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 400
        assert "creator" in response.json()["detail"].lower()

    def test_leave_challenge_not_member(self, test_user_token):
        """Should reject if not a member"""
        fake_challenge_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/api/v1/challenges/{fake_challenge_id}/leave",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code in [403, 404]


class TestChallengeUpdate:
    """Test PATCH /challenges/{id} endpoint"""

    def test_update_challenge_success(self, test_user_token, test_challenge):
        """Should update challenge as creator"""
        challenge_id = test_challenge["id"]
        update_data = {
            "name": "Updated Challenge Name",
            "description": "Updated description",
        }

        response = client.patch(
            f"/api/v1/challenges/{challenge_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    def test_update_challenge_non_creator(
        self, second_user_token, test_challenge_with_member
    ):
        """Should reject non-creator/admin update"""
        challenge_id = test_challenge_with_member["id"]
        update_data = {"name": "Unauthorized Update"}

        response = client.patch(
            f"/api/v1/challenges/{challenge_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code == 403

    def test_update_challenge_not_member(self, test_user_token):
        """Should reject if not a member"""
        fake_challenge_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"name": "Test"}

        response = client.patch(
            f"/api/v1/challenges/{fake_challenge_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code in [403, 404]


class TestChallengeMembers:
    """Test GET /challenges/{id}/members endpoint"""

    def test_get_members_success(self, test_user_token, test_challenge):
        """Should return members list"""
        challenge_id = test_challenge["id"]

        response = client.get(
            f"/api/v1/challenges/{challenge_id}/members",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1  # At least creator

        # Check member structure
        if data:
            member = data[0]
            assert "user_id" in member
            assert "display_name" in member
            assert "role" in member
            assert "status" in member
            assert "stats" in member
            assert "hitch_count" in member["stats"]

    def test_get_members_not_member(self, second_user_token):
        """Should reject if not a member"""
        fake_challenge_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/challenges/{fake_challenge_id}/members",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code in [403, 404]


class TestChallengeProgress:
    """Test GET /challenges/{id}/progress endpoint"""

    def test_get_progress_success(self, test_user_token, test_challenge):
        """Should return today's progress"""
        challenge_id = test_challenge["id"]

        response = client.get(
            f"/api/v1/challenges/{challenge_id}/progress",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "challenge_id" in data
        assert "date" in data
        assert "members" in data
        assert "total_habits" in data
        assert "overall_completion" in data

        assert isinstance(data["members"], list)

        # Check member progress structure
        if data["members"]:
            member = data["members"][0]
            assert "user_id" in member
            assert "display_name" in member
            assert "habits" in member
            assert "total_completed" in member
            assert "completion_percentage" in member

    def test_get_progress_not_member(self, second_user_token):
        """Should reject if not a member"""
        fake_challenge_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/challenges/{fake_challenge_id}/progress",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )

        assert response.status_code in [403, 404]


class TestChallengeEndpointsDocumentation:
    """Test that challenge endpoints are in OpenAPI schema"""

    def test_challenge_endpoints_in_openapi(self):
        """Challenge endpoints should be in OpenAPI schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        paths = schema.get("paths", {})

        # Check all endpoints exist
        assert "/api/v1/challenges/" in paths
        assert "/api/v1/challenges/join" in paths
        assert "/api/v1/challenges/{challenge_id}" in paths
        assert "/api/v1/challenges/{challenge_id}/leave" in paths
        assert "/api/v1/challenges/{challenge_id}/members" in paths
        assert "/api/v1/challenges/{challenge_id}/progress" in paths

    def test_challenge_tag_exists(self):
        """Challenges tag should exist in OpenAPI"""
        response = client.get("/openapi.json")
        schema = response.json()

        paths = schema.get("paths", {})
        challenges_path = paths.get("/api/v1/challenges/", {})
        post_method = challenges_path.get("post", {})
        tags = post_method.get("tags", [])

        assert "Challenges" in tags


class TestProtectedChallengeRoutes:
    """Test that all challenge endpoints require authentication"""

    def test_all_challenge_endpoints_require_auth(self):
        """All challenge endpoints should be protected"""
        fake_id = "00000000-0000-0000-0000-000000000000"

        endpoints = [
            ("/api/v1/challenges/", "POST"),
            ("/api/v1/challenges/", "GET"),
            ("/api/v1/challenges/join", "POST"),
            (f"/api/v1/challenges/{fake_id}", "GET"),
            (f"/api/v1/challenges/{fake_id}", "PATCH"),
            (f"/api/v1/challenges/{fake_id}/leave", "POST"),
            (f"/api/v1/challenges/{fake_id}/members", "GET"),
            (f"/api/v1/challenges/{fake_id}/progress", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PATCH":
                response = client.patch(endpoint, json={})

            # Should be unauthorized
            assert response.status_code in [
                401,
                403,
            ], f"{method} {endpoint} not protected"
