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


@pytest.fixture
def valid_hitch_request():
    """Valid hitch request payload"""
    return {
        "challenge_id": "123e4567-e89b-12d3-a456-426614174000",
        "habit_id": "123e4567-e89b-12d3-a456-426614174001",
        "target_user_ids": [
            "123e4567-e89b-12d3-a456-426614174002",
            "123e4567-e89b-12d3-a456-426614174003",
        ],
    }


# =====================================================
# Send Hitch Tests
# =====================================================


def test_send_hitch_success(mock_auth_headers, valid_hitch_request):
    """
    Test successful hitch sending
    
    Expected: 200 OK with hitches_sent and remaining_hitches
    
    Note: This is a placeholder test. In real implementation,
    you would mock the Supabase RPC call to return expected data.
    """
    # This would require proper mocking of Supabase client
    pass


def test_send_hitch_without_auth(valid_hitch_request):
    """Test sending hitch fails without authentication"""
    response = client.post("/api/v1/hitch", json=valid_hitch_request)

    assert response.status_code in [401, 403]  # Unauthorized or Forbidden


def test_send_hitch_no_hitches_remaining(mock_auth_headers, valid_hitch_request):
    """
    Test sending hitch when user has 0 hitches left
    
    Expected: 400 Bad Request with "No hitches remaining" error
    
    Note: Requires mocking RPC to raise "No hitches remaining" exception
    """
    # Mock implementation would set hitch_count = 0
    pass


def test_send_hitch_rate_limit(mock_auth_headers, valid_hitch_request):
    """
    Test rate limiting - same hitch sent twice in one day
    
    Expected: 400 Bad Request with "already received" error
    
    Note: Requires mocking RPC to raise "already received" exception
    """
    # Mock implementation would have existing hitch_log entry for today
    pass


def test_send_hitch_not_member(mock_auth_headers, valid_hitch_request):
    """
    Test sending hitch when sender is not a challenge member
    
    Expected: 403 Forbidden with "Not a member" error
    """
    # Mock implementation would return no membership record
    pass


def test_send_hitch_invalid_targets(mock_auth_headers):
    """Test sending hitch to invalid targets (not members)"""
    invalid_request = {
        "challenge_id": "123e4567-e89b-12d3-a456-426614174000",
        "habit_id": "123e4567-e89b-12d3-a456-426614174001",
        "target_user_ids": [
            "00000000-0000-0000-0000-000000000000",  # Not a member
        ],
    }

    # Mock implementation would skip invalid targets
    pass


def test_send_hitch_empty_targets():
    """Test validation for empty target list"""
    # Empty target_user_ids should fail Pydantic validation (min_length=1)
    # This is tested at schema level, no need for actual HTTP call
    from app.schemas.hitch import HitchRequest
    from pydantic import ValidationError
    
    try:
        HitchRequest(
            challenge_id="123e4567-e89b-12d3-a456-426614174000",
            habit_id="123e4567-e89b-12d3-a456-426614174001",
            target_user_ids=[],  # Empty list
        )
        assert False, "Should have raised validation error"
    except ValidationError:
        pass  # Expected


def test_send_hitch_too_many_targets():
    """Test validation for too many targets (>10)"""
    # More than 10 targets should fail Pydantic validation (max_length=10)
    # This is tested at schema level, no need for actual HTTP call
    from app.schemas.hitch import HitchRequest
    from pydantic import ValidationError
    
    try:
        HitchRequest(
            challenge_id="123e4567-e89b-12d3-a456-426614174000",
            habit_id="123e4567-e89b-12d3-a456-426614174001",
            target_user_ids=[f"user-{i}" for i in range(11)],  # 11 users
        )
        assert False, "Should have raised validation error"
    except ValidationError:
        pass  # Expected


def test_send_hitch_missing_fields():
    """Test validation for missing required fields"""
    # Missing required fields should fail Pydantic validation
    # This is tested at schema level, no need for actual HTTP call
    from app.schemas.hitch import HitchRequest
    from pydantic import ValidationError
    
    try:
        HitchRequest(
            challenge_id="123e4567-e89b-12d3-a456-426614174000",
            # Missing habit_id and target_user_ids
        )
        assert False, "Should have raised validation error"
    except ValidationError:
        pass  # Expected


