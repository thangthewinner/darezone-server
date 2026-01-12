"""
Test fixtures using real test users instead of anonymous users
"""

import pytest
from fastapi.testclient import TestClient
from supabase import Client
from app.main import app

client = TestClient(app)

# Test user credentials
TEST_USER_1 = {
    "email": "test1@example.com",
    "password": "12345678",
    "id": "8ef3a396-d9fe-4f80-a8d3-437e75dd3248"
}

TEST_USER_2 = {
    "email": "test2@example.com",
    "password": "12345678",
    "id": "627f319d-ee76-4acb-8f80-be1df138130a"
}


@pytest.fixture
def test_user_1_token(supabase_client: Client):
    """Get access token for test user 1"""
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": TEST_USER_1["email"],
            "password": TEST_USER_1["password"]
        })
        
        if response.session:
            return response.session.access_token
        else:
            pytest.skip("Failed to login test user 1")
            
    except Exception as e:
        pytest.skip(f"Test user 1 not found: {str(e)}")


@pytest.fixture
def test_user_2_token(supabase_client: Client):
    """Get access token for test user 2"""
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": TEST_USER_2["email"],
            "password": TEST_USER_2["password"]
        })
        
        if response.session:
            return response.session.access_token
        else:
            pytest.skip("Failed to login test user 2")
            
    except Exception as e:
        pytest.skip(f"Test user 2 not found: {str(e)}")


@pytest.fixture
def test_user_1_id():
    """Get test user 1 ID"""
    return TEST_USER_1["id"]


@pytest.fixture
def test_user_2_id():
    """Get test user 2 ID"""
    return TEST_USER_2["id"]


def get_auth_headers(token: str) -> dict:
    """Helper to create auth headers"""
    return {"Authorization": f"Bearer {token}"}
