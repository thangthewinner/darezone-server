"""
Tests for anonymous user authentication
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


class TestAnonymousLogin:
    """Test suite for anonymous login functionality"""

    def test_anonymous_login_new_user(self):
        """Test creating a new anonymous user"""
        # Generate a unique device ID
        device_id = str(uuid.uuid4())

        response = client.post(
            "/api/v1/auth/anonymous-login",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "user_id" in data
        assert "is_anonymous" in data
        assert "created_at" in data
        assert "is_new_user" in data

        # Verify values
        assert data["is_anonymous"] is True
        assert data["is_new_user"] is True
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_anonymous_login_existing_user(self):
        """Test logging in with existing anonymous user"""
        # Create a user first
        device_id = str(uuid.uuid4())

        # First login - creates user
        response1 = client.post(
            "/api/v1/auth/anonymous-login",
            json={"device_id": device_id}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["is_new_user"] is True
        user_id_1 = data1["user_id"]

        # Second login - returns existing user
        response2 = client.post(
            "/api/v1/auth/anonymous-login",
            json={"device_id": device_id}
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # Should be same user
        assert data2["is_new_user"] is False
        assert data2["user_id"] == user_id_1
        assert data2["is_anonymous"] is True

    def test_anonymous_login_invalid_device_id(self):
        """Test with invalid device ID format"""
        invalid_ids = [
            "not-a-uuid",
            "12345",
            "",
            "550e8400-e29b-41d4-a716",  # Incomplete UUID
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
        ]

        for invalid_id in invalid_ids:
            response = client.post(
                "/api/v1/auth/anonymous-login",
                json={"device_id": invalid_id}
            )
            assert response.status_code == 422  # Validation error

    def test_anonymous_login_missing_device_id(self):
        """Test with missing device_id field"""
        response = client.post(
            "/api/v1/auth/anonymous-login",
            json={}
        )
        assert response.status_code == 422  # Validation error

    def test_anonymous_token_works_with_apis(self):
        """Test that anonymous user token works with protected endpoints"""
        # Create anonymous user
        device_id = str(uuid.uuid4())
        login_response = client.post(
            "/api/v1/auth/anonymous-login",
            json={"device_id": device_id}
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        # Try to access protected endpoint
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should work
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert "id" in user_data
        assert "email" in user_data

    def test_multiple_devices_get_different_users(self):
        """Test that different devices get different anonymous users"""
        device_id_1 = str(uuid.uuid4())
        device_id_2 = str(uuid.uuid4())

        # Login from device 1
        response1 = client.post(
            "/api/v1/auth/anonymous-login",
            json={"device_id": device_id_1}
        )
        user_id_1 = response1.json()["user_id"]

        # Login from device 2
        response2 = client.post(
            "/api/v1/auth/anonymous-login",
            json={"device_id": device_id_2}
        )
        user_id_2 = response2.json()["user_id"]

        # Should be different users
        assert user_id_1 != user_id_2

    def test_anonymous_user_can_create_challenge(self):
        """Test that anonymous users can create challenges"""
        # Create anonymous user
        device_id = str(uuid.uuid4())
        login_response = client.post(
            "/api/v1/auth/anonymous-login",
            json={"device_id": device_id}
        )
        token = login_response.json()["access_token"]

        # Try to create a challenge
        # Note: This will fail if habits don't exist, but tests the auth flow
        challenge_response = client.post(
            "/api/v1/challenges",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Challenge",
                "description": "Test",
                "type": "individual",
                "start_date": "2026-01-05",
                "end_date": "2026-01-31",
                "habit_ids": ["test-habit-id"],
                "checkin_type": "photo",
                "require_evidence": True,
                "max_members": 10,
                "is_public": False
            }
        )

        # Should not get 401 Unauthorized
        assert challenge_response.status_code != 401


class TestAnonymousService:
    """Test suite for anonymous service functions"""

    def test_generate_anonymous_credentials(self):
        """Test credential generation"""
        from app.services.anonymous_service import generate_anonymous_credentials
        import hashlib

        device_id = str(uuid.uuid4())
        email, password = generate_anonymous_credentials(device_id)

        # Verify email format (uses hash, not full device_id)
        hash_obj = hashlib.sha256(device_id.encode())
        expected_hash = hash_obj.hexdigest()[:16]
        expected_email = f"anon{expected_hash}@darezone.app"
        assert email == expected_email

        # Verify password is secure
        assert len(password) == 32
        assert password.isalnum()

    def test_password_regeneration_is_consistent(self):
        """Test that password regeneration produces same result for same device"""
        from app.services.anonymous_service import generate_anonymous_credentials

        device_id = str(uuid.uuid4())

        # Generate twice
        email1, password1 = generate_anonymous_credentials(device_id)
        email2, password2 = generate_anonymous_credentials(device_id)

        # Email should be same
        assert email1 == email2

        # Password should be same (deterministic for same device)
        assert password1 == password2
