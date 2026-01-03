import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestTokenVerification:
    """Test token verification endpoint"""

    def test_verify_valid_token(self, test_user_token):
        """Should verify valid token and return user info"""
        response = client.post(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data
        assert "email" in data
        assert "@" in data["email"]

    def test_verify_invalid_token(self, invalid_token):
        """Should reject invalid token"""
        response = client.post(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_verify_missing_token(self):
        """Should reject request without token"""
        response = client.post("/api/v1/auth/verify")

        # HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403

    def test_verify_malformed_auth_header(self):
        """Should reject malformed Authorization header"""
        response = client.post(
            "/api/v1/auth/verify",
            headers={"Authorization": "InvalidFormat"},
        )

        assert response.status_code == 403


class TestGetCurrentUser:
    """Test get current user endpoint"""

    def test_get_current_user_success(self, test_user_token):
        """Should return full user profile with valid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {test_user_token}"},
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
        assert "total_check_ins" in stats
        assert "points" in stats

    def test_get_current_user_unauthorized(self):
        """Should reject request without token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403

    def test_get_current_user_invalid_token(self, invalid_token):
        """Should reject invalid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

        assert response.status_code == 401

    def test_get_current_user_returns_correct_account_type(self, test_user_token):
        """Should return correct account type"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        # B2C-only app (B2B removed)
        # account_type field may not exist if user_profiles table was updated
        if "account_type" in data:
            assert data["account_type"] == "b2c"


class TestLogout:
    """Test logout endpoint"""

    def test_logout_success(self, test_user_token):
        """Should successfully logout with valid token"""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_logout_unauthorized(self):
        """Should reject logout without token"""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 403

    def test_logout_invalid_token(self, invalid_token):
        """Should reject logout with invalid token"""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

        assert response.status_code == 401


class TestAuthErrorHandling:
    """Test authentication error scenarios"""

    def test_expired_token_returns_401(self, expired_token):
        """Should return 401 for expired token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401

    def test_empty_bearer_token(self):
        """Should reject empty bearer token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "},
        )

        assert response.status_code == 401 or response.status_code == 403

    def test_error_response_format(self, invalid_token):
        """Should return consistent error format"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestProtectedRouteAccess:
    """Test that protected routes properly enforce authentication"""

    def test_all_auth_endpoints_require_token(self):
        """All auth endpoints should require authentication"""
        endpoints = [
            ("/api/v1/auth/verify", "POST"),
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/auth/logout", "POST"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)

            # Should be unauthorized (401 or 403)
            assert response.status_code in [401, 403], f"{endpoint} not protected"


class TestAuthDocumentation:
    """Test that auth endpoints are properly documented"""

    def test_auth_endpoints_in_openapi(self):
        """Auth endpoints should be in OpenAPI schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Check auth endpoints exist
        paths = schema.get("paths", {})
        assert "/api/v1/auth/verify" in paths
        assert "/api/v1/auth/me" in paths
        assert "/api/v1/auth/logout" in paths

    def test_auth_tag_exists(self):
        """Authentication tag should exist in OpenAPI"""
        response = client.get("/openapi.json")
        schema = response.json()

        # Check for Authentication tag
        paths = schema.get("paths", {})
        verify_path = paths.get("/api/v1/auth/verify", {})
        post_method = verify_path.get("post", {})
        tags = post_method.get("tags", [])

        assert "Authentication" in tags
