import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Mock tokens for testing
MOCK_TOKEN = "mock_jwt_token"
MOCK_USER_ID = "test-user-123"


@pytest.fixture
def mock_auth_headers():
    """Mock authentication headers"""
    return {"Authorization": f"Bearer {MOCK_TOKEN}"}


# =====================================================
# Challenge History Tests
# =====================================================


def test_list_history_without_auth():
    """Test listing history without authentication"""
    response = client.get("/api/v1/stats/history")

    assert response.status_code in [401, 403]  # Unauthorized


def test_list_history_success(mock_auth_headers):
    """
    Test successful history listing
    
    Expected: 200 OK with paginated response
    
    Note: Placeholder test. Requires mocking Supabase query.
    """
    # This would require proper mocking of Supabase client
    pass


def test_list_history_with_status_filter(mock_auth_headers):
    """
    Test filtering history by status
    
    Expected: Returns only challenges matching status filter
    """
    # Mock implementation would filter by status=completed
    pass


def test_list_history_with_search(mock_auth_headers):
    """
    Test searching history by name
    
    Expected: Returns only challenges matching search term
    """
    # Mock implementation would search by name
    pass


def test_list_history_pagination(mock_auth_headers):
    """
    Test pagination parameters
    
    Expected: Returns correct page of results
    """
    # Mock implementation would test page/limit params
    pass


# =====================================================
# Challenge Stats Tests
# =====================================================


def test_get_challenge_stats_without_auth():
    """Test getting stats without authentication"""
    response = client.get("/api/v1/stats/stats/challenge-123")

    assert response.status_code in [401, 403]


def test_get_challenge_stats_not_member(mock_auth_headers):
    """
    Test getting stats when not a member
    
    Expected: 403 Forbidden
    """
    # Mock implementation would return no membership
    pass


def test_get_challenge_stats_success(mock_auth_headers):
    """
    Test successful stats retrieval
    
    Expected: 200 OK with comprehensive stats
    """
    # Mock implementation would return stats from RPC
    pass


# =====================================================
# Leaderboard Tests
# =====================================================


def test_get_leaderboard_without_auth():
    """Test getting leaderboard without authentication"""
    response = client.get("/api/v1/stats/leaderboard/challenge-123")

    assert response.status_code in [401, 403]


def test_get_leaderboard_not_member(mock_auth_headers):
    """
    Test getting leaderboard when not a member
    
    Expected: 403 Forbidden
    """
    # Mock implementation would return no membership
    pass


def test_get_leaderboard_success(mock_auth_headers):
    """
    Test successful leaderboard retrieval
    
    Expected: 200 OK with sorted leaderboard
    """
    # Mock implementation would return leaderboard
    pass


def test_get_leaderboard_sort_by_points(mock_auth_headers):
    """
    Test leaderboard sorted by points
    
    Expected: Leaderboard sorted by points_earned DESC
    """
    pass


def test_get_leaderboard_sort_by_streak(mock_auth_headers):
    """
    Test leaderboard sorted by streak
    
    Expected: Leaderboard sorted by current_streak DESC
    """
    pass


def test_get_leaderboard_sort_by_completion_rate(mock_auth_headers):
    """
    Test leaderboard sorted by completion rate
    
    Expected: Leaderboard sorted by completion_rate DESC
    """
    pass


# =====================================================
# User Dashboard Tests
# =====================================================


def test_get_dashboard_without_auth():
    """Test getting dashboard without authentication"""
    response = client.get("/api/v1/stats/dashboard")

    assert response.status_code in [401, 403]


def test_get_dashboard_success(mock_auth_headers):
    """
    Test successful dashboard retrieval
    
    Expected: 200 OK with user stats, active challenges, recent completions
    """
    # Mock implementation would return dashboard data from RPC
    pass


# =====================================================
# Validation Tests
# =====================================================


def test_history_invalid_status_filter():
    """Test history with invalid status filter"""
    response = client.get(
        "/api/v1/stats/history?status=invalid",
        headers={"Authorization": f"Bearer {MOCK_TOKEN}"},
    )

    # Pydantic validation should fail
    assert response.status_code == 422


def test_leaderboard_invalid_sort_by():
    """Test leaderboard with invalid sort_by parameter"""
    response = client.get(
        "/api/v1/stats/leaderboard/challenge-123?sort_by=invalid",
        headers={"Authorization": f"Bearer {MOCK_TOKEN}"},
    )

    # Pydantic validation should fail
    assert response.status_code == 422


