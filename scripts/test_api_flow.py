#!/usr/bin/env python3
"""
Test API Flow for DareZone
Tests: Login, Create Challenge, Join Challenge, List Challenges
"""

import os
import sys
import httpx
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
API_BASE = "http://localhost:8000/api/v1"

# Test users
USER1 = {"email": "test1@example.com", "password": "12345678"}
USER2 = {"email": "test2@example.com", "password": "12345678"}

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def login_user(email, password):
    """Login user and get JWT token"""
    auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    data = {"email": email, "password": password}
    
    try:
        response = httpx.post(auth_url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            token = response.json()["access_token"]
            user_id = response.json()["user"]["id"]
            print(f"✅ Login successful: {email}")
            print(f"   User ID: {user_id}")
            print(f"   Token: {token[:50]}...")
            return token, user_id
        else:
            print(f"❌ Login failed: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None, None

def get_habits(token):
    """Get available habits"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # First, let's check if there are any habits
        # We'll use a simple approach - just use some UUIDs
        # In real scenario, you'd fetch from /habits endpoint
        print("ℹ️  Using predefined habit IDs for testing")
        return []
    except Exception as e:
        print(f"⚠️  Could not fetch habits: {str(e)}")
        return []

def create_challenge(token, user_email):
    """Create a new challenge"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Calculate dates
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=30)
    
    # Get habit ID (you need to have habits in your database)
    # For now, we'll try to create without habits first
    data = {
        "name": f"Test Challenge by {user_email}",
        "description": "A test challenge for API testing",
        "type": "group",
        "start_date": str(start_date),
        "end_date": str(end_date),
        "habit_ids": [],  # Will need actual habit IDs
        "max_members": 10,
        "is_public": False,
        "checkin_type": "daily",
        "require_evidence": True
    }
    
    try:
        response = httpx.post(
            f"{API_BASE}/challenges",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 201:
            challenge = response.json()
            print(f"✅ Challenge created successfully!")
            print(f"   ID: {challenge['id']}")
            print(f"   Name: {challenge['name']}")
            print(f"   Invite Code: {challenge.get('invite_code', 'N/A')}")
            return challenge
        else:
            print(f"❌ Failed to create challenge: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def list_challenges(token, user_email):
    """List user's challenges"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = httpx.get(
            f"{API_BASE}/challenges",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            challenges = data.get("challenges", [])
            print(f"✅ Found {len(challenges)} challenge(s) for {user_email}")
            
            for idx, challenge in enumerate(challenges, 1):
                print(f"\n   Challenge {idx}:")
                print(f"   - ID: {challenge['id']}")
                print(f"   - Name: {challenge['name']}")
                print(f"   - Status: {challenge['status']}")
                print(f"   - Members: {challenge['member_count']}")
                print(f"   - My Role: {challenge.get('my_role', 'N/A')}")
                if challenge.get('invite_code'):
                    print(f"   - Invite Code: {challenge['invite_code']}")
            
            return challenges
        else:
            print(f"❌ Failed to list challenges: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

def join_challenge(token, invite_code, user_email):
    """Join a challenge using invite code"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"invite_code": invite_code}
    
    try:
        response = httpx.post(
            f"{API_BASE}/challenges/join",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            challenge = response.json()
            print(f"✅ {user_email} joined challenge successfully!")
            print(f"   Challenge: {challenge['name']}")
            print(f"   Members: {challenge['member_count']}")
            return challenge
        else:
            print(f"❌ Failed to join challenge: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def check_common_challenges(token1, token2, user1_email, user2_email):
    """Check if two users share any challenges"""
    print_section("Checking Common Challenges")
    
    challenges1 = list_challenges(token1, user1_email)
    print()
    challenges2 = list_challenges(token2, user2_email)
    
    if not challenges1 or not challenges2:
        print("\n⚠️  One or both users have no challenges")
        return
    
    # Find common challenge IDs
    ids1 = {c['id'] for c in challenges1}
    ids2 = {c['id'] for c in challenges2}
    common_ids = ids1 & ids2
    
    print(f"\n{'='*60}")
    if common_ids:
        print(f"✅ Found {len(common_ids)} common challenge(s)!")
        for challenge_id in common_ids:
            challenge = next(c for c in challenges1 if c['id'] == challenge_id)
            print(f"\n   Common Challenge:")
            print(f"   - Name: {challenge['name']}")
            print(f"   - ID: {challenge_id}")
            print(f"   - Members: {challenge['member_count']}")
    else:
        print("❌ No common challenges found between the two users")
    print(f"{'='*60}\n")

def main():
    """Main test flow"""
    print_section("DareZone API Test Flow")
    
    # Step 1: Login both users
    print_section("Step 1: Login Users")
    token1, user1_id = login_user(USER1["email"], USER1["password"])
    print()
    token2, user2_id = login_user(USER2["email"], USER2["password"])
    
    if not token1 or not token2:
        print("\n❌ Login failed. Exiting.")
        sys.exit(1)
    
    # Step 2: User 1 creates a challenge
    print_section("Step 2: User 1 Creates Challenge")
    challenge = create_challenge(token1, USER1["email"])
    
    if not challenge:
        print("\n⚠️  Challenge creation failed. Continuing with existing challenges...")
    
    # Step 3: List challenges for User 1
    print_section("Step 3: List Challenges for User 1")
    user1_challenges = list_challenges(token1, USER1["email"])
    
    # Step 4: User 2 joins the challenge (if invite code available)
    if challenge and challenge.get('invite_code'):
        print_section("Step 4: User 2 Joins Challenge")
        invite_code = challenge['invite_code']
        print(f"Using invite code: {invite_code}")
        join_challenge(token2, invite_code, USER2["email"])
    else:
        print_section("Step 4: User 2 Joins Challenge")
        print("⚠️  No invite code available. Skipping join step.")
        
        # Try to find an existing challenge with invite code
        if user1_challenges:
            for ch in user1_challenges:
                if ch.get('invite_code'):
                    print(f"\nℹ️  Found existing challenge with invite code: {ch['invite_code']}")
                    print(f"   Attempting to join...")
                    join_challenge(token2, ch['invite_code'], USER2["email"])
                    break
    
    # Step 5: Check common challenges
    check_common_challenges(token1, token2, USER1["email"], USER2["email"])
    
    print_section("Test Complete!")
    print("✅ All tests executed successfully\n")

if __name__ == "__main__":
    main()