# =====================================================
# Integration Test Placeholders
# =====================================================


def test_hitch_count_decrements():
    """
    Integration test: Verify hitch_count decrements after sending
    
    Steps:
    1. Get initial hitch_count from challenge_members
    2. Send hitch
    3. Verify hitch_count decreased by 1
    
    Requires: Real database connection
    """
    pass


def test_notification_created():
    """
    Integration test: Verify notification created for target
    
    Steps:
    1. Send hitch to target user
    2. Query notifications table
    3. Verify notification exists with type='hitch_reminder'
    
    Requires: Real database connection
    """
    pass


def test_hitch_log_created():
    """
    Integration test: Verify hitch_log entry created
    
    Steps:
    1. Send hitch
    2. Query hitch_log table
    3. Verify entry exists for sender/target/habit/date
    
    Requires: Real database connection
    """
    pass


def test_duplicate_hitch_same_day():
    """
    Integration test: Verify duplicate hitch blocked
    
    Steps:
    1. Send hitch to user A
    2. Try to send same hitch again
    3. Verify second hitch is skipped (rate limit)
    
    Requires: Real database connection
    """
    pass


# =====================================================
# Manual Testing Guide (in comments)
# =====================================================

"""
MANUAL TESTING COMMANDS:

Pre-requisites:
1. Run migration 008_hitch_system.sql in Supabase
2. Have 2+ users in same challenge
3. Have challenge_members with hitch_count > 0

1. Send hitch reminder:
   curl -X POST "http://localhost:8000/api/v1/hitch" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "challenge_id": "YOUR_CHALLENGE_ID",
       "habit_id": "YOUR_HABIT_ID",
       "target_user_ids": ["TARGET_USER_ID"]
     }'

   Expected: 200 OK
   {
     "success": true,
     "hitches_sent": 1,
     "remaining_hitches": 1,
     "message": "Sent 1 reminder. 1 hitch remaining."
   }

2. Verify hitch_count decremented:
   SELECT hitch_count 
   FROM challenge_members 
   WHERE challenge_id = 'YOUR_CHALLENGE_ID' 
     AND user_id = 'YOUR_USER_ID';
   
   Should be decreased by 1

3. Verify notification created:
   SELECT * FROM notifications 
   WHERE user_id = 'TARGET_USER_ID' 
     AND type = 'hitch_reminder' 
   ORDER BY created_at DESC 
   LIMIT 1;
   
   Should see notification with hitch details

4. Test rate limiting (send again):
   curl -X POST "http://localhost:8000/api/v1/hitch" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "challenge_id": "YOUR_CHALLENGE_ID",
       "habit_id": "YOUR_HABIT_ID",
       "target_user_ids": ["TARGET_USER_ID"]
     }'

   Expected: 400 Bad Request
   "All targets have already received a hitch reminder today"

5. Test no hitches remaining:
   -- First, set hitch_count to 0
   UPDATE challenge_members 
   SET hitch_count = 0 
   WHERE user_id = 'YOUR_USER_ID';
   
   -- Then try to send
   curl -X POST "http://localhost:8000/api/v1/hitch" \
     ...
   
   Expected: 400 Bad Request
   "You have used all your hitches for this challenge"

6. Test not a member:
   Use JWT token of user NOT in the challenge
   
   Expected: 403 Forbidden
   "You must be an active member..."

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
   - Create test challenge
   - Add members to challenge
   - Set hitch_count > 0

2. Mock Supabase RPC calls:
   - Mock send_hitch_reminder response
   - Test different error scenarios

3. Integration tests with test database:
   - Use Supabase test project
   - Create/cleanup test data
   - Test actual RPC function behavior

4. Test notifications:
   - Verify notification created
   - Check notification content
   - Test push notification sending (optional)

Example fixture:

@pytest.fixture
async def test_challenge_with_members(supabase):
    # Create test challenge
    challenge = await create_test_challenge()
    
    # Add members
    member1 = await add_member(challenge.id, hitch_count=2)
    member2 = await add_member(challenge.id, hitch_count=2)
    
    yield challenge, member1, member2
    
    # Cleanup
    await cleanup_test_data()
"""