def test_history_invalid_page():
    """Test history with invalid page number"""
    response = client.get(
        "/api/v1/stats/history?page=0",
        headers={"Authorization": f"Bearer {MOCK_TOKEN}"},
    )

    # Validation: page must be >= 1
    assert response.status_code == 422


def test_history_invalid_limit():
    """Test history with invalid limit"""
    response = client.get(
        "/api/v1/stats/history?limit=0",
        headers={"Authorization": f"Bearer {MOCK_TOKEN}"},
    )

    # Validation: limit must be >= 1
    assert response.status_code == 422


def test_history_limit_too_large():
    """Test history with limit > 100"""
    response = client.get(
        "/api/v1/stats/history?limit=101",
        headers={"Authorization": f"Bearer {MOCK_TOKEN}"},
    )

    # Validation: limit must be <= 100
    assert response.status_code == 422


# =====================================================
# Integration Test Placeholders
# =====================================================


def test_materialized_view_exists():
    """
    Integration test: Verify materialized view created
    
    Steps:
    1. Query pg_matviews
    2. Verify challenge_member_stats exists
    
    Requires: Database connection
    """
    pass


def test_refresh_stats_function():
    """
    Integration test: Verify refresh function works
    
    Steps:
    1. Call refresh_challenge_stats()
    2. Verify materialized view refreshed
    
    Requires: Database connection
    """
    pass


def test_get_challenge_stats_rpc():
    """
    Integration test: Verify RPC function returns correct data
    
    Steps:
    1. Call get_challenge_stats RPC
    2. Verify returned stats structure
    
    Requires: Database connection with test data
    """
    pass


def test_get_user_dashboard_rpc():
    """
    Integration test: Verify dashboard RPC function
    
    Steps:
    1. Call get_user_dashboard RPC
    2. Verify returned dashboard structure
    
    Requires: Database connection with test data
    """
    pass


# =====================================================
# Manual Testing Guide (in comments)
# =====================================================

"""
MANUAL TESTING COMMANDS:

Pre-requisites:
1. Run migration 009_stats_views.sql in Supabase
2. Have challenge data with members and check-ins
3. Materialized view populated

1. Get challenge history:
   curl -X GET "http://localhost:8000/api/v1/stats/history?page=1&limit=10" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

   Expected: 200 OK with paginated list of challenges

2. Filter history by status:
   curl -X GET "http://localhost:8000/api/v1/stats/history?status=completed" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

   Expected: Only completed challenges

3. Search history:
   curl -X GET "http://localhost:8000/api/v1/stats/history?search=Fitness" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

   Expected: Challenges matching "Fitness"

4. Get challenge stats:
   curl -X GET "http://localhost:8000/api/v1/stats/stats/CHALLENGE_ID" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

   Expected: Comprehensive stats with top performers, habit stats

5. Get leaderboard:
   curl -X GET "http://localhost:8000/api/v1/stats/leaderboard/CHALLENGE_ID?sort_by=points" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

   Expected: Ranked list sorted by points

6. Get user dashboard:
   curl -X GET "http://localhost:8000/api/v1/stats/dashboard" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

   Expected: User stats, active challenges, recent completions

7. Refresh materialized view (in Supabase SQL Editor):
   SELECT refresh_challenge_stats();

   Expected: Materialized view refreshed with latest data

8. Verify materialized view data:
   SELECT * FROM challenge_member_stats LIMIT 10;

   Expected: Rows with calculated stats (completion_rate, ranks)

GETTING JWT TOKEN:
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
"""


# =====================================================
# Notes for Future Implementation
# =====================================================

"""
To implement real tests with database:

1. Use pytest fixtures for test data:
   - Create test users
   - Create test challenges with members
   - Create check-ins
   - Refresh materialized view

2. Mock Supabase RPC calls:
   - Mock get_challenge_stats response
   - Mock get_user_dashboard response
   - Test different scenarios

3. Integration tests with test database:
   - Use Supabase test project
   - Create/cleanup test data
   - Test actual RPC functions
   - Test materialized view queries

4. Test performance:
   - Compare query times with/without materialized view
   - Verify indexes used
   - Test concurrent refresh

Example fixture:

@pytest.fixture
async def test_challenge_with_stats(supabase):
    # Create test challenge with members
    challenge = await create_test_challenge()
    
    # Add members
    member1 = await add_member(challenge.id)
    member2 = await add_member(challenge.id)
    
    # Add check-ins
    await create_checkins(member1, count=10)
    await create_checkins(member2, count=8)
    
    # Refresh materialized view
    await supabase.rpc('refresh_challenge_stats').execute()
    
    yield challenge, member1, member2
    
    # Cleanup
    await cleanup_test_data()
"""
