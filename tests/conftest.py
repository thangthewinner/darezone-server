import pytest
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Generator

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def supabase_url() -> str:
    """Get Supabase URL from environment"""
    url = os.getenv("SUPABASE_URL")
    if not url:
        pytest.skip("SUPABASE_URL not set in environment")
    return url


@pytest.fixture(scope="session")
def supabase_service_key() -> str:
    """Get Supabase service role key from environment"""
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        pytest.skip("SUPABASE_SERVICE_ROLE_KEY not set in environment")
    return key


@pytest.fixture(scope="session")
def supabase_client(supabase_url: str, supabase_service_key: str) -> Client:
    """
    Get Supabase client for tests
    Uses service role key for admin operations
    """
    return create_client(supabase_url, supabase_service_key)


@pytest.fixture
def test_user_credentials():
    """
    Return test user credentials
    Note: These should be created in Supabase for testing
    """
    return {
        "email": "test@darezone.com",
        "password": "TestPassword123!",
    }


@pytest.fixture
def test_user_token(
    supabase_client: Client, test_user_credentials: dict
) -> Generator[str, None, None]:
    """
    Create test user and return auth token

    This fixture:
    1. Creates a test user in Supabase Auth
    2. Creates corresponding user_profile entry
    3. Returns the access token for testing
    4. Cleans up after test completes

    Usage in tests:
        def test_something(test_user_token):
            headers = {"Authorization": f"Bearer {test_user_token}"}
            response = client.get("/api/v1/auth/me", headers=headers)
    """
    email = test_user_credentials["email"]
    password = test_user_credentials["password"]

    # Try to sign in first (user might already exist)
    try:
        auth_response = supabase_client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user_id = auth_response.user.id
        token = auth_response.session.access_token
    except Exception:
        # User doesn't exist, create new one
        try:
            auth_response = supabase_client.auth.sign_up(
                {"email": email, "password": password}
            )

            if not auth_response.user:
                pytest.skip("Failed to create test user")

            user_id = auth_response.user.id
            token = auth_response.session.access_token

            # Create user profile
            profile_data = {
                "id": user_id,
                "email": email,
                "display_name": "Test User",
                "account_type": "b2c",
            }

            supabase_client.table("user_profiles").insert(profile_data).execute()

        except Exception as e:
            pytest.skip(f"Failed to setup test user: {str(e)}")

    yield token

    # Cleanup: Delete user profile
    # Note: Deleting from auth.users requires admin API
    # For now, we'll just delete the profile
    try:
        supabase_client.table("user_profiles").delete().eq("id", user_id).execute()
    except Exception:
        pass  # Cleanup failed, not critical for tests


@pytest.fixture
def invalid_token():
    """Return an invalid JWT token for testing unauthorized access"""
    return "invalid_token_12345_this_is_not_valid"


@pytest.fixture
def expired_token():
    """
    Return an expired JWT token for testing
    Note: Generate a real expired token from Supabase if needed
    """
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.expired"
